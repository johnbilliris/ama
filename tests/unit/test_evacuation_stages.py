"""Unit tests for evacuation stage state machine."""

import pytest
from evacuation.stages import (
    create_initial_stage,
    is_re_entry,
    transition_stage,
    validate_transition,
)
from packages.domain.src.domain.models.evacuation_stage import (
    RE_ENTRY_TRANSITIONS,
    VALID_TRANSITIONS,
    EvacuationStage,
)


# ---------------------------------------------------------------------------
# validate_transition
# ---------------------------------------------------------------------------


class TestValidateTransition:
    @pytest.mark.parametrize(
        ("current", "target"),
        [
            ("decision", "warning"),
            ("decision", "shelter_in_place"),
            ("warning", "withdrawal"),
            ("warning", "decision"),
            ("withdrawal", "shelter"),
            ("withdrawal", "decision"),
            ("shelter", "return"),
            ("shelter", "decision"),
            ("return", "completed"),
            ("return", "decision"),
            ("shelter_in_place", "decision"),
        ],
    )
    def test_valid_forward_transitions(self, current: str, target: str) -> None:
        valid, error = validate_transition(current, target)
        assert valid is True
        assert error == ""

    @pytest.mark.parametrize(
        ("current", "target"),
        [
            ("decision", "completed"),
            ("warning", "return"),
            ("completed", "decision"),
            ("shelter", "warning"),
            ("return", "withdrawal"),
        ],
    )
    def test_invalid_transitions_raise(self, current: str, target: str) -> None:
        valid, error = validate_transition(current, target)
        assert valid is False
        assert "Invalid evacuation transition" in error

    def test_completed_has_no_transitions(self) -> None:
        valid, error = validate_transition("completed", "decision")
        assert valid is False


# ---------------------------------------------------------------------------
# is_re_entry
# ---------------------------------------------------------------------------


class TestIsReEntry:
    @pytest.mark.parametrize(
        ("current", "target"),
        [
            ("warning", "decision"),
            ("withdrawal", "decision"),
            ("shelter", "decision"),
            ("shelter_in_place", "decision"),
        ],
    )
    def test_re_entry_detection(self, current: str, target: str) -> None:
        assert is_re_entry(current, target) is True

    @pytest.mark.parametrize(
        ("current", "target"),
        [
            ("decision", "warning"),
            ("warning", "withdrawal"),
            ("shelter", "return"),
            ("return", "completed"),
        ],
    )
    def test_forward_is_not_re_entry(self, current: str, target: str) -> None:
        assert is_re_entry(current, target) is False

    def test_re_entry_transitions_set_size(self) -> None:
        assert len(RE_ENTRY_TRANSITIONS) == 4


# ---------------------------------------------------------------------------
# create_initial_stage
# ---------------------------------------------------------------------------


class TestCreateInitialStage:
    def test_creates_at_decision(self) -> None:
        stage = create_initial_stage(
            incident_id="INC-001",
            plan_id="PLN-001",
            decision_authority="IC Smith",
            decision_rationale="Approaching bushfire",
        )
        assert stage.current_stage == "decision"
        assert stage.decision_authority == "IC Smith"
        assert stage.decision_rationale == "Approaching bushfire"
        assert stage.incident_id == "INC-001"
        assert stage.evacuation_plan_id == "PLN-001"
        assert stage.re_entry_count == 0

    def test_creates_with_optional_fields(self) -> None:
        stage = create_initial_stage(
            incident_id="INC-002",
            plan_id="PLN-002",
            decision_authority="IC Jones",
            decision_rationale="Flood warning",
            evacuation_type="pre_warned",
            evacuation_approach="directed",
            evacuation_scope="total",
        )
        assert stage.evacuation_type == "pre_warned"
        assert stage.evacuation_approach == "directed"
        assert stage.evacuation_scope == "total"

    def test_stage_id_is_uuid(self) -> None:
        stage = create_initial_stage(
            incident_id="INC-003",
            plan_id="PLN-003",
            decision_authority="IC Test",
            decision_rationale="Test",
        )
        assert len(stage.stage_id) == 36  # UUID format


# ---------------------------------------------------------------------------
# transition_stage
# ---------------------------------------------------------------------------


class TestTransitionStage:
    @pytest.fixture()
    def decision_stage(self) -> EvacuationStage:
        return create_initial_stage(
            incident_id="INC-001",
            plan_id="PLN-001",
            decision_authority="IC Smith",
            decision_rationale="Fire approaching",
        )

    def test_transition_updates_current_stage(self, decision_stage: EvacuationStage) -> None:
        new_stage = transition_stage(
            decision_stage,
            "warning",
            authorized_by="IC Smith",
            rationale="Escalating to warning",
        )
        assert new_stage.current_stage == "warning"
        assert new_stage.previous_stage == "decision"

    def test_transition_preserves_incident_id(self, decision_stage: EvacuationStage) -> None:
        new_stage = transition_stage(
            decision_stage,
            "warning",
            authorized_by="IC Smith",
            rationale="Escalating",
        )
        assert new_stage.incident_id == "INC-001"

    def test_invalid_transition_raises(self, decision_stage: EvacuationStage) -> None:
        with pytest.raises(ValueError, match="Invalid evacuation transition"):
            transition_stage(
                decision_stage,
                "completed",
                authorized_by="IC Smith",
                rationale="Skip ahead",
            )

    def test_re_entry_increments_count(self) -> None:
        # Build a stage at "warning" via model_copy
        base = create_initial_stage(
            incident_id="INC-001",
            plan_id="PLN-001",
            decision_authority="IC Smith",
            decision_rationale="Fire",
        )
        warning = transition_stage(
            base, "warning", authorized_by="IC Smith", rationale="Escalate"
        )
        # Re-entry: warning → decision
        re_entry_stage = transition_stage(
            warning, "decision", authorized_by="IC Smith", rationale="Conditions improved",
            shelter_in_place_rationale=None,
        )
        assert re_entry_stage.current_stage == "decision"
        assert re_entry_stage.re_entry_count == 1

    def test_shelter_in_place_transition(self, decision_stage: EvacuationStage) -> None:
        sip = transition_stage(
            decision_stage,
            "shelter_in_place",
            authorized_by="IC Smith",
            rationale="Roads blocked",
            shelter_in_place_rationale="Safer to stay indoors",
        )
        assert sip.current_stage == "shelter_in_place"
        assert sip.shelter_in_place_rationale == "Safer to stay indoors"

    def test_full_lifecycle(self) -> None:
        """Walk through decision → warning → withdrawal → shelter → return → completed."""
        stage = create_initial_stage(
            incident_id="INC-001",
            plan_id="PLN-001",
            decision_authority="IC Smith",
            decision_rationale="Fire confirmed",
        )
        stage = transition_stage(stage, "warning", authorized_by="IC Smith", rationale="Alert")
        stage = transition_stage(stage, "withdrawal", authorized_by="IC Smith", rationale="Move")
        stage = transition_stage(stage, "shelter", authorized_by="IC Smith", rationale="Shelter")
        stage = transition_stage(stage, "return", authorized_by="IC Smith", rationale="Safe")
        stage = transition_stage(stage, "completed", authorized_by="IC Smith", rationale="Done")
        assert stage.current_stage == "completed"
        assert stage.re_entry_count == 0
