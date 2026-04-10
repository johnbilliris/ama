from app.services.dashboard_service import DashboardService
from app.services.resource_governor import ResourceGovernor
from app.services.state_store import INCIDENTS
from app.repositories.simulation_repository import SimulationRepository
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/incidents", tags=["incidents"])

_sim_repo = SimulationRepository()
_governor = ResourceGovernor(simulation_repository=_sim_repo)


@router.get("/{incident_id}/dashboard")
async def get_dashboard(incident_id: str) -> dict[str, object]:
    if incident_id not in INCIDENTS:
        raise HTTPException(status_code=404, detail="Incident not found")
    return DashboardService().get_dashboard(incident_id)


@router.post("/declare")
async def declare_incident() -> dict:
    affected = await _governor.declare_incident()
    return {"status": "incident_declared", "simulations_throttled": affected}


@router.post("/resolve")
async def resolve_incident() -> dict:
    restored = await _governor.resolve_incident()
    return {"status": "incident_resolved", "simulations_restored": restored}
