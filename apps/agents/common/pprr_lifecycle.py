"""PPRR phase transition logic with managed transitions and overlap tracking.

Handles phase transitions for incidents and generates TimelineEvent payloads.
Supports overlap periods where multiple PPRR phases are active simultaneously.

FRs: FR-031, FR-053 | Research: R-001
"""

# Valid PPRR phase transitions
VALID_PPRR_TRANSITIONS: dict[str, list[str]] = {
    "prevention": ["preparedness"],
    "preparedness": ["response", "prevention"],
    "response": ["recovery"],
    "recovery": [],
}

# Phases that can run concurrently (FR-030, FR-035)
CONCURRENT_PHASE_PAIRS: set[tuple[str, str]] = {
    ("response", "recovery"),  # Recovery can begin during response
}


def validate_phase_transition(
    current_phase: str,
    target_phase: str,
) -> tuple[bool, str]:
    """Validate whether a PPRR phase transition is allowed.

    Returns:
        Tuple of (is_valid, error_message_or_empty).
    """
    valid_targets = VALID_PPRR_TRANSITIONS.get(current_phase, [])
    if target_phase in valid_targets:
        return True, ""
    return False, (f"Invalid PPRR transition: '{current_phase}' → '{target_phase}'. Valid targets: {valid_targets}")


def can_run_concurrently(phase_a: str, phase_b: str) -> bool:
    """Check if two PPRR phases can be active simultaneously."""
    return (phase_a, phase_b) in CONCURRENT_PHASE_PAIRS or (phase_b, phase_a) in CONCURRENT_PHASE_PAIRS


def build_phase_transition_payload(
    *,
    source_phase: str,
    target_phase: str,
    transition_rationale: str,
    authorising_user: str,
    overlap_active: bool = False,
    overlap_end_expected_at: str | None = None,
) -> dict[str, object]:
    """Build a TimelineEvent payload for a PPRR phase transition (FR-053)."""
    payload: dict[str, object] = {
        "action": "pprr_phase_transition",
        "source_phase": source_phase,
        "target_phase": target_phase,
        "transition_rationale": transition_rationale,
        "authorising_user": authorising_user,
        "overlap_active": overlap_active,
    }
    if overlap_end_expected_at:
        payload["overlap_end_expected_at"] = overlap_end_expected_at
    return payload


def build_incident_level_change_payload(
    *,
    previous_level: int,
    new_level: int,
    rationale: str,
    authorising_user: str,
) -> dict[str, object]:
    """Build a TimelineEvent payload for an incident level change."""
    return {
        "action": "incident_level_change",
        "previous_level": previous_level,
        "new_level": new_level,
        "rationale": rationale,
        "authorising_user": authorising_user,
    }


def build_lessons_capture_trigger_payload(
    *,
    trigger_source: str,
    incident_level: int,
    incident_id: str,
    scenario_run_id: str | None = None,
) -> dict[str, object]:
    """Build a TimelineEvent payload for lessons capture trigger (FR-038)."""
    return {
        "action": "lessons_capture_triggered",
        "trigger_source": trigger_source,
        "incident_level": incident_level,
        "incident_id": incident_id,
        "scenario_run_id": scenario_run_id,
    }
