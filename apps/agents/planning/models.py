"""Request and response models for Planning Agent endpoints.

FRs: FR-001–007 | Research: R-002
"""

from typing import Literal, NotRequired, TypedDict

from pydantic import BaseModel


class PlanSection(TypedDict, total=False):
    section_slug: str
    title: str
    content: str
    is_complete: bool
    last_edited_at: str | None
    last_edited_by: str | None


class ProcessStep(TypedDict, total=False):
    step_number: int
    step_name: str
    is_complete: bool
    completed_at: str | None
    completed_by: str | None
    notes: str


class PlanActivationRecord(TypedDict):
    incident_id: str
    activated_at: str
    activated_by: str
    deactivated_at: str | None
    deactivation_reason: str | None


class PlanDocument(TypedDict):
    plan_id: str
    title: str
    region_id: str
    hazard_types: list[str]
    hierarchy_level: str
    parent_plan_id: str | None
    lifecycle_state: str
    version: int
    security_rating: str
    authority: str
    created_by: str
    created_at: str
    updated_at: str | None
    plan_sections: dict[str, PlanSection]
    planning_principles_checklist: dict[str, bool]
    process_steps: dict[int, ProcessStep]
    activation_records: NotRequired[list[PlanActivationRecord]]


class PlanSummary(TypedDict):
    plan_id: str
    title: str
    region_id: str
    lifecycle_state: str
    hierarchy_level: str
    version: int
    hazard_types: list[str]
    created_at: str
    updated_at: str | None


class PlanTransitionResult(TypedDict):
    plan_id: str
    previous_state: str
    new_state: str
    transitioned_by: str


class PlanHierarchy(TypedDict):
    region_id: str
    plans: list[PlanSummary]


class PlanCompleteness(TypedDict):
    section_completeness: float
    principles_completeness: float
    total_sections: int
    completed_sections: int
    total_principles: int
    checked_principles: int
    missing_sections: list[str]
    unchecked_principles: list[str]
    plan_id: NotRequired[str]


class PlanActivationPayload(TypedDict, total=False):
    plan_id: str
    activated_by: str


class PlanActivationHandoff(TypedDict):
    payload: PlanActivationPayload


class PlanActivationHandoffResult(TypedDict):
    status: str
    plan_id: str | None
    activated_by: str


class CreatePlanRequest(BaseModel):
    title: str
    region_id: str
    hazard_types: list[str]
    hierarchy_level: Literal["national", "state", "regional", "local"] = "local"
    parent_plan_id: str | None = None
    security_rating: Literal["unclassified", "official", "official_sensitive", "protected"] = "official"
    authority: str = ""
    created_by: str = ""


class PlanSummaryResponse(BaseModel):
    plan_id: str
    title: str
    region_id: str
    lifecycle_state: str
    hierarchy_level: str
    version: int
    hazard_types: list[str]
    created_at: str
    updated_at: str | None = None


class PlanTransitionRequest(BaseModel):
    target_state: str
    user_role: str
    reason: str = ""


class PlanTransitionResponse(BaseModel):
    plan_id: str
    previous_state: str
    new_state: str
    transitioned_by: str


class PlanActivationRequest(BaseModel):
    incident_id: str
    activated_by: str


class PlanActivationResponse(BaseModel):
    plan_id: str
    incident_id: str
    activated_at: str
    response_arrangements: dict[str, object] | None = None


class PlanCompletenessResponse(BaseModel):
    plan_id: str
    section_completeness: float
    principles_completeness: float
    total_sections: int
    completed_sections: int
    total_principles: int
    checked_principles: int
    missing_sections: list[str]
    unchecked_principles: list[str]


class UpdateSectionRequest(BaseModel):
    title: str = ""
    content: str = ""


class UpdateStepRequest(BaseModel):
    is_complete: bool = False
    notes: str = ""
    completed_by: str = ""


class PlanHierarchyResponse(BaseModel):
    region_id: str
    plans: list[PlanSummaryResponse]
