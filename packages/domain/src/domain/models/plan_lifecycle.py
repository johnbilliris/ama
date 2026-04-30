"""Plan Lifecycle — state machine for EmergencyPlan 7-state lifecycle.

Governs valid transitions between plan states with role-based authorization.
Terminal state: superseded.  Editable states: draft, in_consultation.

FRs: FR-005, FR-006, FR-007 | Research: R-002
"""

from typing import Literal

PlanLifecycleState = Literal[
    "draft",
    "in_consultation",
    "under_review",
    "endorsed",
    "activated",
    "post_event_review",
    "superseded",
]

# Valid transitions: source → list[target]
VALID_PLAN_TRANSITIONS: dict[str, list[str]] = {
    "draft": ["in_consultation"],
    "in_consultation": ["under_review", "draft"],
    "under_review": ["endorsed", "draft"],
    "endorsed": ["activated", "superseded"],
    "activated": ["post_event_review", "superseded"],
    "post_event_review": ["endorsed", "superseded"],
    "superseded": [],
}

# Role required to perform each (source, target) transition
TRANSITION_ROLE_REQUIREMENTS: dict[tuple[str, str], str] = {
    ("draft", "in_consultation"): "plan_author",
    ("in_consultation", "under_review"): "plan_author",
    ("in_consultation", "draft"): "plan_author",
    ("under_review", "endorsed"): "endorsing_authority",
    ("under_review", "draft"): "endorsing_authority",
    ("endorsed", "activated"): "incident_controller",
    ("endorsed", "superseded"): "plan_author",
    ("activated", "post_event_review"): "incident_controller",
    ("activated", "superseded"): "incident_controller",
    ("post_event_review", "endorsed"): "endorsing_authority",
    ("post_event_review", "superseded"): "plan_author",
}

TERMINAL_STATES: set[str] = {"superseded"}
EDITABLE_STATES: set[str] = {"draft", "in_consultation"}


def is_terminal_state(state: str) -> bool:
    """Return True if the given plan lifecycle state is terminal (no further transitions)."""
    return state in TERMINAL_STATES


def is_editable_state(state: str) -> bool:
    """Return True if the plan can be edited in this state."""
    return state in EDITABLE_STATES


def validate_plan_transition(
    current_state: str,
    target_state: str,
    user_role: str | None = None,
) -> tuple[bool, str]:
    """Validate whether a plan lifecycle transition is allowed.

    Args:
        current_state: Current lifecycle state of the plan.
        target_state: Desired target state.
        user_role: Role of the user requesting the transition (optional).

    Returns:
        Tuple of (is_valid, error_message_or_empty).
    """
    valid_targets = VALID_PLAN_TRANSITIONS.get(current_state)
    if valid_targets is None:
        return False, f"Unknown plan lifecycle state: '{current_state}'"
    if target_state not in valid_targets:
        return False, (f"Invalid plan transition: '{current_state}' → '{target_state}'. Valid targets: {valid_targets}")
    # Check role authorization if a user_role was provided
    if user_role is not None:
        required_role = TRANSITION_ROLE_REQUIREMENTS.get((current_state, target_state))
        if required_role and user_role != required_role:
            return False, (
                f"Role '{user_role}' not authorized for transition "
                f"'{current_state}' → '{target_state}'. Requires '{required_role}'"
            )
    return True, ""
