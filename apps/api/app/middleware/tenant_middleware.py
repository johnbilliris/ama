import logging
from typing import Any

from app.core.auth import AuthenticatedPrincipal, extract_principal_from_claims
from app.core.dev_access import dev_access_enabled
from app.core.tenant_context import TenantContext, reset_current_tenant, set_current_tenant
from app.observability.tenant_telemetry import annotate_current_span
from fastapi import FastAPI, HTTPException, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)

UNAUTHENTICATED_PATHS = {"/api/health", "/api/docs", "/api/openapi.json"}
SIMULATION_MANAGEMENT_PREFIX = "/api/simulations"
SIMULATION_ADMIN_ROLES = frozenset({"simulation.admin", "system-administrator"})


def _is_simulation_administrator(principal: AuthenticatedPrincipal) -> bool:
    return bool(SIMULATION_ADMIN_ROLES.intersection(principal.roles))


class TenantMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: Any, simulation_repository: Any = None):
        super().__init__(app)
        self._simulation_repo = simulation_repository

    def _repository(self) -> Any:
        if callable(self._simulation_repo):
            return self._simulation_repo()
        return self._simulation_repo

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        path = request.url.path

        if any(path.startswith(p) for p in UNAUTHENTICATED_PATHS):
            return await call_next(request)

        claims = getattr(request.state, "claims", None)
        if claims is None:
            return await call_next(request)

        principal = extract_principal_from_claims(claims)
        try:
            tenant_id = await self._resolve_tenant_id(path, principal, request.headers.get("X-Tenant-Id"))
        except HTTPException as exc:
            return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
        except PermissionError as exc:
            return JSONResponse(status_code=403, content={"detail": str(exc)})

        ctx = TenantContext(
            agency_id=principal.agency_id,
            jurisdiction_ids=principal.jurisdiction_ids,
            persona_id=principal.persona_id,
            tenant_id=tenant_id,
        )
        token = set_current_tenant(ctx)
        annotate_current_span(ctx)

        request.state.tenant_context = ctx
        try:
            response = await call_next(request)
            response.headers["X-Tenant-Id"] = tenant_id
            if (
                tenant_id.startswith("sim-")
                and request.method in {"POST", "PUT", "PATCH"}
                and response.status_code < 400
                and "/archive" not in path
            ):
                repository = self._repository()
                if repository is not None:
                    await repository.touch_activity(tenant_id)
            return response
        finally:
            reset_current_tenant(token)

    async def _resolve_tenant_id(
        self,
        path: str,
        principal: AuthenticatedPrincipal,
        requested_tenant_id: str | None = None,
    ) -> str:
        if (
            dev_access_enabled()
            and path.startswith("/api/personas/")
            and requested_tenant_id
            and requested_tenant_id.startswith("sim-")
        ):
            repository = self._repository()
            if repository:
                try:
                    tenant = await repository.get_by_tenant_id(requested_tenant_id)
                except Exception as exc:
                    logger.exception("Simulation tenant lookup failed for %s", requested_tenant_id)
                    raise HTTPException(status_code=503, detail="Simulation tenant store unavailable") from exc
                if tenant is None or getattr(tenant, "status", None) == "Deleted":
                    raise HTTPException(status_code=404, detail="Simulation tenant not found")
            return requested_tenant_id

        # Path-based tenant resolution for simulation data-access routes
        # e.g., /api/simulations/sim-abc123/seed → tenant_id = sim-abc123
        if path.startswith(SIMULATION_MANAGEMENT_PREFIX + "/sim-"):
            parts = path.split("/")
            if len(parts) >= 4:
                candidate = parts[3]  # /api/simulations/{tenantId}/...
                if candidate.startswith("sim-"):
                    repository = self._repository()
                    if repository:
                        try:
                            tenant = await repository.get_by_tenant_id(candidate)
                        except Exception as exc:
                            logger.exception("Simulation tenant lookup failed for %s", candidate)
                            raise HTTPException(status_code=503, detail="Simulation tenant store unavailable") from exc
                        if tenant is None or getattr(tenant, "status", None) == "Deleted":
                            raise HTTPException(status_code=404, detail="Simulation tenant not found")
                        participants = getattr(tenant, "participants", [])
                        creator = getattr(tenant, "created_by", None)
                        if (
                            principal.subject != creator
                            and principal.subject not in participants
                            and not _is_simulation_administrator(principal)
                        ):
                            # Administrators resolve the scope for retention-governed
                            # management actions; route RBAC still gates each operation.
                            logger.warning("User %s not a participant of %s", principal.subject, candidate)
                            raise PermissionError("Simulation tenant membership required")
                    return candidate

        # Top-level simulation management (list, create) operates as live
        if path.startswith(SIMULATION_MANAGEMENT_PREFIX):
            return "live"

        # Check if user is an active simulation participant
        repository = self._repository()
        if repository:
            try:
                active_sims = await repository.get_by_participant(principal.subject)
            except Exception as exc:
                logger.exception("Simulation membership lookup failed for %s", principal.subject)
                raise HTTPException(status_code=503, detail="Simulation tenant store unavailable") from exc
            if len(active_sims) == 1:
                return active_sims[0].tenant_id
            if len(active_sims) > 1:
                raise HTTPException(
                    status_code=409,
                    detail="Multiple active simulations require an explicit tenant path",
                )

        return "live"


def add_tenant_middleware(app: FastAPI, simulation_repository: Any = None) -> None:
    app.add_middleware(TenantMiddleware, simulation_repository=simulation_repository)
