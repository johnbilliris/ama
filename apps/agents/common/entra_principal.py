"""Fail-closed Entra principal resolution for standalone agent services."""

from __future__ import annotations

import asyncio
import json
import os
import time
from dataclasses import dataclass
from typing import Any

import httpx
from fastapi import HTTPException, Request

COMMANDER_ROLES = frozenset(
    {
        "commander",
        "emergencycommander",
        "ic",
        "incidentcommander",
        "publicinformationofficer",
    }
)
HANDOFF_PRODUCER_ROLES = frozenset({"riskassessmentagent", "systemadministrator"})


def normalize_role(role: str) -> str:
    return "".join(character for character in role.casefold() if character.isalnum())


@dataclass(frozen=True)
class AuthenticatedPrincipal:
    subject: str
    tenant_id: str
    roles: tuple[str, ...]
    incident_ids: tuple[str, ...] = ()

    @property
    def commander_role(self) -> str | None:
        return next((role for role in self.roles if normalize_role(role) in COMMANDER_ROLES), None)

    def has_asserted_role(self, role: str) -> bool:
        asserted = normalize_role(role)
        return any(normalize_role(candidate) == asserted for candidate in self.roles)


class EntraPrincipalResolver:
    """Validate bearer tokens against the configured Entra tenant and audience."""

    _cache: dict[str, tuple[float, list[dict[str, Any]]]] = {}

    def __init__(
        self,
        *,
        tenant_id: str | None = None,
        audience: str | None = None,
        jwks_cache_seconds: float = 3600.0,
    ) -> None:
        self._tenant_id = tenant_id or os.environ.get("AMA_ENTRA_TENANT_ID") or os.environ.get("ENTRA_TENANT_ID")
        self._audience = audience or os.environ.get("AMA_ENTRA_AUDIENCE") or os.environ.get("ENTRA_AUDIENCE")
        self._jwks_cache_seconds = jwks_cache_seconds
        self._cache_lock = asyncio.Lock()

    async def __call__(self, request: Request) -> AuthenticatedPrincipal:
        authorization = request.headers.get("Authorization", "")
        if not authorization.lower().startswith("bearer "):
            raise HTTPException(status_code=401, detail="Bearer authentication is required")
        token = authorization.split(" ", 1)[1].strip()
        if not token:
            raise HTTPException(status_code=401, detail="Bearer authentication is required")
        if not self._tenant_id or not self._audience:
            raise HTTPException(status_code=503, detail="Authentication is not configured")

        claims = await self._validate_token(token)
        subject = str(claims.get("oid") or "").strip()
        roles_claim = claims.get("roles")
        roles = tuple(str(role).strip() for role in roles_claim) if isinstance(roles_claim, list) else ()
        operational_tenant = str(claims.get("operational_tenant_id") or claims.get("tenant_id") or "").strip()
        incident_claim = claims.get("incident_ids")
        incident_ids = (
            tuple(str(incident_id).strip() for incident_id in incident_claim if str(incident_id).strip())
            if isinstance(incident_claim, list)
            else ()
        )
        if not subject or not operational_tenant:
            raise HTTPException(status_code=401, detail="Token is missing required identity claims")
        return AuthenticatedPrincipal(
            subject=subject,
            tenant_id=operational_tenant,
            roles=roles,
            incident_ids=incident_ids,
        )

    async def _validate_token(self, token: str) -> dict[str, Any]:
        try:
            import jwt
            from jwt.algorithms import RSAAlgorithm
        except ImportError as exc:  # pragma: no cover - packaging failure
            raise HTTPException(status_code=503, detail="Authentication dependency is unavailable") from exc

        try:
            header = jwt.get_unverified_header(token)
        except jwt.PyJWTError as exc:
            raise HTTPException(status_code=401, detail="Bearer token is malformed") from exc
        if header.get("alg") != "RS256" or not header.get("kid"):
            raise HTTPException(status_code=401, detail="Bearer token uses an unsupported signing key")

        keys = await self._get_jwks()
        matching_key = next((key for key in keys if key.get("kid") == header["kid"]), None)
        if matching_key is None:
            raise HTTPException(status_code=401, detail="Bearer token signing key is unknown")

        public_key = RSAAlgorithm.from_jwk(json.dumps(matching_key))
        try:
            return jwt.decode(
                token,
                public_key,
                algorithms=["RS256"],
                audience=self._audience,
                issuer=f"https://login.microsoftonline.com/{self._tenant_id}/v2.0",
                options={"require": ["exp", "iat", "iss", "aud"]},
            )
        except jwt.PyJWTError as exc:
            raise HTTPException(status_code=401, detail="Bearer token is invalid or expired") from exc

    async def _get_jwks(self) -> list[dict[str, Any]]:
        assert self._tenant_id is not None
        cached = self._cache.get(self._tenant_id)
        now = time.monotonic()
        if cached is not None and now - cached[0] < self._jwks_cache_seconds:
            return cached[1]

        async with self._cache_lock:
            cached = self._cache.get(self._tenant_id)
            if cached is not None and now - cached[0] < self._jwks_cache_seconds:
                return cached[1]
            url = f"https://login.microsoftonline.com/{self._tenant_id}/discovery/v2.0/keys"
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    response = await client.get(url)
                    response.raise_for_status()
                    keys = response.json().get("keys", [])
            except (httpx.HTTPError, ValueError) as exc:
                raise HTTPException(status_code=503, detail="Identity provider keys are unavailable") from exc
            if not isinstance(keys, list) or not keys:
                raise HTTPException(status_code=503, detail="Identity provider returned no signing keys")
            self._cache[self._tenant_id] = (time.monotonic(), keys)
            return keys


def require_commander(principal: AuthenticatedPrincipal) -> AuthenticatedPrincipal:
    if principal.commander_role is None:
        raise HTTPException(status_code=403, detail="Commander role is required")
    return principal


def require_handoff_producer(principal: AuthenticatedPrincipal) -> AuthenticatedPrincipal:
    if not any(normalize_role(role) in HANDOFF_PRODUCER_ROLES for role in principal.roles):
        raise HTTPException(status_code=403, detail="Risk Assessment Agent role is required")
    return principal


__all__ = [
    "AuthenticatedPrincipal",
    "EntraPrincipalResolver",
    "require_commander",
    "require_handoff_producer",
]
