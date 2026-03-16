from fastapi import APIRouter, Query

from app.services.state_store import HANDOFF_EVENTS


router = APIRouter(tags=["incidents"])


@router.get("/incidents/{incident_id}/handoffs")
async def list_handoffs(
    incident_id: str,
    status: str | None = Query(default=None),
) -> list[dict[str, object]]:
    events = HANDOFF_EVENTS.get(incident_id, [])
    if status is None:
        return events
    return [event for event in events if event.get("status") == status]
