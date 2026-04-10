import logging
from typing import Any

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from app.core.auth import AuthenticatedPrincipal, extract_principal_from_claims
from app.core.tenant_context import TenantContext, set_current_tenant

logger = logging.getLogger(__name__)

UNAUTHENTICATED_PATHS = {"/api/health", "/api/docs", "/api/openapi.json"}
SIMULATION_MANAGEMENT_PREFIX = "/api/simulations"


class TenantMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: Any, simulation_repository: Any = None):
        super().__init__(app)
        self._simulation_repo = simulation_repository

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        path = request.url.path

        if any(path.startswith(p) for p in UNAUTHENTICATED_PATHS):
            return await call_next(request)

        claims = getattr(request.state, "claims", None)
        if claims is None:
            return await call_next(request)

        principal = extract_principal_from_claims(claims)
        tenant_id = await self._resolve_tenant_id(path, principal)

        ctx = TenantContext(
            agency_id=principal.agency_id,
            jurisdiction_ids=principal.jurisdiction_ids,
            persona_id=principal.persona_id,
            tenant_id=tenant_id,
        )
        set_current_tenant(ctx)

        request.state.tenant_context = ctx

        response = await call_next(request)
        response.headers["X-Tenant-Id"] = tenant_id
        return response

    async def _resolve_tenant_id(self, path: str, principal: AuthenticatedPrincipal) -> str:
        # Path-based tenant resolution for simulation data-access routes
        # e.g., /api/simulations/sim-abc123/seed → tenant_id = sim-abc123
        if path.startswith(SIMULATION_MANAGEMENT_PREFIX + "/sim-"):
            parts = path.split("/")
            if len(parts) >= 4:
                candidate = parts[3]  # /api/simulations/{tenantId}/...
                if candidate.startswith("sim-"):
                    if self._simulation_repo:
                        is_member = await self._simulation_repo.is_participant(
                            candidate, principal.subject
                        )
                        if not is_member:
                            logger.warning(
                                "User %s not a participant of %s",
                                principal.subject,
                                candidate,
                            )
                    return candidate

        # Top-level simulation management (list, create) operates as live
        if path.startswith(SIMULATION_MANAGEMENT_PREFIX):
            return "live"

        # Check if user is an active simulation participant
        if self._simulation_repo:
            active_sims = await self._simulation_repo.get_by_participant(principal.subject)
            if active_sims:
                return active_sims[0].tenant_id

        return "live"


def add_tenant_middleware(app: FastAPI, simulation_repository: Any = None) -> None:
    app.add_middleware(TenantMiddleware, simulation_repository=simulation_repository)
