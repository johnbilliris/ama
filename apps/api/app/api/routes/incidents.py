from fastapi import APIRouter, HTTPException

from app.services.dashboard_service import DashboardService
from app.services.state_store import INCIDENTS

router = APIRouter(prefix="/incidents", tags=["incidents"])


@router.get("/{incident_id}/dashboard")
async def get_dashboard(incident_id: str) -> dict[str, object]:
    if incident_id not in INCIDENTS:
        raise HTTPException(status_code=404, detail="Incident not found")
    return DashboardService().get_dashboard(incident_id)
