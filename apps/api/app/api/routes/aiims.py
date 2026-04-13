"""AIIMS structure and incident-level API routes.

Provides endpoints for managing AIIMS role assignments, viewing
the Common Operating Picture structure, and changing incident levels.

FRs: FR-013, FR-014, FR-049
"""

from app.services.aiims_service import AiimsService
from app.services.state_store import AIIMS_ASSIGNMENTS, INCIDENTS
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/incidents/{incident_id}/aiims", tags=["aiims"])
level_router = APIRouter(prefix="/incidents/{incident_id}", tags=["aiims"])
service = AiimsService()


class AssignRoleInput(BaseModel):
    agent_identifier: str
    aiims_function: str
    assigned_by: str


class UpdateAssignmentInput(BaseModel):
    aiims_function: str | None = None
    is_active: bool | None = None


class ChangeLevelInput(BaseModel):
    new_level: int
    rationale: str
    authorising_user: str


@router.post("/assignments")
async def assign_role(
    incident_id: str, payload: AssignRoleInput,
) -> dict[str, object]:
    if incident_id not in INCIDENTS:
        raise HTTPException(status_code=404, detail="Incident not found")
    try:
        assignment = service.assign_role(
            incident_id=incident_id,
            agent_identifier=payload.agent_identifier,
            aiims_function=payload.aiims_function,  # type: ignore[arg-type]
            assigned_by=payload.assigned_by,
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return assignment.model_dump(mode="json")


@router.get("/structure")
async def get_structure(incident_id: str) -> dict[str, object]:
    if incident_id not in INCIDENTS:
        raise HTTPException(status_code=404, detail="Incident not found")
    return service.get_structure(incident_id)


@router.put("/assignments/{assignment_id}")
async def update_assignment(
    incident_id: str,
    assignment_id: str,
    payload: UpdateAssignmentInput,
) -> dict[str, object]:
    if incident_id not in INCIDENTS:
        raise HTTPException(status_code=404, detail="Incident not found")
    if assignment_id not in AIIMS_ASSIGNMENTS:
        raise HTTPException(status_code=404, detail="Assignment not found")
    assignment = service.update_assignment(
        assignment_id,
        aiims_function=payload.aiims_function,  # type: ignore[arg-type]
        is_active=payload.is_active,
    )
    return assignment.model_dump(mode="json")


@level_router.post("/level")
async def change_incident_level(
    incident_id: str, payload: ChangeLevelInput,
) -> dict[str, object]:
    if incident_id not in INCIDENTS:
        raise HTTPException(status_code=404, detail="Incident not found")
    try:
        result = service.change_incident_level(
            incident_id=incident_id,
            new_level=payload.new_level,
            rationale=payload.rationale,
            authorising_user=payload.authorising_user,
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return result
