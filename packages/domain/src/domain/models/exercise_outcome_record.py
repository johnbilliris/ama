"""Exercise outcome record — per data-model.md §5 (feature 036, FR-054/FR-055).

AIDR-compatible post-exercise lessons-capture record. Persisted to Blob WORM
(7-yr immutability) by the lessons-capture pipeline; an index doc mirrors
this in Cosmos ``exercise_outcome_index`` partitioned by ``simulation_id``.
"""

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, NonNegativeInt

EndReason = Literal["completed", "aborted", "timeout"]


class ParticipantSummary(BaseModel):
    """Aggregate participant counts for the exercise."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    coordinators: NonNegativeInt = 0
    sub_agents_invoked: NonNegativeInt = 0
    cascade_threads: NonNegativeInt = 0
    injections_attempted: NonNegativeInt = 0
    injections_accepted: NonNegativeInt = 0


class ObjectiveOutcome(BaseModel):
    """Per-objective outcome row in the AIDR roll-up."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    objective_id: str
    objective_text: str
    achieved: bool
    evidence_audit_ids: list[str] = Field(default_factory=list)
    notes: str | None = None


class Lesson(BaseModel):
    """One lesson identified during after-action review (AIDR §3)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    lesson_id: str
    summary: str = Field(max_length=2000)
    category: Literal["safety", "command", "comms", "logistics", "process", "tech"]
    severity: Literal["minor", "moderate", "major", "critical"]
    recommendation: str | None = None


class Attachment(BaseModel):
    """Blob URI attachment (e.g. transcript, map snapshot)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    blob_uri: str
    media_type: str
    description: str | None = None


class ExerciseOutcomeRecord(BaseModel):
    """AIDR-compatible exercise outcome (FR-054)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    record_id: str = Field(description="Equals simulation_id for idempotency (FR-055).")
    simulation_id: str
    tenant_id: str
    start_at: datetime
    end_at: datetime
    end_reason: EndReason
    participant_summary: ParticipantSummary
    objective_outcomes: list[ObjectiveOutcome] = Field(default_factory=list)
    lessons: list[Lesson] = Field(default_factory=list)
    attachments: list[Attachment] = Field(default_factory=list)
    aidr_version: str = "v2.1"
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    document_type: Literal["exercise_outcome_record"] = "exercise_outcome_record"

    @property
    def partition_key(self) -> str:
        return self.simulation_id
