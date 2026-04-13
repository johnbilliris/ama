"""Evacuation Stage model — five-stage evacuation lifecycle tracking.

Stages: Decision → Warning → Withdrawal → Shelter → Return → Completed.
Supports shelter-in-place, re-entry transitions, and audit fields.

FRs: FR-018–025 | Research: R-010
"""

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator

EvacStageName = Literal[
    "decision", "warning", "withdrawal", "shelter",
    "return", "shelter_in_place", "completed",
]

EvacuationType = Literal["pre_warned", "immediate"]
EvacuationApproach = Literal["directed", "recommended", "self_initiated"]
EvacuationScope = Literal["total", "partial", "phased"]

# Valid state transitions (R-010)
VALID_TRANSITIONS: dict[str, list[str]] = {
    "decision": ["warning", "shelter_in_place"],
    "warning": ["withdrawal", "decision"],
    "withdrawal": ["shelter", "decision"],
    "shelter": ["return", "decision"],
    "return": ["completed", "decision"],
    "shelter_in_place": ["decision"],
    "completed": [],
}

# Transitions that count as re-entry
RE_ENTRY_TRANSITIONS: set[tuple[str, str]] = {
    ("warning", "decision"),
    ("withdrawal", "decision"),
    ("shelter", "decision"),
    ("shelter_in_place", "decision"),
}


class EvacuationStage(BaseModel):
    stage_id: str
    incident_id: str
    evacuation_plan_id: str
    current_stage: EvacStageName
    previous_stage: EvacStageName | None = None
    stage_started_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    stage_ended_at: datetime | None = None
    re_entry_count: int = 0

    # Decision stage fields (FR-019)
    decision_authority: str | None = None
    decision_rationale: str | None = None
    evacuation_type: EvacuationType | None = None
    evacuation_approach: EvacuationApproach | None = None
    evacuation_scope: EvacuationScope | None = None

    # Warning stage fields (FR-020)
    warning_alert_ids: list[str] = Field(default_factory=list)
    evacuation_timeframe_minutes: int | None = None

    # Withdrawal stage fields (FR-021)
    population_total: int | None = None
    population_moved: int | None = None
    vulnerable_population_status: dict[str, str] = Field(default_factory=dict)

    # Shelter stage fields (FR-022)
    active_shelter_ids: list[str] = Field(default_factory=list)
    total_shelter_capacity: int | None = None
    current_shelter_occupancy: int | None = None

    # Return stage fields (FR-023)
    safety_conditions_met: bool = False
    safety_certifier: str | None = None
    return_completion_rate: float | None = None

    # Shelter-in-place fields (FR-024)
    shelter_in_place_rationale: str | None = None
    shelter_in_place_monitoring_interval_minutes: int | None = None

    # Audit
    authorized_by: str | None = None
    transition_rationale: str | None = None

    @model_validator(mode="after")
    def _validate_decision_fields(self) -> "EvacuationStage":
        if self.current_stage == "decision":
            if not self.decision_authority or not self.decision_rationale:
                msg = "decision_authority and decision_rationale are required for Decision stage"
                raise ValueError(msg)
        if self.current_stage == "shelter_in_place":
            if not self.shelter_in_place_rationale:
                msg = "shelter_in_place_rationale is required for Shelter-in-place stage"
                raise ValueError(msg)
        return self
