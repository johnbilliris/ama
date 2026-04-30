"""Emergency plan lifecycle state machine with role-based authorization.

7-state lifecycle: Draft → In Consultation → Under Review → Endorsed →
Activated → Post-Event Review → Superseded.

Follows common/pprr_lifecycle.py pattern.

FRs: FR-006 | Research: R-002
"""

VALID_PLAN_TRANSITIONS: dict[str, list[str]] = {
    "draft": ["in_consultation"],
    "in_consultation": ["under_review", "draft"],
    "under_review": ["endorsed", "draft"],
    "endorsed": ["activated", "superseded"],
    "activated": ["post_event_review"],
    "post_event_review": ["draft"],  # Creates new version; original → superseded
    "superseded": [],  # Terminal state
}

TRANSITION_ROLES: dict[tuple[str, str], str] = {
    ("draft", "in_consultation"): "planning_officer",
    ("in_consultation", "under_review"): "planning_officer",
    ("in_consultation", "draft"): "planning_officer",
    ("under_review", "endorsed"): "designated_authority",
    ("under_review", "draft"): "designated_authority",
    ("endorsed", "activated"): "incident_controller",
    ("activated", "post_event_review"): "incident_controller_or_planning_officer",
    ("post_event_review", "draft"): "planning_officer",
}

ALL_LIFECYCLE_STATES: list[str] = [
    "draft",
    "in_consultation",
    "under_review",
    "endorsed",
    "activated",
    "post_event_review",
    "superseded",
]


def validate_plan_transition(
    current_state: str,
    target_state: str,
    user_role: str,
) -> tuple[bool, str]:
    """Validate whether a plan lifecycle transition is allowed.

    Checks both the transition validity and the user's role authorization.

    Returns:
        Tuple of (is_valid, error_message_or_empty).
    """
    valid_targets = VALID_PLAN_TRANSITIONS.get(current_state, [])
    if target_state not in valid_targets:
        return False, (f"Invalid plan transition: '{current_state}' → '{target_state}'. Valid targets: {valid_targets}")
    required_role = TRANSITION_ROLES.get((current_state, target_state))
    if required_role:
        allowed_roles = required_role.split("_or_")
        if user_role not in allowed_roles:
            return False, (
                f"Role '{user_role}' cannot perform '{current_state}' → '{target_state}'. Required: {required_role}"
            )
    return True, ""


def is_terminal_state(state: str) -> bool:
    """Check if a lifecycle state is terminal (no further transitions)."""
    return len(VALID_PLAN_TRANSITIONS.get(state, [])) == 0


def is_editable_state(state: str) -> bool:
    """Check if a plan can be edited in the given state."""
    return state in ("draft", "in_consultation")
