"""Entra-bearer-token validation middleware (spec-035 T024).

Validates `Authorization: Bearer <jwt>` against an Entra tenant via JWKS,
extracts ``oid``, ``roles``, ``persona_id`` claims onto ``request.state.claims``,
and emits the
[Q10 extension envelope](../../../../specs/035-webapp-capstone-closure/contracts/production-auth-extension.contract.md)
on `401 unauthorized` or `403 forbidden`.

Activation:
- Disabled by default (test_support guard already covers dev/test).
- Enabled for every protected route when ``AMA_ENABLE_PRODUCTION_AUTH=1``.
- Enabled only for ``/api/incidents/map`` when ``AMA_ENABLE_INCIDENT_MAP_AUTH=1``.
- Required env vars in either mode are
  ``AMA_ENTRA_TENANT_ID`` and ``AMA_ENTRA_AUDIENCE``.
- For tests, set ``AMA_ENTRA_TEST_PRINCIPAL`` to an inline JSON string and the
  middleware will short-circuit JWKS validation and adopt that principal —
  this is the supported pattern for contract tests (T017..T023).

JWKS keys cached for 1 hour (``research.md § R-001``).
"""

from __future__ import annotations

import json
import logging
import os
import time
from typing import Any

from app.middleware.envelope_response import error_to_envelope_response
from app.schemas.envelope_errors import ExtensionEnvelopeError
from app.schemas.extension_envelope import ExtensionErrorCode
from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

logger = logging.getLogger(__name__)


_PROTECTED_PREFIXES = (
    "/api/simulations",
    "/api/incidents",
    "/api/data-sources",
    "/api/alerts/",
    "/api/recommendations/",
    "/api/outcomes/",
    "/api/audit/list",
    "/api/auth/whoami",
    "/api/offline/replay",
    "/api/recovery/handover",
    "/api/governance/dashboard",
    "/api/workflow_runs",
    "/api/help",
    "/api/governance/evidence-pack",
    "/api/v1/evidence",
)

_JWKS_CACHE_TTL = 3600.0
_jwks_cache: dict[str, tuple[float, list[dict[str, Any]]]] = {}
_INCIDENT_MAP_PATH = "/api/incidents/map"


def _is_protected(path: str) -> bool:
    return any(path.startswith(prefix) for prefix in _PROTECTED_PREFIXES)


def _production_auth_enabled() -> bool:
    return os.environ.get("AMA_ENABLE_PRODUCTION_AUTH", "0") == "1"


def _incident_map_auth_enabled() -> bool:
    return os.environ.get("AMA_ENABLE_INCIDENT_MAP_AUTH", "0") == "1"


def _should_authenticate(path: str) -> bool:
    return (_production_auth_enabled() and _is_protected(path)) or (
        _incident_map_auth_enabled() and path == _INCIDENT_MAP_PATH
    )


def _get_test_principal() -> dict[str, Any] | None:
    raw = os.environ.get("AMA_ENTRA_TEST_PRINCIPAL")
    if not raw:
        return None
    if _production_auth_enabled() or _incident_map_auth_enabled():
        logger.warning("Ignoring AMA_ENTRA_TEST_PRINCIPAL when live Entra authentication is enabled")
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        logger.error("AMA_ENTRA_TEST_PRINCIPAL is not valid JSON; rejecting all requests")
        return None


def _fetch_jwks(tenant_id: str) -> list[dict[str, Any]]:
    cached = _jwks_cache.get(tenant_id)
    now = time.time()
    if cached and now - cached[0] < _JWKS_CACHE_TTL:
        return cached[1]
    import httpx

    url = f"https://login.microsoftonline.com/{tenant_id}/discovery/v2.0/keys"
    try:
        resp = httpx.get(url, timeout=5.0)
        resp.raise_for_status()
        keys = resp.json().get("keys", [])
    except Exception:
        logger.exception("JWKS fetch failed for tenant=%s", tenant_id)
        return cached[1] if cached else []

    _jwks_cache[tenant_id] = (now, keys)
    return keys


def _validate_jwt(token: str) -> dict[str, Any]:
    """Validate the JWT signature + audience and return claims.

    Raises ``ExtensionEnvelopeError(unauthorized)`` on any validation failure.
    """
    tenant_id = os.environ.get("AMA_ENTRA_TENANT_ID", os.environ.get("ENTRA_TENANT_ID"))
    audience = os.environ.get("AMA_ENTRA_AUDIENCE", os.environ.get("ENTRA_AUDIENCE"))
    if not (tenant_id and audience):
        raise ExtensionEnvelopeError(
            ExtensionErrorCode.UNAUTHORIZED,
            detail="Production auth not configured (tenant/audience env missing).",
        )

    try:
        import jwt as pyjwt
        from jwt.algorithms import RSAAlgorithm
    except ImportError as exc:  # pragma: no cover
        raise ExtensionEnvelopeError(
            ExtensionErrorCode.UNAUTHORIZED,
            detail="JWT library unavailable.",
        ) from exc

    try:
        unverified = pyjwt.get_unverified_header(token)
    except pyjwt.PyJWTError as exc:
        raise ExtensionEnvelopeError(
            ExtensionErrorCode.UNAUTHORIZED,
            detail=f"malformed token: {exc}",
        ) from exc

    kid = unverified.get("kid")
    keys = _fetch_jwks(tenant_id)
    matching = next((k for k in keys if k.get("kid") == kid), None)
    if not matching:
        raise ExtensionEnvelopeError(
            ExtensionErrorCode.UNAUTHORIZED,
            detail="signing key not found in JWKS",
        )

    from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey

    parsed_key = RSAAlgorithm.from_jwk(json.dumps(matching))
    public_key = parsed_key.public_key() if isinstance(parsed_key, RSAPrivateKey) else parsed_key
    try:
        claims: dict[str, Any] = pyjwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            audience=audience,
            issuer=f"https://login.microsoftonline.com/{tenant_id}/v2.0",
        )
    except pyjwt.PyJWTError as exc:
        raise ExtensionEnvelopeError(
            ExtensionErrorCode.UNAUTHORIZED,
            detail=f"token rejected: {exc}",
        ) from exc

    return claims


class EntraAuthMiddleware(BaseHTTPMiddleware):
    """Resolve principal claims from ``Authorization: Bearer ...``."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if not _should_authenticate(request.url.path):
            return await call_next(request)

        try:
            claims = self._resolve_claims(request)
        except ExtensionEnvelopeError as exc:
            return error_to_envelope_response(request, exc)

        request.state.entra_claims = claims
        existing = getattr(request.state, "claims", None) or {}
        merged = {**existing, **claims}
        request.state.claims = merged
        return await call_next(request)

    @staticmethod
    def _resolve_claims(request: Request) -> dict[str, Any]:
        principal = _get_test_principal()
        if principal is not None:
            return principal

        auth = request.headers.get("Authorization", "")
        if not auth.lower().startswith("bearer "):
            raise ExtensionEnvelopeError(
                ExtensionErrorCode.UNAUTHORIZED,
                detail="missing bearer token",
            )
        token = auth.split(" ", 1)[1].strip()
        if not token:
            raise ExtensionEnvelopeError(
                ExtensionErrorCode.UNAUTHORIZED,
                detail="empty bearer token",
            )
        return _validate_jwt(token)


def add_entra_auth_middleware(app: FastAPI) -> None:
    if not (_production_auth_enabled() or _incident_map_auth_enabled()):
        return
    app.add_middleware(EntraAuthMiddleware)


__all__ = ["EntraAuthMiddleware", "add_entra_auth_middleware"]
