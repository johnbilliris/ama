"""Emergency Plan — AIDR-compliant emergency planning with 7-state lifecycle.

27 plan sections per Emergency Planning Handbook Chapter 3.
Eight planning principles validation (FR-004).

FRs: FR-001–007, FR-007a | Research: R-002, R-003, R-008
"""

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator

PlanLifecycleState = Literal[
    "draft",
    "in_consultation",
    "under_review",
    "endorsed",
    "activated",
    "post_event_review",
    "superseded",
]
PlanHierarchyLevel = Literal["national", "state", "regional", "local"]
SecurityRating = Literal["unclassified", "official", "official_sensitive", "protected"]

PLAN_SECTION_SLUGS: list[str] = [
    "contents_glossary",
    "authority",
    "security_rating",
    "review_schedule",
    "amendment_register",
    "distribution_list",
    "aim_objectives",
    "legislative_context",
    "plan_context",
    "plan_scope",
    "leadership_structures",
    "roles_responsibilities",
    "financial_management",
    "communication_systems",
    "information_management",
    "resource_capability",
    "prevention_mitigation",
    "preparedness",
    "public_education",
    "plan_scheduling_activation",
    "response_arrangements",
    "emergency_control_facilities",
    "public_information_warnings",
    "evacuation_management",
    "relief_arrangements",
    "recovery_arrangements",
    "exercise_schedule",
]

PLANNING_PRINCIPLES: list[str] = [
    "risk_informed",
    "reducing_unknowns",
    "collaborative_inclusive",
    "strategic",
    "solutions_oriented",
    "iterative",
    "adaptive_capacity",
    "shared_responsibility",
]


class PlanSection(BaseModel):
    """A single section within an emergency plan (27 total per AIDR)."""

    section_slug: str
    title: str
    content: str = ""
    is_complete: bool = False
    last_edited_at: datetime | None = None
    last_edited_by: str | None = None


class PlanActivationRecord(BaseModel):
    """Record of a plan being activated during an incident."""

    incident_id: str
    activated_at: datetime
    activated_by: str
    deactivated_at: datetime | None = None
    deactivation_reason: str | None = None


class PlanAmendment(BaseModel):
    """Version history and change record for a plan amendment."""

    amendment_number: int
    description: str
    amended_by: str
    amended_at: datetime
    sections_affected: list[str] = Field(default_factory=list)


class EmergencyPlan(BaseModel):
    """Emergency Plan with 7-state lifecycle and 27 AIDR plan sections.

    FRs: FR-001–007, FR-007a | Research: R-002, R-003, R-008
    """

    plan_id: str
    title: str
    region_id: str
    hazard_types: list[str] = Field(default_factory=list)
    hierarchy_level: PlanHierarchyLevel = "local"
    parent_plan_id: str | None = None
    lifecycle_state: PlanLifecycleState = "draft"
    version: int = 1
    security_rating: SecurityRating = "official"
    authority: str = ""
    endorsed_by: str | None = None
    endorsed_at: datetime | None = None
    next_review_date: datetime | None = None
    last_exercise_date: datetime | None = None
    plan_sections: dict[str, PlanSection] = Field(default_factory=dict)
    planning_principles_checklist: dict[str, bool] = Field(default_factory=dict)
    activation_records: list[PlanActivationRecord] = Field(default_factory=list)
    amendment_register: list[PlanAmendment] = Field(default_factory=list)
    distribution_list: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    created_by: str = ""
    updated_at: datetime | None = None

    @model_validator(mode="after")
    def _validate_plan(self) -> "EmergencyPlan":
        # Endorsed+ states require endorsement info
        if self.lifecycle_state in ("endorsed", "activated", "post_event_review"):
            if not self.endorsed_by:
                raise ValueError("endorsed_by required for endorsed+ states")
            if not self.endorsed_at:
                raise ValueError("endorsed_at required for endorsed+ states")
        # Hazard types must be non-empty
        if not self.hazard_types:
            raise ValueError("hazard_types must be non-empty")
        # Planning principles checklist keys must be valid
        for key in self.planning_principles_checklist:
            if key not in PLANNING_PRINCIPLES:
                raise ValueError(f"Invalid planning principle key: '{key}'. Must be one of {PLANNING_PRINCIPLES}")
        return self
