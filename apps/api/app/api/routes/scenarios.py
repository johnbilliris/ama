from app.services.rehearsal_orchestrator import RehearsalOrchestrator
from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(prefix="/scenarios", tags=["scenarios"])


class ScenarioReplayInput(BaseModel):
    scenarioName: str
    scenarioType: str
    jurisdictionIds: list[str] = Field(default_factory=list)


@router.post("/replay")
async def replay_scenario(payload: ScenarioReplayInput) -> dict[str, object]:
    scenario_run = RehearsalOrchestrator().run(payload.scenarioName, payload.scenarioType, payload.jurisdictionIds)
    return scenario_run.model_dump(mode="json")
