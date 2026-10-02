from enum import StrEnum

from app.core.auth import require_authenticated_persona
from app.services.state_store import HANDOFF_EVENTS
from fastapi import APIRouter, HTTPException, Query, Request

router = APIRouter(tags=["incidents"])


class HandoffStatus(StrEnum):
    pending = "pending"
    delivered = "delivered"
    retrying = "retrying"
    failed = "failed"
    dead_lettered = "dead_lettered"


def _reject_unknown_filters(request: Request, allowed: set[str]) -> None:
    unexpected = sorted({key for key in request.query_params.keys() if key not in allowed})
    if unexpected:
        raise HTTPException(status_code=422, detail=f"Unsupported query parameter(s): {', '.join(unexpected)}")


@router.get("/incidents/{incident_id}/handoffs")
async def list_handoffs(
    request: Request,
    incident_id: str,
    status: HandoffStatus | None = Query(default=None),
) -> list[dict[str, object]]:
    require_authenticated_persona(request)
    _reject_unknown_filters(request, {"status"})
    events = HANDOFF_EVENTS.get(incident_id, [])
    events = [event for event in events if str(event.get("incidentId")) == incident_id]
    if status is None:
        return events
    return [event for event in events if event.get("status") == status.value]
