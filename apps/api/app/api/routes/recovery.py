"""Community recovery API routes.

Provides endpoints for initialising recovery trackers, updating
indicators, and viewing dashboards including a community-safe view.

FRs: FR-032–037 | SCs: SC-005
"""

from app.services.recovery_service import RecoveryService
from app.services.state_store import INCIDENTS
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/incidents/{incident_id}/recovery", tags=["recovery"])
service = RecoveryService()


class UpdateIndicatorInput(BaseModel):
    value: float
    update_source: str = "manual"
    population_coverage: int | None = None
    linked_alert_id: str | None = None


class BatchIndicatorItem(BaseModel):
    indicator_name: str
    value: float
    update_source: str = "manual"
    population_coverage: int | None = None
    linked_alert_id: str | None = None


class BatchUpdateInput(BaseModel):
    updates: list[BatchIndicatorItem]


def _require_incident(incident_id: str) -> None:
    if incident_id not in INCIDENTS:
        raise HTTPException(status_code=404, detail="Incident not found")


@router.post("")
async def initialise_tracker(incident_id: str) -> dict[str, object]:
    _require_incident(incident_id)
    try:
        tracker = service.initialise_tracker(incident_id)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return tracker.model_dump(mode="json")


@router.get("/dashboard")
async def get_dashboard(incident_id: str) -> dict[str, object]:
    _require_incident(incident_id)
    try:
        return service.get_dashboard(incident_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.put("/indicators/{indicator_name}")
async def update_indicator(
    incident_id: str,
    indicator_name: str,
    payload: UpdateIndicatorInput,
) -> dict[str, object]:
    _require_incident(incident_id)
    try:
        return service.update_indicator(
            incident_id=incident_id,
            indicator_name=indicator_name,
            value=payload.value,
            update_source=payload.update_source,
            population_coverage=payload.population_coverage,
            linked_alert_id=payload.linked_alert_id,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/indicators/batch")
async def batch_update_indicators(
    incident_id: str,
    payload: BatchUpdateInput,
) -> dict[str, object]:
    _require_incident(incident_id)
    try:
        return service.batch_update_indicators(
            incident_id=incident_id,
            updates=[u.model_dump() for u in payload.updates],
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/community")
async def get_community_view(incident_id: str) -> dict[str, object]:
    _require_incident(incident_id)
    try:
        return service.get_community_view(incident_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
