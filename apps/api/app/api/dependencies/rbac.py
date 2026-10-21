from app.core.auth import AuthenticatedPrincipal
from app.core.dev_access import dev_access_enabled
from app.core.tenant_context import TenantContext
from app.repositories.simulation_repository import SimulationRepository
from fastapi import HTTPException


def require_role(principal: AuthenticatedPrincipal, expected_role: str) -> AuthenticatedPrincipal:
    if not dev_access_enabled() and expected_role not in principal.roles:
        raise PermissionError(f"Principal is missing required role: {expected_role}")
    return principal


def require_simulation_role(principal: AuthenticatedPrincipal) -> AuthenticatedPrincipal:
    if not principal.has_simulation_role:
        raise PermissionError("Principal is missing required role: SimulationUser")
    return principal


def require_simulation_admin(principal: AuthenticatedPrincipal) -> AuthenticatedPrincipal:
    if not dev_access_enabled() and not {"simulation.admin", "system-administrator"}.intersection(principal.roles):
        raise PermissionError("Principal is missing required simulation administrator role")
    return principal


async def require_simulation_participant(
    principal: AuthenticatedPrincipal,
    tenant_id: str,
    simulation_repository: SimulationRepository,
) -> AuthenticatedPrincipal:
    """Verify the caller is a participant of the named simulation.

    Distinguishes three outcomes:

    * tenant doesn't exist → ``404`` (not ``403``) — the previous behaviour
      conflated a missing tenant with a membership failure, which produced
      misleading "User anonymous is not a participant …" errors whenever the
      in-memory repo was wiped (e.g. uvicorn reload, process restart).
    * caller is ``created_by`` → allowed. The creator is always implicitly a
      participant even if the stored list drifted (e.g. migrations).
    * caller absent from ``participants`` → ``403``.
    """
    repo = simulation_repository
    tenant = await repo.get_by_tenant_id(tenant_id)
    if tenant is None:
        raise HTTPException(status_code=404, detail="Simulation tenant not found")
    if dev_access_enabled():
        return principal
    if principal.subject == getattr(tenant, "created_by", None):
        return principal
    if principal.subject in getattr(tenant, "participants", []):
        return principal
    raise PermissionError(f"User {principal.subject} is not a participant of simulation {tenant_id}")


def build_tenant_context(principal: AuthenticatedPrincipal, tenant_id: str = "live") -> TenantContext:
    return TenantContext(
        agency_id=principal.agency_id,
        jurisdiction_ids=principal.jurisdiction_ids,
        persona_id=principal.persona_id,
        tenant_id=tenant_id,
    )
