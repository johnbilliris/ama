"""Lesson model — lessons management with AIIMS/PPRR categorisation.

Supports auto-triggered lessons capture for Level 2+ incidents and exercises,
severity classification, assignment tracking, contradictory-lesson handling,
and PR quality gate verification.

FRs: FR-038–042, FR-052 | Research: R-007
"""

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator

LessonStatus = Literal["identified", "in_progress", "resolved", "rejected"]
LessonSeverity = Literal["low", "medium", "high", "critical"]


class Lesson(BaseModel):
    lesson_id: str
    incident_id: str | None = None
    scenario_run_id: str | None = None
    title: str
    description: str
    aiims_function: Literal[
        "control", "intelligence", "planning",
        "operations", "logistics", "public_information",
    ] | None = None
    pprr_phase: Literal[
        "prevention", "preparedness", "response", "recovery",
    ] | None = None
    severity: LessonSeverity = "medium"
    status: LessonStatus = "identified"
    assigned_to: str | None = None
    target_resolution_date: datetime | None = None
    resolved_at: datetime | None = None
    resolution_reference: str | None = None
    resolution_notes: str = ""
    originating_event_id: str | None = None
    is_contradictory: bool = False
    contradicts_config_ref: str | None = None
    escalation_approved_by: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    created_by: str = ""
    tags: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _validate_lesson(self) -> "Lesson":
        if self.incident_id is None and self.scenario_run_id is None:
            msg = "At least one of incident_id or scenario_run_id must be set"
            raise ValueError(msg)
        if self.status == "resolved":
            if self.resolved_at is None:
                msg = "resolved_at is required when status is 'resolved'"
                raise ValueError(msg)
            if self.resolution_reference is None:
                msg = "resolution_reference is required when status is 'resolved'"
                raise ValueError(msg)
        if self.is_contradictory and self.status == "resolved":
            if not self.escalation_approved_by:
                msg = "escalation_approved_by is required for resolving contradictory lessons"
                raise ValueError(msg)
        return self
