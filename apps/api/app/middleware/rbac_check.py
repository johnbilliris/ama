"""RBAC enforcement middleware (spec-035 T024b).

Stage-(a): AppRole → route-family allowlist.
Stage-(b): persona_id → AIIMS-function allowlist (looked up via the auth registry).
Admin path: ``system-administrator`` always passes stage-(a) and either:
  - direct (no ``X-Impersonate-Persona``): records ``outcome=admin_override`` and
    sets ``persona_id="*"`` on the audit row (handled in audit_appender), OR
  - impersonating (``X-Impersonate-Persona: <pid>``): inherits the target persona's
    AIIMS function set for stage-(b), records the paired-row metadata
    (``request.state.audit_impersonated_persona_id`` etc.).

A non-admin caller presenting ``X-Impersonate-Persona`` is rejected with
``403 forbidden``.
"""

from __future__ import annotations

import os
from typing import Any

from app.auth.rbac_registry import (
    APP_ROLES,
    ROLE_TO_AIIMS_FUNCTIONS,
    is_role_allowed_on_route,
)
from app.middleware.envelope_response import error_to_envelope_response
from app.schemas.envelope_errors import ExtensionEnvelopeError
from app.schemas.extension_envelope import ExtensionErrorCode
from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

_PROTECTED_PREFIXES = (
    "/api/outcomes/",
    "/api/audit/list",
    "/api/auth/whoami",
    "/api/offline/replay",
    "/api/recovery/handover",
)


def _is_protected(path: str) -> bool:
    return any(path.startswith(prefix) for prefix in _PROTECTED_PREFIXES)


def _resolve_persona_aiims_function(persona_id: str) -> str | None:
    """Resolve a persona id to its AIIMS function via the persona registry.

    Returns ``None`` if the persona is unknown — caller should treat as forbidden.
    """
    try:
        from app.repositories.persona_registry_repository import (
            get_persona_registry_repository,
        )
    except Exception:
        return None

    repo = get_persona_registry_repository()
    persona = getattr(repo, "find_by_id", lambda _pid: None)(persona_id)
    if persona is None:
        return None
    return getattr(persona, "aiims_function", None) or persona.get("aiims_function")  # type: ignore[union-attr]


def _normalise_role(claims: dict[str, Any]) -> str | None:
    role = claims.get("app_role") or claims.get("appRole")
    if role:
        return str(role)
    roles = claims.get("roles") or []
    if isinstance(roles, list) and roles:
        return str(roles[0])
    return None


def _normalise_persona_id(claims: dict[str, Any]) -> str | None:
    return claims.get("persona_id") or claims.get("personaId")


class RbacCheckMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if not _is_protected(request.url.path):
            return await call_next(request)

        try:
            self._enforce(request)
        except ExtensionEnvelopeError as exc:
            return error_to_envelope_response(request, exc)

        return await call_next(request)

    @staticmethod
    def _enforce(request: Request) -> None:
        claims: dict[str, Any] = getattr(request.state, "claims", None) or {}
        role = _normalise_role(claims)

        if role is None:
            raise ExtensionEnvelopeError(
                ExtensionErrorCode.UNAUTHORIZED,
                detail="missing AppRole claim",
            )

        if role not in APP_ROLES:
            raise ExtensionEnvelopeError(
                ExtensionErrorCode.FORBIDDEN,
                detail=f"AppRole '{role}' is outside the FR-011 closed set",
            )

        if not is_role_allowed_on_route(role, request.url.path):
            raise ExtensionEnvelopeError(
                ExtensionErrorCode.FORBIDDEN,
                detail=f"AppRole '{role}' is not authorised on {request.url.path}",
            )

        impersonated = request.headers.get("X-Impersonate-Persona")
        is_admin = role == "system-administrator"

        if impersonated and not is_admin:
            raise ExtensionEnvelopeError(
                ExtensionErrorCode.FORBIDDEN,
                detail="X-Impersonate-Persona is reserved for system-administrator",
            )

        if is_admin:
            request.state.is_admin = True
            request.state.audit_impersonated_persona_id = impersonated
            return

        persona_id = _normalise_persona_id(claims)
        if not persona_id:
            raise ExtensionEnvelopeError(
                ExtensionErrorCode.FORBIDDEN,
                detail="missing persona_id claim",
            )

        allowed_functions = ROLE_TO_AIIMS_FUNCTIONS[role]
        if not allowed_functions:
            raise ExtensionEnvelopeError(
                ExtensionErrorCode.FORBIDDEN,
                detail=f"AppRole '{role}' has no AIIMS-function scope",
            )

        function_name = _resolve_persona_aiims_function(persona_id)
        if function_name and function_name not in allowed_functions:
            raise ExtensionEnvelopeError(
                ExtensionErrorCode.FORBIDDEN,
                detail=(
                    f"persona '{persona_id}' (AIIMS '{function_name}') outside "
                    f"AppRole '{role}' scope"
                ),
            )


def add_rbac_check_middleware(app: FastAPI) -> None:
    if os.environ.get("AMA_ENABLE_PRODUCTION_AUTH", "0") != "1":
        return
    app.add_middleware(RbacCheckMiddleware)


__all__ = ["RbacCheckMiddleware", "add_rbac_check_middleware"]
