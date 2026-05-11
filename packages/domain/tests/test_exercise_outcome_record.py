"""T-A05: ExerciseOutcomeRecord unit tests (FR-054/FR-055)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from domain.models.exercise_outcome_record import (
    ExerciseOutcomeRecord,
    Lesson,
    ParticipantSummary,
)
from pydantic import ValidationError


def _kwargs(**overrides: object) -> dict[str, object]:
    sid = str(uuid4())
    start = datetime.now(UTC)
    base: dict[str, object] = {
        "record_id": sid,  # FR-055 idempotency: equals simulation_id
        "simulation_id": sid,
        "tenant_id": "sim-tenant-a",
        "start_at": start,
        "end_at": start + timedelta(hours=2),
        "end_reason": "completed",
        "participant_summary": ParticipantSummary(
            coordinators=3,
            sub_agents_invoked=12,
            cascade_threads=4,
            injections_attempted=20,
            injections_accepted=18,
        ),
    }
    base.update(overrides)
    return base


def test_exercise_outcome_record_happy() -> None:
    rec = ExerciseOutcomeRecord(**_kwargs())
    assert rec.partition_key == rec.simulation_id
    assert rec.aidr_version == "v2.1"


def test_exercise_outcome_record_idempotency_record_id_equals_sim() -> None:
    rec = ExerciseOutcomeRecord(**_kwargs())
    assert rec.record_id == rec.simulation_id


def test_exercise_outcome_record_lessons_severity_constrained() -> None:
    with pytest.raises(ValidationError):
        Lesson(
            lesson_id=str(uuid4()),
            summary="oops",
            category="safety",
            severity="catastrophic",  # type: ignore[arg-type]
        )


def test_exercise_outcome_record_end_reason_constrained() -> None:
    with pytest.raises(ValidationError):
        ExerciseOutcomeRecord(**_kwargs(end_reason="vaporised"))
