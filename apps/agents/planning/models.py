"""Request and response models for Planning Agent endpoints.

FRs: FR-001–007 | Research: R-002
"""
from typing import Literal

from pydantic import BaseModel


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
    response_arrangements: dict | None = None


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
