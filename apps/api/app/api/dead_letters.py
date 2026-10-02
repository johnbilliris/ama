from typing import Literal

from app.core.auth import require_authenticated_persona
from app.services.dead_letter_service import DeadLetterService
from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, ConfigDict, Field

ResolutionType = Literal["replayed", "discarded", "escalated"]


class ResolveDeadLetterRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    resolution: ResolutionType
    resolved_by_persona_id: str = Field(alias="resolvedByPersonaId")
    notes: str | None = None


def _reject_unknown_filters(request: Request, allowed: set[str]) -> None:
    unexpected = sorted({key for key in request.query_params.keys() if key not in allowed})
    if unexpected:
        raise HTTPException(status_code=422, detail=f"Unsupported query parameter(s): {', '.join(unexpected)}")


router = APIRouter(tags=["operations"])
service = DeadLetterService()


@router.get("/dead-letters")
async def list_dead_letters(
    request: Request,
    entry_type: Literal["handoff_failure", "ingestion_failure", "event_delivery_failure"] | None = Query(
        default=None,
        alias="entryType",
    ),
    resolution: Literal["pending", "replayed", "discarded", "escalated"] | None = Query(default="pending"),
    incident_id: str | None = Query(default=None, alias="incidentId"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> dict[str, object]:
    require_authenticated_persona(request)
    _reject_unknown_filters(request, {"entryType", "resolution", "incidentId", "limit", "offset"})
    items, total = service.query_entries(
        entry_type=entry_type,
        resolution=resolution,
        incident_id=incident_id,
        limit=limit,
        offset=offset,
    )
    return {
        "items": [item.model_dump(mode="json", by_alias=True) for item in items],
        "total": total,
    }


@router.post("/dead-letters/{entry_id}/resolve")
async def resolve_dead_letter(request: Request, entry_id: str, payload: ResolveDeadLetterRequest) -> dict[str, object]:
    verified_persona_id = require_authenticated_persona(request, asserted_persona_id=payload.resolved_by_persona_id)
    resolved = service.resolve_entry(
        entry_id=entry_id,
        resolution=payload.resolution,
        resolved_by_persona_id=verified_persona_id,
        notes=payload.notes,
    )
    return resolved.model_dump(mode="json", by_alias=True)
