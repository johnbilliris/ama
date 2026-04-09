from datetime import UTC, datetime
from uuid import uuid4

from fastapi import APIRouter

from packages.domain.src.domain.models.simulation_run import SimulationRun
from packages.domain.src.domain.models.simulation_scenario import SimulationScenario

router = APIRouter(prefix="/simulations", tags=["simulation"])

SCENARIOS: dict[str, SimulationScenario] = {}
RUNS: dict[str, SimulationRun] = {}


@router.get("/scenarios")
async def list_scenarios() -> list[dict]:
    return [s.model_dump(mode="json") for s in SCENARIOS.values()]


@router.post("/scenarios", status_code=201)
async def create_scenario(body: dict) -> dict:
    scenario_id = f"scn-{uuid4().hex[:8]}"
    scenario = SimulationScenario(scenario_id=scenario_id, **body)
    SCENARIOS[scenario_id] = scenario
    return scenario.model_dump(mode="json")


@router.post("/runs", status_code=202)
async def start_run(body: dict) -> dict:
    scenario_id = body["scenarioId"]
    if scenario_id not in SCENARIOS:
        return {"error": f"Scenario {scenario_id} not found"}
    run_id = f"run-{uuid4().hex[:8]}"
    run = SimulationRun(
        run_id=run_id,
        scenario_id=scenario_id,
        time_compression_ratio=body.get("timeCompressionRatio", 1.0),
        misinformation_ratio=body.get("misinformationRatio", 0.15),
        created_by=body.get("requestedByPersonaId", ""),
    )
    run = run.transition_to("running")
    RUNS[run_id] = run
    return run.model_dump(mode="json")


@router.get("/runs/{run_id}")
async def get_run(run_id: str) -> dict:
    run = RUNS.get(run_id)
    if not run:
        return {"error": f"Run {run_id} not found"}
    return run.model_dump(mode="json")


@router.post("/runs/{run_id}/abort")
async def abort_run(run_id: str, body: dict) -> dict:
    run = RUNS.get(run_id)
    if not run:
        return {"error": f"Run {run_id} not found"}
    run = run.transition_to("aborted")
    RUNS[run_id] = run
    return run.model_dump(mode="json")
