from app.core.auth import AuthenticatedPrincipal
from app.core.tenant_context import TenantContext


def require_role(principal: AuthenticatedPrincipal, expected_role: str) -> AuthenticatedPrincipal:
    if expected_role not in principal.roles:
        raise PermissionError(f"Principal is missing required role: {expected_role}")
    return principal


def build_tenant_context(principal: AuthenticatedPrincipal) -> TenantContext:
    return TenantContext(
        agency_id=principal.agency_id,
        jurisdiction_ids=principal.jurisdiction_ids,
        persona_id=principal.persona_id,
    )
