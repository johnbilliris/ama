"""Evacuation stage management API routes.

Provides endpoints for initialising evacuation stages, advancing
through the state machine, and updating stage-specific progress fields.

FRs: FR-018–FR-025
"""

from uuid import uuid4

from app.services.state_store import (
    EVACUATION_STAGES,
    INCIDENTS,
    TIMELINE_EVENTS,
)
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from apps.agents.evacuation.stages import (
    build_stage_transition_payload,
    create_initial_stage,
    transition_stage,
)
from packages.domain.src.domain.models.timeline_event import TimelineEvent

router = APIRouter(
    prefix="/incidents/{incident_id}/evacuation",
    tags=["evacuation"],
)


# --- Request models ---


class CreateStageInput(BaseModel):
    plan_id: str
    decision_authority: str
    decision_rationale: str
    evacuation_type: str | None = None
    evacuation_approach: str | None = None
    evacuation_scope: str | None = None


class TransitionInput(BaseModel):
    target_stage: str
    authorized_by: str
    rationale: str
    shelter_in_place_rationale: str | None = None


class WithdrawalUpdateInput(BaseModel):
    population_moved: int | None = None
    vulnerable_status: dict[str, str] | None = None


class ShelterUpdateInput(BaseModel):
    occupancy: int | None = None
    capacity: int | None = None


class ReturnUpdateInput(BaseModel):
    safety_conditions_met: bool | None = None
    certifier: str | None = None
    rate: float | None = None


# --- Helpers ---


def _require_incident(incident_id: str) -> None:
    if incident_id not in INCIDENTS:
        raise HTTPException(status_code=404, detail="Incident not found")


def _require_stage(stage_id: str) -> None:
    if stage_id not in EVACUATION_STAGES:
        raise HTTPException(status_code=404, detail="Evacuation stage not found")


# --- Routes ---


@router.post("/stages")
async def create_stage(
    incident_id: str,
    payload: CreateStageInput,
) -> dict[str, object]:
    _require_incident(incident_id)
    stage = create_initial_stage(
        incident_id=incident_id,
        plan_id=payload.plan_id,
        decision_authority=payload.decision_authority,
        decision_rationale=payload.decision_rationale,
        evacuation_type=payload.evacuation_type,
        evacuation_approach=payload.evacuation_approach,
        evacuation_scope=payload.evacuation_scope,
    )
    EVACUATION_STAGES[stage.stage_id] = stage
    return stage.model_dump(mode="json")


@router.post("/stages/{stage_id}/transition")
async def transition(
    incident_id: str,
    stage_id: str,
    payload: TransitionInput,
) -> dict[str, object]:
    _require_incident(incident_id)
    _require_stage(stage_id)
    stage = EVACUATION_STAGES[stage_id]

    try:
        updated = transition_stage(
            stage,
            payload.target_stage,  # type: ignore[arg-type]
            authorized_by=payload.authorized_by,
            rationale=payload.rationale,
            shelter_in_place_rationale=payload.shelter_in_place_rationale,
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    EVACUATION_STAGES[stage_id] = updated

    # Record timeline event
    from apps.agents.evacuation.stages import is_re_entry

    event_payload = build_stage_transition_payload(
        stage_id=stage_id,
        incident_id=incident_id,
        source_stage=stage.current_stage,
        target_stage=payload.target_stage,
        authorized_by=payload.authorized_by,
        rationale=payload.rationale,
        is_re_entry_transition=is_re_entry(
            stage.current_stage,
            payload.target_stage,
        ),
    )
    event = TimelineEvent(
        event_id=str(uuid4()),
        incident_id=incident_id,
        event_type="system",
        summary=(f"Evacuation stage transitioned from '{stage.current_stage}' to '{payload.target_stage}'"),
        actor=payload.authorized_by,
        payload=event_payload,
    )
    TIMELINE_EVENTS.setdefault(incident_id, []).append(event)

    return updated.model_dump(mode="json")


@router.get("/stages/{stage_id}")
async def get_stage(incident_id: str, stage_id: str) -> dict[str, object]:
    _require_incident(incident_id)
    _require_stage(stage_id)
    return EVACUATION_STAGES[stage_id].model_dump(mode="json")


@router.put("/stages/{stage_id}/withdrawal")
async def update_withdrawal(
    incident_id: str,
    stage_id: str,
    payload: WithdrawalUpdateInput,
) -> dict[str, object]:
    _require_incident(incident_id)
    _require_stage(stage_id)
    stage = EVACUATION_STAGES[stage_id]
    updates: dict = {}
    if payload.population_moved is not None:
        updates["population_moved"] = payload.population_moved
    if payload.vulnerable_status is not None:
        updates["vulnerable_population_status"] = payload.vulnerable_status
    EVACUATION_STAGES[stage_id] = stage.model_copy(update=updates)
    return EVACUATION_STAGES[stage_id].model_dump(mode="json")


@router.put("/stages/{stage_id}/shelter")
async def update_shelter(
    incident_id: str,
    stage_id: str,
    payload: ShelterUpdateInput,
) -> dict[str, object]:
    _require_incident(incident_id)
    _require_stage(stage_id)
    stage = EVACUATION_STAGES[stage_id]
    updates: dict = {}
    if payload.occupancy is not None:
        updates["current_shelter_occupancy"] = payload.occupancy
    if payload.capacity is not None:
        updates["total_shelter_capacity"] = payload.capacity
    EVACUATION_STAGES[stage_id] = stage.model_copy(update=updates)
    return EVACUATION_STAGES[stage_id].model_dump(mode="json")


@router.put("/stages/{stage_id}/return")
async def update_return(
    incident_id: str,
    stage_id: str,
    payload: ReturnUpdateInput,
) -> dict[str, object]:
    _require_incident(incident_id)
    _require_stage(stage_id)
    stage = EVACUATION_STAGES[stage_id]
    updates: dict = {}
    if payload.safety_conditions_met is not None:
        updates["safety_conditions_met"] = payload.safety_conditions_met
    if payload.certifier is not None:
        updates["safety_certifier"] = payload.certifier
    if payload.rate is not None:
        updates["return_completion_rate"] = payload.rate
    EVACUATION_STAGES[stage_id] = stage.model_copy(update=updates)
    return EVACUATION_STAGES[stage_id].model_dump(mode="json")
