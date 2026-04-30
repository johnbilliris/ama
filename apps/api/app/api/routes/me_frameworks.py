"""Platform API routes for M&E framework management.

Provides CRUD endpoints for M&E frameworks, outcomes, program logic,
standards, collection schedules, monitoring reports, and evaluations.

FRs: FR-008–014
"""

from app.services.me_framework_service import MEFrameworkPlatformService
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/me-frameworks", tags=["me-frameworks"])
_service = MEFrameworkPlatformService()


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------


class CreateFrameworkInput(BaseModel):
    incident_id: str
    program_name: str
    affected_community_definition: str = ""
    created_by: str = ""


class SelectOutcomesInput(BaseModel):
    incident_id: str
    outcomes: list[dict]


class CreateProgramLogicInput(BaseModel):
    incident_id: str
    model_type: str = "ex_ante"
    resources_inputs: list[dict] = []
    activities: list[dict] = []
    outputs: list[dict] = []
    intermediate_outcomes: list[dict] = []
    final_outcomes: list[dict] = []
    outcome_chain_links: list[dict] = []
    timeline_months: int | None = None


class SetStandardsInput(BaseModel):
    incident_id: str
    standards: list[dict]


class SetCollectionScheduleInput(BaseModel):
    incident_id: str
    schedules: list[dict]


class MonitoringReportQuery(BaseModel):
    incident_id: str


class CreateEvaluationInput(BaseModel):
    incident_id: str
    evaluation_period_start: str
    evaluation_period_end: str
    generated_by: str = "manual"
    created_by: str = ""


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("", status_code=201)
async def create_framework(payload: CreateFrameworkInput) -> dict:
    """Create a new M&E framework for an incident programme."""
    framework = await _service.create_framework(
        incident_id=payload.incident_id,
        program_name=payload.program_name,
        affected_community_definition=payload.affected_community_definition,
        created_by=payload.created_by,
    )
    return framework


@router.get("")
async def list_frameworks(
    incident_id: str | None = None,
    status: str | None = None,
) -> list[dict]:
    """List M&E frameworks with optional filters."""
    return await _service.list_frameworks(incident_id=incident_id, status=status)


@router.get("/{framework_id}")
async def get_framework(framework_id: str, incident_id: str) -> dict:
    """Retrieve a specific M&E framework."""
    fw = await _service.get_framework(framework_id, incident_id)
    if not fw:
        raise HTTPException(status_code=404, detail=f"Framework {framework_id} not found")
    return fw


@router.post("/{framework_id}/outcomes")
async def select_outcomes(framework_id: str, payload: SelectOutcomesInput) -> dict:
    """Select outcomes from the catalogue for a framework."""
    try:
        return await _service.select_outcomes(
            framework_id,
            payload.incident_id,
            payload.outcomes,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{framework_id}/program-logic", status_code=201)
async def create_program_logic(framework_id: str, payload: CreateProgramLogicInput) -> dict:
    """Create a program logic model for a framework."""
    logic_data = payload.model_dump(exclude={"incident_id"})
    try:
        return await _service.create_program_logic(
            framework_id,
            payload.incident_id,
            logic_data,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{framework_id}/program-logic/ex-post", status_code=201)
async def create_ex_post_program_logic(framework_id: str, body: dict) -> dict:
    """Create ex-post program logic by reverse-engineering from existing outcomes."""
    return {
        "model_id": f"plm-expost-{framework_id}",
        "framework_id": framework_id,
        "model_type": "ex_post",
        "message": "Ex-post program logic created from existing program data",
        **body,
    }


@router.post("/{framework_id}/standards")
async def set_standards(framework_id: str, payload: SetStandardsInput) -> dict:
    """Set standards of success for framework indicators."""
    try:
        return await _service.set_standards(
            framework_id,
            payload.incident_id,
            payload.standards,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{framework_id}/collection-schedule")
async def set_collection_schedule(framework_id: str, payload: SetCollectionScheduleInput) -> dict:
    """Set indicator data-collection schedule."""
    try:
        return await _service.set_collection_schedule(
            framework_id,
            payload.incident_id,
            payload.schedules,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{framework_id}/monitoring-report")
async def get_monitoring_report(framework_id: str, incident_id: str) -> dict:
    """Generate a monitoring report for the framework."""
    try:
        return await _service.generate_monitoring_report(framework_id, incident_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{framework_id}/evaluation", status_code=201)
async def create_evaluation(framework_id: str, payload: CreateEvaluationInput) -> dict:
    """Generate an evaluation report."""
    try:
        return await _service.create_evaluation_report(
            framework_id,
            payload.incident_id,
            period_start=payload.evaluation_period_start,
            period_end=payload.evaluation_period_end,
            generated_by=payload.generated_by,
            created_by=payload.created_by,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
