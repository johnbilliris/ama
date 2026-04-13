"""M&E Framework — Monitoring and Evaluation Framework for disaster recovery programs.

Covers outcome selection, program logic linking, success standards,
collection schedules, and evaluation domain tracking per AIDR M&E Framework v2.

FRs: FR-008–014 | Research: R-005, R-009
"""

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator

EvaluationDomain = Literal[
    "governance", "community_engagement", "effectiveness",
    "efficiency", "implementation",
]
RecoveryDomain = Literal["overarching", "social", "economic", "built", "natural"]
ObjectiveType = Literal["sustainability", "resilience"]

ALL_EVALUATION_DOMAINS: list[str] = [
    "governance", "community_engagement", "effectiveness",
    "efficiency", "implementation",
]


class SelectedOutcome(BaseModel):
    """An AIDR catalogue outcome selected for this M&E framework."""
    catalogue_outcome_id: str
    domain: RecoveryDomain
    objective_type: ObjectiveType
    community_restatement: str | None = None
    is_active: bool = True


class SuccessStandard(BaseModel):
    """Threshold for measuring success against a selected outcome's indicator."""
    catalogue_outcome_id: str
    indicator_id: str
    threshold_value: float
    threshold_operator: Literal["gte", "lte", "eq", "between"] = "gte"
    threshold_upper: float | None = None
    stakeholder_label: str = "primary"
    notes: str = ""

    @model_validator(mode="after")
    def _validate_between(self) -> "SuccessStandard":
        if self.threshold_operator == "between" and self.threshold_upper is None:
            raise ValueError("threshold_upper required when threshold_operator is 'between'")
        return self


class CollectionSchedule(BaseModel):
    """Data collection schedule for an indicator."""
    indicator_id: str
    frequency: Literal["weekly", "fortnightly", "monthly", "quarterly", "annually"]
    next_due_date: datetime
    last_collected_at: datetime | None = None
    is_overdue: bool = False


class MEFramework(BaseModel):
    """Monitoring & Evaluation Framework for a disaster recovery program.

    FRs: FR-008–014 | Research: R-005, R-009
    """
    framework_id: str
    incident_id: str
    program_name: str
    affected_community_definition: str = ""
    selected_outcomes: list[SelectedOutcome] = Field(default_factory=list)
    program_logic_id: str | None = None
    active_evaluation_domains: list[EvaluationDomain] = Field(
        default_factory=lambda: list(ALL_EVALUATION_DOMAINS)
    )
    standards_of_success: list[SuccessStandard] = Field(default_factory=list)
    indicator_collection_schedule: list[CollectionSchedule] = Field(default_factory=list)
    evaluation_reports: list[str] = Field(default_factory=list)
    status: Literal["configuring", "active", "evaluation_complete", "closed"] = "configuring"
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    created_by: str = ""
    updated_at: datetime | None = None

    @model_validator(mode="after")
    def _validate_framework(self) -> "MEFramework":
        for domain in self.active_evaluation_domains:
            if domain not in ALL_EVALUATION_DOMAINS:
                raise ValueError(f"Invalid evaluation domain: '{domain}'")
        return self
