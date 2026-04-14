"""Evacuation stage state machine logic.

Validates transitions, detects re-entry, and manages stage lifecycle
for the five-stage evacuation model.

FRs: FR-018–FR-025 | Research: R-010
"""

from datetime import UTC, datetime
from uuid import uuid4

from packages.domain.src.domain.models.evacuation_stage import (
    RE_ENTRY_TRANSITIONS,
    VALID_TRANSITIONS,
    EvacStageName,
    EvacuationStage,
)


def validate_transition(current: str, target: str) -> tuple[bool, str]:
    """Validate whether an evacuation stage transition is allowed.

    Returns:
        Tuple of (is_valid, error_message_or_empty).
    """
    valid_targets = VALID_TRANSITIONS.get(current, [])
    if target in valid_targets:
        return True, ""
    return False, (
        f"Invalid evacuation transition: '{current}' → '{target}'. "
        f"Valid targets: {valid_targets}"
    )


def is_re_entry(current: str, target: str) -> bool:
    """Check if the transition constitutes a re-entry (reversal to decision)."""
    return (current, target) in RE_ENTRY_TRANSITIONS


def transition_stage(
    stage: EvacuationStage,
    target: EvacStageName,
    *,
    authorized_by: str,
    rationale: str,
    shelter_in_place_rationale: str | None = None,
) -> EvacuationStage:
    """Advance an evacuation stage to a new state.

    Raises ValueError if the transition is invalid.
    """
    valid, error = validate_transition(stage.current_stage, target)
    if not valid:
        raise ValueError(error)

    now = datetime.now(UTC)
    re_entry = is_re_entry(stage.current_stage, target)

    updates: dict = {
        "previous_stage": stage.current_stage,
        "current_stage": target,
        "stage_started_at": now,
        "stage_ended_at": None,
        "authorized_by": authorized_by,
        "transition_rationale": rationale,
    }

    if re_entry:
        updates["re_entry_count"] = stage.re_entry_count + 1

    if target == "shelter_in_place":
        updates["shelter_in_place_rationale"] = shelter_in_place_rationale or rationale

    return stage.model_copy(update=updates)


def build_stage_transition_payload(
    *,
    stage_id: str,
    incident_id: str,
    source_stage: str,
    target_stage: str,
    authorized_by: str,
    rationale: str,
    is_re_entry_transition: bool = False,
) -> dict[str, object]:
    """Build a TimelineEvent payload for an evacuation stage transition."""
    return {
        "action": "evacuation_stage_transition",
        "stage_id": stage_id,
        "incident_id": incident_id,
        "source_stage": source_stage,
        "target_stage": target_stage,
        "authorized_by": authorized_by,
        "rationale": rationale,
        "is_re_entry": is_re_entry_transition,
    }


def create_initial_stage(
    incident_id: str,
    plan_id: str,
    decision_authority: str,
    decision_rationale: str,
    *,
    evacuation_type: str | None = None,
    evacuation_approach: str | None = None,
    evacuation_scope: str | None = None,
) -> EvacuationStage:
    """Create a new evacuation stage starting at the Decision phase."""
    return EvacuationStage(
        stage_id=str(uuid4()),
        incident_id=incident_id,
        evacuation_plan_id=plan_id,
        current_stage="decision",
        decision_authority=decision_authority,
        decision_rationale=decision_rationale,
        evacuation_type=evacuation_type,  # type: ignore[arg-type]
        evacuation_approach=evacuation_approach,  # type: ignore[arg-type]
        evacuation_scope=evacuation_scope,  # type: ignore[arg-type]
    )
