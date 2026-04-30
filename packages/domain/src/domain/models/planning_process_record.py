"""Planning Process Record — 9-step AIDR emergency planning process tracker.

Tracks completion of each step in the AIDR planning process alongside
team membership, stakeholder engagement, and endorsement approvals.

FRs: FR-001 | Research: R-001
"""

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator

PLANNING_STEPS: dict[int, str] = {
    1: "Establish project plan",
    2: "Establish project team",
    3: "Communicate and consult",
    4: "Understand risks and consequences",
    5: "Develop strategies and arrangements",
    6: "Document and trial",
    7: "Endorse the plan",
    8: "Implement and exercise",
    9: "Monitor and review",
}

EngagementMethod = Literal[
    "workshop",
    "survey",
    "interview",
    "public_meeting",
    "written_submission",
    "other",
]


class StepCompletion(BaseModel):
    """Completion status for a single planning process step."""

    step_number: int
    step_name: str
    is_complete: bool = False
    completed_at: datetime | None = None
    completed_by: str | None = None
    notes: str = ""

    @model_validator(mode="after")
    def _validate_step(self) -> "StepCompletion":
        if self.step_number < 1 or self.step_number > 9:
            raise ValueError(f"step_number must be 1–9, got {self.step_number}")
        if self.is_complete and not self.completed_at:
            raise ValueError("completed_at required when is_complete is True")
        return self


class TeamMember(BaseModel):
    """A member of the planning project team."""

    name: str
    role: str
    organisation: str
    joined_at: datetime


class EngagementEntry(BaseModel):
    """Record of stakeholder engagement during the planning process."""

    stakeholder: str
    method: EngagementMethod
    date: datetime
    summary: str
    attendee_count: int | None = None


class EndorsementApproval(BaseModel):
    """Record of endorsement approval by a designated authority."""

    authority_name: str
    authority_role: str
    approved: bool
    approved_at: datetime | None = None
    comments: str = ""


class PlanningProcessRecord(BaseModel):
    """9-step AIDR emergency planning process tracker.

    FRs: FR-001 | Research: R-001
    """

    record_id: str
    plan_id: str
    current_step: int = 1
    step_status: dict[int, StepCompletion] = Field(default_factory=dict)
    project_team: list[TeamMember] = Field(default_factory=list)
    stakeholder_engagement_log: list[EngagementEntry] = Field(default_factory=list)
    risk_assessment_id: str | None = None
    endorsement_approvals: list[EndorsementApproval] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime | None = None

    @model_validator(mode="after")
    def _validate_record(self) -> "PlanningProcessRecord":
        if self.current_step < 1 or self.current_step > 9:
            raise ValueError(f"current_step must be 1–9, got {self.current_step}")
        for key in self.step_status:
            if key < 1 or key > 9:
                raise ValueError(f"step_status key must be 1–9, got {key}")
        return self
