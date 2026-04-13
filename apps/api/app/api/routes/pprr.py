"""PPRR lifecycle API routes.

Provides endpoints for PPRR phase transitions on incidents and
management of non-incident PPRR phase contexts.

FRs: FR-031, FR-050, FR-053
"""

from app.services.pprr_service import PprrService
from app.services.state_store import INCIDENTS
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/incidents/{incident_id}/pprr", tags=["pprr"])
context_router = APIRouter(prefix="/pprr", tags=["pprr"])
service = PprrService()


class TransitionPhaseInput(BaseModel):
    target_phase: str
    rationale: str
    authorising_user: str
    overlap_active: bool = False
    overlap_end_expected_at: str | None = None


class CreateContextInput(BaseModel):
    context_type: str
    context_reference_id: str
    pprr_phase: str
    activated_by: str
    notes: str = ""


class TransitionToIncidentInput(BaseModel):
    incident_id: str


@router.post("/transition")
async def transition_phase(
    incident_id: str, payload: TransitionPhaseInput,
) -> dict[str, object]:
    if incident_id not in INCIDENTS:
        raise HTTPException(status_code=404, detail="Incident not found")
    try:
        result = service.transition_phase(
            incident_id=incident_id,
            target_phase=payload.target_phase,
            rationale=payload.rationale,
            authorising_user=payload.authorising_user,
            overlap_active=payload.overlap_active,
            overlap_end_expected_at=payload.overlap_end_expected_at,
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return result


@router.get("")
async def get_phase_info(incident_id: str) -> dict[str, object]:
    if incident_id not in INCIDENTS:
        raise HTTPException(status_code=404, detail="Incident not found")
    return service.get_phase_info(incident_id)


@context_router.post("/contexts")
async def create_context(payload: CreateContextInput) -> dict[str, object]:
    try:
        context = service.create_context(
            context_type=payload.context_type,
            context_reference_id=payload.context_reference_id,
            pprr_phase=payload.pprr_phase,
            activated_by=payload.activated_by,
            notes=payload.notes,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return context.model_dump(mode="json")


@context_router.get("/contexts")
async def list_contexts(active_only: bool = True) -> list[dict[str, object]]:
    contexts = service.list_contexts(active_only=active_only)
    return [c.model_dump(mode="json") for c in contexts]


@context_router.put("/contexts/{context_id}/transition-to-incident")
async def transition_context_to_incident(
    context_id: str, payload: TransitionToIncidentInput,
) -> dict[str, object]:
    try:
        context = service.transition_context_to_incident(
            context_id=context_id,
            incident_id=payload.incident_id,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return context.model_dump(mode="json")
