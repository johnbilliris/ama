"""Unit tests for plan lifecycle state machine.

Tests: valid transitions, invalid transitions, role authorization,
terminal states, editable states, incident_controller requirement.
"""

import pytest

from packages.domain.src.domain.models.plan_lifecycle import (
    EDITABLE_STATES,
    TERMINAL_STATES,
    TRANSITION_ROLE_REQUIREMENTS,
    VALID_PLAN_TRANSITIONS,
    is_editable_state,
    is_terminal_state,
    validate_plan_transition,
)


class TestValidPlanTransitions:
    """All valid transitions succeed."""

    @pytest.mark.parametrize(
        ("current", "target"),
        [
            ("draft", "in_consultation"),
            ("in_consultation", "under_review"),
            ("in_consultation", "draft"),
            ("under_review", "endorsed"),
            ("under_review", "draft"),
            ("endorsed", "activated"),
            ("endorsed", "superseded"),
            ("activated", "post_event_review"),
            ("activated", "superseded"),
            ("post_event_review", "endorsed"),
            ("post_event_review", "superseded"),
        ],
    )
    def test_valid_transition_accepted(self, current, target):
        valid, error = validate_plan_transition(current, target)
        assert valid is True
        assert error == ""

    def test_all_transitions_covered_in_role_requirements(self):
        """Every valid transition has a role requirement defined."""
        for source, targets in VALID_PLAN_TRANSITIONS.items():
            for target in targets:
                assert (source, target) in TRANSITION_ROLE_REQUIREMENTS, (
                    f"Missing role requirement for ({source}, {target})"
                )


class TestInvalidPlanTransitions:
    """Invalid transitions rejected."""

    @pytest.mark.parametrize(
        ("current", "target"),
        [
            ("draft", "endorsed"),
            ("draft", "activated"),
            ("draft", "superseded"),
            ("draft", "under_review"),
            ("draft", "post_event_review"),
            ("in_consultation", "endorsed"),
            ("in_consultation", "activated"),
            ("in_consultation", "superseded"),
            ("under_review", "activated"),
            ("under_review", "superseded"),
            ("under_review", "in_consultation"),
            ("endorsed", "draft"),
            ("endorsed", "in_consultation"),
            ("endorsed", "under_review"),
            ("endorsed", "post_event_review"),
            ("activated", "draft"),
            ("activated", "endorsed"),
            ("activated", "in_consultation"),
            ("post_event_review", "draft"),
            ("post_event_review", "activated"),
            ("post_event_review", "in_consultation"),
            ("superseded", "draft"),
            ("superseded", "endorsed"),
            ("superseded", "activated"),
        ],
    )
    def test_invalid_transition_rejected(self, current, target):
        valid, error = validate_plan_transition(current, target)
        assert valid is False
        assert "Invalid plan transition" in error

    def test_unknown_state_rejected(self):
        valid, error = validate_plan_transition("unknown_state", "draft")
        assert valid is False
        assert "Unknown plan lifecycle state" in error


class TestRoleAuthorization:
    """Role authorization enforced for each transition."""

    @pytest.mark.parametrize(
        ("current", "target", "required_role"),
        [
            ("draft", "in_consultation", "plan_author"),
            ("in_consultation", "under_review", "plan_author"),
            ("in_consultation", "draft", "plan_author"),
            ("under_review", "endorsed", "endorsing_authority"),
            ("under_review", "draft", "endorsing_authority"),
            ("endorsed", "activated", "incident_controller"),
            ("endorsed", "superseded", "plan_author"),
            ("activated", "post_event_review", "incident_controller"),
            ("activated", "superseded", "incident_controller"),
            ("post_event_review", "endorsed", "endorsing_authority"),
            ("post_event_review", "superseded", "plan_author"),
        ],
    )
    def test_correct_role_succeeds(self, current, target, required_role):
        valid, error = validate_plan_transition(current, target, user_role=required_role)
        assert valid is True
        assert error == ""

    @pytest.mark.parametrize(
        ("current", "target", "wrong_role"),
        [
            ("draft", "in_consultation", "incident_controller"),
            ("in_consultation", "under_review", "endorsing_authority"),
            ("under_review", "endorsed", "plan_author"),
            ("endorsed", "activated", "plan_author"),
            ("activated", "post_event_review", "plan_author"),
            ("post_event_review", "endorsed", "plan_author"),
        ],
    )
    def test_wrong_role_rejected(self, current, target, wrong_role):
        valid, error = validate_plan_transition(current, target, user_role=wrong_role)
        assert valid is False
        assert "not authorized" in error

    def test_no_role_provided_still_validates_transition(self):
        """When user_role is None, only transition validity is checked."""
        valid, error = validate_plan_transition("draft", "in_consultation", user_role=None)
        assert valid is True
        assert error == ""

    def test_no_role_invalid_transition_still_rejected(self):
        valid, error = validate_plan_transition("draft", "endorsed", user_role=None)
        assert valid is False


class TestActivatedRequiresIncidentController:
    """Activated state transitions require incident_controller role."""

    def test_endorsed_to_activated_requires_incident_controller(self):
        valid, error = validate_plan_transition("endorsed", "activated", user_role="plan_author")
        assert valid is False
        assert "incident_controller" in error

    def test_endorsed_to_activated_incident_controller_succeeds(self):
        valid, error = validate_plan_transition("endorsed", "activated", user_role="incident_controller")
        assert valid is True

    def test_activated_to_post_event_review_requires_incident_controller(self):
        valid, error = validate_plan_transition("activated", "post_event_review", user_role="plan_author")
        assert valid is False
        assert "incident_controller" in error

    def test_activated_to_superseded_requires_incident_controller(self):
        valid, error = validate_plan_transition("activated", "superseded", user_role="plan_author")
        assert valid is False
        assert "incident_controller" in error


class TestTerminalState:
    def test_superseded_is_terminal(self):
        assert is_terminal_state("superseded") is True

    def test_superseded_has_no_valid_transitions(self):
        assert VALID_PLAN_TRANSITIONS["superseded"] == []

    @pytest.mark.parametrize(
        "state",
        [
            "draft",
            "in_consultation",
            "under_review",
            "endorsed",
            "activated",
            "post_event_review",
        ],
    )
    def test_non_terminal_states(self, state):
        assert is_terminal_state(state) is False

    def test_terminal_states_set_has_only_superseded(self):
        assert TERMINAL_STATES == {"superseded"}


class TestEditableState:
    def test_draft_is_editable(self):
        assert is_editable_state("draft") is True

    def test_in_consultation_is_editable(self):
        assert is_editable_state("in_consultation") is True

    @pytest.mark.parametrize(
        "state",
        [
            "under_review",
            "endorsed",
            "activated",
            "post_event_review",
            "superseded",
        ],
    )
    def test_non_editable_states(self, state):
        assert is_editable_state(state) is False

    def test_editable_states_set(self):
        assert EDITABLE_STATES == {"draft", "in_consultation"}

    def test_unknown_state_not_editable(self):
        assert is_editable_state("nonexistent") is False

    def test_unknown_state_not_terminal(self):
        assert is_terminal_state("nonexistent") is False
