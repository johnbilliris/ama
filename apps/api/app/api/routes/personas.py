from fastapi import APIRouter

from app.services.persona_workspace_service import PersonaWorkspaceService

router = APIRouter(prefix="/personas", tags=["personas"])


@router.get("/{persona_id}/workspace")
async def get_persona_workspace(persona_id: str) -> dict[str, object]:
    return PersonaWorkspaceService().get_workspace(persona_id)
