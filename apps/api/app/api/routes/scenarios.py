from app.core.auth import require_authenticated_persona
from app.services.rehearsal_orchestrator import RehearsalOrchestrator
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

router = APIRouter(prefix="/scenarios", tags=["scenarios"])


class ScenarioReplayInput(BaseModel):
    scenarioName: str
    scenarioType: str
    jurisdictionIds: list[str] = Field(default_factory=list)


class ScenarioRunStartInput(BaseModel):
    requestedByPersonaId: str


@router.post("/replay")
async def replay_scenario(payload: ScenarioReplayInput, request: Request) -> dict[str, object]:
    require_authenticated_persona(request)
    try:
        scenario_run = RehearsalOrchestrator().run(payload.scenarioName, payload.scenarioType, payload.jurisdictionIds)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return scenario_run.model_dump(mode="json")


@router.post("/{scenario_run_id}/runs", status_code=202)
async def queue_scenario_run(scenario_run_id: str, payload: ScenarioRunStartInput, request: Request) -> dict[str, str]:
    require_authenticated_persona(request, payload.requestedByPersonaId)
    return {
        "scenarioRunId": scenario_run_id,
        "status": "queued",
        "requestedByPersonaId": payload.requestedByPersonaId,
    }


@router.get("/{scenario_run_id}")
async def get_scenario_run(scenario_run_id: str, request: Request) -> dict[str, object]:
    require_authenticated_persona(request)
    run = RehearsalOrchestrator().get(scenario_run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Scenario run not found")
    return run.model_dump(mode="json")


@router.post("/{scenario_run_id}/cancel")
async def cancel_scenario_run(scenario_run_id: str, request: Request) -> dict[str, object]:
    require_authenticated_persona(request)
    try:
        run = RehearsalOrchestrator().cancel(scenario_run_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return run.model_dump(mode="json")


@router.post("/{scenario_run_id}/restart")
async def restart_scenario_run(scenario_run_id: str, request: Request) -> dict[str, object]:
    require_authenticated_persona(request)
    try:
        run = RehearsalOrchestrator().restart(scenario_run_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return run.model_dump(mode="json")
