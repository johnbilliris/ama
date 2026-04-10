from app.core.auth import AuthenticatedPrincipal
from app.core.tenant_context import TenantContext


def require_role(principal: AuthenticatedPrincipal, expected_role: str) -> AuthenticatedPrincipal:
    if expected_role not in principal.roles:
        raise PermissionError(f"Principal is missing required role: {expected_role}")
    return principal


def require_simulation_role(principal: AuthenticatedPrincipal) -> AuthenticatedPrincipal:
    if not principal.has_simulation_role:
        raise PermissionError("Principal is missing required role: SimulationUser")
    return principal


async def require_simulation_participant(
    principal: AuthenticatedPrincipal,
    tenant_id: str,
    simulation_repository: object,
) -> AuthenticatedPrincipal:
    repo = simulation_repository  # type: ignore[assignment]
    is_member = await repo.is_participant(tenant_id, principal.subject)
    if not is_member:
        raise PermissionError(
            f"User {principal.subject} is not a participant of simulation {tenant_id}"
        )
    return principal


def build_tenant_context(principal: AuthenticatedPrincipal, tenant_id: str = "live") -> TenantContext:
    return TenantContext(
        agency_id=principal.agency_id,
        jurisdiction_ids=principal.jurisdiction_ids,
        persona_id=principal.persona_id,
        tenant_id=tenant_id,
    )
