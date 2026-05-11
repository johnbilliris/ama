"""Spec-036 Wave 4 — RBAC dependency for coordinator-only routes (T-M01..M04).

Closes critical finding C3 (``anonymous-coord`` fallback). Per FR-051
(Amendment E STRENGTHEN) every coordinator-only route MUST validate
JWT/app-role + tenant membership BEFORE any audit attempt; anonymous
fallbacks are PROHIBITED in production.

This module exposes:

* :class:`CoordinatorPrincipal` — the validated, immutable principal
  attached to ``request.state.coordinator_principal`` for downstream use.
* :func:`require_simulation_coordinator` — FastAPI dependency that
  reads ``request.state.claims`` (populated by
  :class:`apps.api.app.middleware.auth_middleware.AuthMiddleware` from
  the Container Apps EasyAuth ``X-MS-CLIENT-PRINCIPAL`` header) and
  verifies the principal carries ``simulation.coordinator``. On rejection
  it writes an ``audit.rbac.unauthorized_attempt`` envelope (T-M03) and
  raises ``HTTPException(403, application/problem+json forbidden-role)``.

Tests use ``app.dependency_overrides[require_simulation_coordinator]``
to inject a coordinator (or an explicit principal carrying any role)
without round-tripping JWTs.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Final
from uuid import uuid4

from fastapi import HTTPException, Path, Request

logger = logging.getLogger(__name__)


#: Canonical role string per FR-051 (Amendment E STRENGTHEN).
COORDINATOR_ROLE: Final[str] = "simulation.coordinator"

#: Canonical role string for the read-only observer role.
OBSERVER_ROLE: Final[str] = "simulation.observer"

#: Canonical role string for the admin role.
ADMIN_ROLE: Final[str] = "simulation.admin"


@dataclass(frozen=True)
class CoordinatorPrincipal:
    """Validated coordinator principal — owned by route handlers."""

    user_id: str
    tenant_id: str
    roles: tuple[str, ...] = field(default_factory=tuple)
    request_correlation_id: str | None = None

    @property
    def is_coordinator(self) -> bool:
        return COORDINATOR_ROLE in self.roles


def _claims_from_request(request: Request) -> dict[str, Any]:
    """Read the claims dict populated by :class:`AuthMiddleware`.

    Returns an empty dict when no claims are set so callers see an
    explicit deny (the authoritative path) rather than a silent pass.
    """

    state = getattr(request, "state", None)
    if state is None:
        return {}
    claims = getattr(state, "claims", None)
    if isinstance(claims, dict):
        return claims
    return {}


def _principal_from_claims(claims: dict[str, Any]) -> CoordinatorPrincipal:
    """Build a :class:`CoordinatorPrincipal` from the request claims dict."""

    user_id = str(claims.get("sub") or claims.get("oid") or "anonymous")
    tenant_id = str(claims.get("tenant_id") or claims.get("tid") or "unknown-tenant")
    roles_raw = claims.get("roles") or claims.get("app_roles") or []
    if isinstance(roles_raw, str):
        roles_tuple: tuple[str, ...] = (roles_raw,)
    else:
        roles_tuple = tuple(str(r) for r in roles_raw)
    return CoordinatorPrincipal(
        user_id=user_id,
        tenant_id=tenant_id,
        roles=roles_tuple,
    )


def _problem_detail(*, status: int, type_id: str, title: str, **extra: Any) -> dict[str, Any]:
    detail: dict[str, Any] = {
        "type": f"https://aidr.gov.au/problems/{type_id}",
        "title": title,
        "status": status,
    }
    detail.update(extra)
    return detail


async def _emit_rbac_denial_audit(
    *,
    principal: CoordinatorPrincipal,
    route: str,
    sim_id: str | None,
    reason: str,
    request_correlation_id: str,
) -> None:
    """Write the ``audit.rbac.unauthorized_attempt`` envelope (T-M03)."""

    # Imported lazily to avoid a circular import via audit_writer → repos.
    from apps.api.app.services.simulation.audit_writer import get_audit_writer

    audit = get_audit_writer()
    try:
        await audit.write(
            "audit.rbac.unauthorized_attempt",
            simulation_id=sim_id or "unknown",
            actor="simulation_rbac",
            request_correlation_id=request_correlation_id,
            details={
                "subject": {
                    "user_id": principal.user_id,
                    "tenant_id": principal.tenant_id,
                },
                "route": route,
                "requested_role": "coordinator",
                "actual_roles": list(principal.roles),
                "reason": reason,
                "sim_id": sim_id,
                "request_correlation_id": request_correlation_id,
            },
        )
    except Exception:  # pragma: no cover - audit failure is non-fatal
        logger.exception(
            "rbac.audit_emit_failed user=%s route=%s",
            principal.user_id,
            route,
        )


async def require_simulation_coordinator(
    request: Request,
    sim_id: str = Path(..., min_length=1, description="Simulation ID"),
) -> CoordinatorPrincipal:
    """Validate coordinator-role membership for a simulation route.

    Raises ``HTTPException(403)`` with ``application/problem+json`` body
    ``forbidden-role`` and writes ``audit.rbac.unauthorized_attempt``
    (T-M03) on rejection. On success returns a :class:`CoordinatorPrincipal`
    that the route handler can use for downstream user_id propagation.

    Per FR-051 the deny decision is authoritative — even on idempotent
    replay the cached response MUST NOT be served when an RBAC denial
    fires (audit-envelope.md §6.3 cross-references).
    """

    request_correlation_id = (
        request.headers.get("X-Request-Correlation-Id") if request else None
    ) or str(uuid4())

    claims = _claims_from_request(request)
    if not claims:
        principal = CoordinatorPrincipal(
            user_id="anonymous",
            tenant_id="unknown-tenant",
            roles=(),
            request_correlation_id=request_correlation_id,
        )
        await _emit_rbac_denial_audit(
            principal=principal,
            route=str(request.url.path),
            sim_id=sim_id,
            reason="missing_role",
            request_correlation_id=request_correlation_id,
        )
        raise HTTPException(
            status_code=403,
            detail=_problem_detail(
                status=403,
                type_id="forbidden-role",
                title="Coordinator role required",
                detail=(
                    "The simulation.coordinator role is required for this "
                    "route; no claims were presented."
                ),
                requested_role="coordinator",
            ),
        )

    principal = _principal_from_claims(claims)
    if request_correlation_id and principal.request_correlation_id is None:
        principal = CoordinatorPrincipal(
            user_id=principal.user_id,
            tenant_id=principal.tenant_id,
            roles=principal.roles,
            request_correlation_id=request_correlation_id,
        )

    if not principal.is_coordinator:
        await _emit_rbac_denial_audit(
            principal=principal,
            route=str(request.url.path),
            sim_id=sim_id,
            reason="missing_role",
            request_correlation_id=request_correlation_id,
        )
        raise HTTPException(
            status_code=403,
            detail=_problem_detail(
                status=403,
                type_id="forbidden-role",
                title="Coordinator role required",
                detail=(
                    f"Principal {principal.user_id!r} carried roles "
                    f"{list(principal.roles)!r} but lacked "
                    f"{COORDINATOR_ROLE!r}."
                ),
                requested_role="coordinator",
                actual_roles=list(principal.roles),
            ),
        )

    expected_tenant = claims.get("tenant_id") or claims.get("tid")
    declared_tenant = request.headers.get("X-Tenant-Id") if request else None
    if declared_tenant and expected_tenant and declared_tenant != expected_tenant:
        await _emit_rbac_denial_audit(
            principal=principal,
            route=str(request.url.path),
            sim_id=sim_id,
            reason="tenant_mismatch",
            request_correlation_id=request_correlation_id,
        )
        raise HTTPException(
            status_code=403,
            detail=_problem_detail(
                status=403,
                type_id="forbidden-tenant",
                title="Tenant mismatch",
                detail=(
                    f"Principal tenant {expected_tenant!r} does not match "
                    f"the requested simulation tenant {declared_tenant!r}."
                ),
            ),
        )

    # Stash for downstream consumers.
    if hasattr(request, "state"):
        request.state.coordinator_principal = principal
    return principal


__all__ = [
    "ADMIN_ROLE",
    "COORDINATOR_ROLE",
    "CoordinatorPrincipal",
    "OBSERVER_ROLE",
    "require_simulation_coordinator",
]
