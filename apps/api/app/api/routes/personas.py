from app.api.dependencies.simulation_composition import get_simulation_repository
from app.core.auth import extract_principal_from_claims
from app.core.dev_access import dev_access_enabled
from app.core.tenant_context import get_current_tenant
from app.services.persona_workspace_service import PersonaWorkspaceService
from fastapi import APIRouter, HTTPException, Query, Request

router = APIRouter(prefix="/personas", tags=["personas"])


@router.get("/{persona_id}/workspace")
async def get_persona_workspace(
    persona_id: str,
    request: Request,
    incidentId: str = Query(..., min_length=1),
) -> dict[str, object]:
    principal = extract_principal_from_claims(request.state.claims)
    dev_access = dev_access_enabled()
    if not dev_access and principal.persona_id != persona_id:
        raise HTTPException(status_code=403, detail="Workspace persona must match authenticated persona")

    try:
        tenant_id = get_current_tenant().tenant_id
    except LookupError:
        tenant_id = "live"
    assignment = None
    if tenant_id.startswith("sim-"):
        tenant = await get_simulation_repository().get_by_tenant_id(tenant_id)
        if tenant is None:
            raise HTTPException(status_code=404, detail="Simulation tenant not found")
        assignment = next(
            (
                candidate
                for candidate in tenant.participant_assignments
                if candidate.persona_id == persona_id and (dev_access or candidate.oid == principal.subject)
            ),
            None,
        )
        if assignment is None and not dev_access:
            raise HTTPException(status_code=403, detail="Simulation persona assignment required")
    return PersonaWorkspaceService().get_workspace(
        persona_id,
        incidentId,
        assignment=assignment,
        tenant_id=tenant_id,
    )
