from typing import Literal

from app.services.dead_letter_service import DeadLetterService
from fastapi import APIRouter, Query
from pydantic import BaseModel

ResolutionType = Literal["replayed", "discarded", "escalated"]


class ResolveDeadLetterRequest(BaseModel):
    resolution: ResolutionType
    resolved_by_persona_id: str
    notes: str | None = None


router = APIRouter(tags=["operations"])
service = DeadLetterService()


@router.get("/dead-letters")
async def list_dead_letters(
    entry_type: str | None = Query(default=None),
    resolution: str | None = Query(default=None),
    incident_id: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> dict[str, object]:
    items, total = service.query_entries(
        entry_type=entry_type,
        resolution=resolution,
        incident_id=incident_id,
        limit=limit,
        offset=offset,
    )
    return {
        "items": [item.model_dump(mode="json") for item in items],
        "total": total,
    }


@router.post("/dead-letters/{entry_id}/resolve")
async def resolve_dead_letter(
    entry_id: str, payload: ResolveDeadLetterRequest
) -> dict[str, object]:
    resolved = service.resolve_entry(
        entry_id=entry_id,
        resolution=payload.resolution,
        resolved_by_persona_id=payload.resolved_by_persona_id,
        notes=payload.notes,
    )
    return resolved.model_dump(mode="json")
