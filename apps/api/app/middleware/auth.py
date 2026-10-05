"""Management API authorization middleware (FR-021).

Non-dev: signed Entra JWT with issuer/audience validation and operator/admin role.
Dev: full access only when AMA_ALLOW_ANONYMOUS_DEV_ACCESS is enabled.
Local fallback: X-API-Key header matching MANAGEMENT_API_KEY env var.
"""

from __future__ import annotations

import logging
import os
from typing import TypedDict

from app.core.dev_access import dev_access_enabled
from app.schemas.envelope_errors import ExtensionEnvelopeError
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

logger = logging.getLogger(__name__)


class JWTClaims(TypedDict, total=False):
    sub: str
    oid: str
    roles: list[str]


class AuthenticatedIdentity(TypedDict):
    sub: str
    roles: list[str]


_bearer_scheme = HTTPBearer(auto_error=False)


def _get_env() -> tuple[str, str, str, str]:
    """Read environment variables at call time (testable with monkeypatch)."""
    return (
        os.environ.get("AMA_ENVIRONMENT", os.environ.get("ENVIRONMENT", "local")),
        os.environ.get("MANAGEMENT_API_KEY", ""),
        os.environ.get("AMA_ENTRA_TENANT_ID", os.environ.get("ENTRA_TENANT_ID", "")),
        os.environ.get("AMA_ENTRA_AUDIENCE", os.environ.get("ENTRA_AUDIENCE", "api://disaster-response-hub")),
    )


def _log_auth_failure(request: Request, reason: str) -> None:
    """Structured security audit log for auth failures."""
    logger.warning(
        "management_auth_failure",
        extra={
            "reason": reason,
            "ip": request.client.host if request.client else "unknown",
            "path": str(request.url.path),
            "method": request.method,
        },
    )


def _log_auth_forbidden(
    request: Request,
    identity: str,
    roles: list[str],
    required_role: str,
) -> None:
    """Structured security audit log for authorization failures."""
    logger.warning(
        "management_auth_forbidden",
        extra={
            "identity": identity,
            "roles": roles,
            "required_role": required_role,
            "path": str(request.url.path),
        },
    )


def _validate_jwt(token: str) -> JWTClaims:
    """Validate management tokens using the shared Entra JWKS verifier."""
    try:
        from app.middleware.entra_auth import _validate_jwt as validate_entra_jwt

        return validate_entra_jwt(token)
    except ExtensionEnvelopeError as exc:
        raise HTTPException(status_code=401, detail="Invalid authorization token") from exc


async def authorize_management(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    required_role: str = "operator",
) -> AuthenticatedIdentity:
    """FastAPI dependency for management API authorization.

    Returns the authenticated identity as a dict with 'sub' and 'roles' keys.
    """
    environment, api_key_expected, _, _ = _get_env()
    if dev_access_enabled():
        return {"sub": "dev-user", "roles": ["admin", "operator", "system-administrator"]}

    if environment == "local":
        api_key = request.headers.get("X-API-Key", "")
        if not api_key or api_key != api_key_expected:
            _log_auth_failure(request, "invalid_api_key")
            raise HTTPException(status_code=401, detail="Invalid or missing API key")
        return {"sub": "local-dev", "roles": ["admin"]}

    # Production: JWT validation
    if not credentials:
        _log_auth_failure(request, "missing_token")
        raise HTTPException(status_code=401, detail="Missing authorization token")

    payload = _validate_jwt(credentials.credentials)
    roles = payload.get("roles", [])
    identity = payload.get("sub", payload.get("oid", "unknown"))

    allowed_roles = {"admin", "operator"} if required_role == "operator" else {"admin"}
    if not any(r in allowed_roles for r in roles):
        _log_auth_forbidden(request, identity, roles, required_role)
        raise HTTPException(
            status_code=403,
            detail=f"Insufficient role. Required: {required_role}",
        )

    return {"sub": identity, "roles": roles}


async def authorize_admin(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
) -> AuthenticatedIdentity:
    """Require admin role specifically."""
    return await authorize_management(request, credentials, required_role="admin")
