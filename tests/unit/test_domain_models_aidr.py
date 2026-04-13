"""Unit tests for AIDR domain models — validates Pydantic models, validators, and type constraints."""

from datetime import UTC, datetime

import pytest
from packages.domain.src.domain.models.aiims_role_assignment import (
    ALL_AIIMS_FUNCTIONS,
    AiimsRoleAssignment,
)
from packages.domain.src.domain.models.evacuation_stage import (
    VALID_TRANSITIONS,
    EvacuationStage,
)
from packages.domain.src.domain.models.handoff_chain import HandoffStep
from packages.domain.src.domain.models.incident import Incident
from packages.domain.src.domain.models.lesson import Lesson
from packages.domain.src.domain.models.pprr_phase_context import PprrPhaseContext
from packages.domain.src.domain.models.public_alert import (
    TIER_COLOUR_MAP,
    WARNING_PRINCIPLE_KEYS,
    PublicAlert,
)
from packages.domain.src.domain.models.recovery_environment_tracker import (
    AIDR_INDICATORS,
    ALL_RECOVERY_PRINCIPLES,
    RecoveryEnvironmentTracker,
    RecoveryIndicator,
)


# ---------------------------------------------------------------------------
# Incident
# ---------------------------------------------------------------------------


class TestIncident:
    """Tests for AIDR-extended Incident model."""

    @pytest.fixture()
    def base_kwargs(self) -> dict:
        return {
            "incident_id": "INC-001",
            "title": "Test Incident",
            "incident_type": "bushfire",
            "status": "active",
            "severity": "warning",
            "affected_jurisdiction_ids": ["jur-1"],
        }

    def test_existing_fields_still_work(self, base_kwargs: dict) -> None:
        inc = Incident(**base_kwargs)
        assert inc.incident_id == "INC-001"
        assert inc.status == "active"
        assert inc.participating_organisation_ids == []
        assert isinstance(inc.started_at, datetime)

    @pytest.mark.parametrize("itype", ["tsunami", "extreme_heat", "pandemic"])
    def test_new_incident_types_accepted(self, base_kwargs: dict, itype: str) -> None:
        inc = Incident(**{**base_kwargs, "incident_type": itype})
        assert inc.incident_type == itype

    def test_pprr_phase_default_none(self, base_kwargs: dict) -> None:
        inc = Incident(**base_kwargs)
        assert inc.pprr_phase is None

    @pytest.mark.parametrize("phase", ["prevention", "preparedness", "response", "recovery"])
    def test_pprr_phase_valid_values(self, base_kwargs: dict, phase: str) -> None:
        inc = Incident(**{**base_kwargs, "pprr_phase": phase})
        assert inc.pprr_phase == phase

    def test_incident_level_default_1(self, base_kwargs: dict) -> None:
        inc = Incident(**base_kwargs)
        assert inc.incident_level == 1

    @pytest.mark.parametrize("level", [1, 2, 3])
    def test_incident_level_valid_values(self, base_kwargs: dict, level: int) -> None:
        inc = Incident(**{**base_kwargs, "incident_level": level})
        assert inc.incident_level == level

    def test_incident_level_invalid_rejects(self, base_kwargs: dict) -> None:
        with pytest.raises(Exception):
            Incident(**{**base_kwargs, "incident_level": 4})

    def test_incident_type_invalid_rejects(self, base_kwargs: dict) -> None:
        with pytest.raises(Exception):
            Incident(**{**base_kwargs, "incident_type": "alien_invasion"})


# ---------------------------------------------------------------------------
# PublicAlert
# ---------------------------------------------------------------------------


class TestPublicAlert:
    """Tests for AWS warning-extended PublicAlert model."""

    @pytest.fixture()
    def base_kwargs(self) -> dict:
        return {
            "alert_id": "ALR-001",
            "incident_id": "INC-001",
        }

    def test_tier_colour_auto_mapping_advice(self, base_kwargs: dict) -> None:
        alert = PublicAlert(
            **base_kwargs,
            warning_tier="advice",
            action_statement="Stay informed",
        )
        assert alert.colour_code == "yellow"

    def test_tier_colour_auto_mapping_watch_and_act(self, base_kwargs: dict) -> None:
        alert = PublicAlert(
            **base_kwargs,
            warning_tier="watch_and_act",
            action_statement="Prepare to leave",
        )
        assert alert.colour_code == "orange"

    def test_tier_colour_auto_mapping_emergency(self, base_kwargs: dict) -> None:
        alert = PublicAlert(
            **base_kwargs,
            warning_tier="emergency_warning",
            action_statement="Leave now",
        )
        assert alert.colour_code == "red"

    def test_tier_colour_map_has_three_entries(self) -> None:
        assert TIER_COLOUR_MAP == {
            "advice": "yellow",
            "watch_and_act": "orange",
            "emergency_warning": "red",
        }

    def test_colour_mismatch_raises(self, base_kwargs: dict) -> None:
        with pytest.raises(ValueError, match="colour_code must be"):
            PublicAlert(
                **base_kwargs,
                warning_tier="advice",
                colour_code="red",
                action_statement="Stay informed",
            )

    def test_action_statement_required_with_tier(self, base_kwargs: dict) -> None:
        with pytest.raises(ValueError, match="action_statement is required"):
            PublicAlert(**base_kwargs, warning_tier="advice")

    def test_all_clear_with_tier_raises(self, base_kwargs: dict) -> None:
        with pytest.raises(ValueError, match="warning_tier must be None"):
            PublicAlert(
                **base_kwargs,
                warning_tier="advice",
                action_statement="All clear",
                is_all_clear=True,
            )

    def test_all_clear_without_tier_passes(self, base_kwargs: dict) -> None:
        alert = PublicAlert(**base_kwargs, is_all_clear=True)
        assert alert.is_all_clear is True
        assert alert.warning_tier is None

    def test_warning_principles_checklist_valid(self, base_kwargs: dict) -> None:
        checklist = {k: True for k in WARNING_PRINCIPLE_KEYS}
        alert = PublicAlert(**base_kwargs, warning_principles_checklist=checklist)
        assert len(alert.warning_principles_checklist) == 10

    def test_warning_principles_checklist_wrong_keys_raises(self, base_kwargs: dict) -> None:
        with pytest.raises(ValueError, match="warning_principles_checklist must have exactly"):
            PublicAlert(
                **base_kwargs,
                warning_principles_checklist={"wrong_key": True},
            )

    def test_warning_principles_checklist_empty_passes(self, base_kwargs: dict) -> None:
        alert = PublicAlert(**base_kwargs)
        assert alert.warning_principles_checklist == {}

    def test_warning_principle_keys_has_10(self) -> None:
        assert len(WARNING_PRINCIPLE_KEYS) == 10


# ---------------------------------------------------------------------------
# AiimsRoleAssignment
# ---------------------------------------------------------------------------


class TestAiimsRoleAssignment:
    """Tests for AIIMS role assignment model."""

    @pytest.fixture()
    def base_kwargs(self) -> dict:
        return {
            "assignment_id": "ASGN-001",
            "incident_id": "INC-001",
            "agent_identifier": "monitoring",
            "aiims_function": "intelligence",
            "assigned_by": "admin",
        }

    def test_valid_creation(self, base_kwargs: dict) -> None:
        role = AiimsRoleAssignment(**base_kwargs)
        assert role.assignment_id == "ASGN-001"
        assert role.aiims_function == "intelligence"
        assert role.is_active is True
        assert role.unassigned_at is None
        assert isinstance(role.assigned_at, datetime)

    def test_is_active_with_unassigned_at_raises(self, base_kwargs: dict) -> None:
        with pytest.raises(ValueError, match="is_active cannot be True when unassigned_at"):
            AiimsRoleAssignment(
                **base_kwargs,
                is_active=True,
                unassigned_at=datetime.now(UTC),
            )

    def test_inactive_with_unassigned_at_passes(self, base_kwargs: dict) -> None:
        role = AiimsRoleAssignment(
            **base_kwargs,
            is_active=False,
            unassigned_at=datetime.now(UTC),
        )
        assert role.is_active is False

    @pytest.mark.parametrize("func", ALL_AIIMS_FUNCTIONS)
    def test_all_six_functions_accepted(self, base_kwargs: dict, func: str) -> None:
        role = AiimsRoleAssignment(**{**base_kwargs, "aiims_function": func})
        assert role.aiims_function == func

    def test_six_functions_defined(self) -> None:
        assert len(ALL_AIIMS_FUNCTIONS) == 6

    def test_invalid_function_rejected(self, base_kwargs: dict) -> None:
        with pytest.raises(Exception):
            AiimsRoleAssignment(**{**base_kwargs, "aiims_function": "cooking"})


# ---------------------------------------------------------------------------
# EvacuationStage
# ---------------------------------------------------------------------------


class TestEvacuationStage:
    """Tests for evacuation stage model and transitions map."""

    @pytest.fixture()
    def decision_kwargs(self) -> dict:
        return {
            "stage_id": "STG-001",
            "incident_id": "INC-001",
            "evacuation_plan_id": "PLN-001",
            "current_stage": "decision",
            "decision_authority": "IC Smith",
            "decision_rationale": "Bushfire approaching",
        }

    def test_decision_stage_requires_authority_and_rationale(self) -> None:
        with pytest.raises(ValueError, match="decision_authority and decision_rationale"):
            EvacuationStage(
                stage_id="STG-001",
                incident_id="INC-001",
                evacuation_plan_id="PLN-001",
                current_stage="decision",
            )

    def test_decision_stage_valid(self, decision_kwargs: dict) -> None:
        stage = EvacuationStage(**decision_kwargs)
        assert stage.current_stage == "decision"
        assert stage.decision_authority == "IC Smith"

    def test_shelter_in_place_requires_rationale(self) -> None:
        with pytest.raises(ValueError, match="shelter_in_place_rationale is required"):
            EvacuationStage(
                stage_id="STG-002",
                incident_id="INC-001",
                evacuation_plan_id="PLN-001",
                current_stage="shelter_in_place",
            )

    def test_shelter_in_place_valid(self) -> None:
        stage = EvacuationStage(
            stage_id="STG-002",
            incident_id="INC-001",
            evacuation_plan_id="PLN-001",
            current_stage="shelter_in_place",
            shelter_in_place_rationale="Too dangerous to move",
        )
        assert stage.current_stage == "shelter_in_place"

    @pytest.mark.parametrize(
        "stage_name",
        ["decision", "warning", "withdrawal", "shelter", "return", "shelter_in_place", "completed"],
    )
    def test_valid_stage_names_accepted(self, stage_name: str) -> None:
        assert stage_name in VALID_TRANSITIONS

    def test_valid_transitions_structure(self) -> None:
        assert len(VALID_TRANSITIONS) == 7
        assert VALID_TRANSITIONS["decision"] == ["warning", "shelter_in_place"]
        assert VALID_TRANSITIONS["completed"] == []
        for targets in VALID_TRANSITIONS.values():
            assert isinstance(targets, list)


# ---------------------------------------------------------------------------
# RecoveryIndicator & RecoveryEnvironmentTracker
# ---------------------------------------------------------------------------


class TestRecoveryIndicator:
    """Tests for recovery indicator k-anonymity and regression validation."""

    def test_k_anonymity_violation_raises(self) -> None:
        with pytest.raises(ValueError, match="population_coverage must be ≥ 10"):
            RecoveryIndicator(
                indicator_name="health",
                environment="social",
                data_classification="sensitive",
                population_coverage=5,
            )

    def test_k_anonymity_at_threshold_passes(self) -> None:
        ind = RecoveryIndicator(
            indicator_name="health",
            environment="social",
            data_classification="sensitive",
            population_coverage=10,
        )
        assert ind.population_coverage == 10

    def test_k_anonymity_above_threshold_passes(self) -> None:
        ind = RecoveryIndicator(
            indicator_name="health",
            environment="social",
            data_classification="sensitive",
            population_coverage=100,
        )
        assert ind.population_coverage == 100

    def test_k_anonymity_not_enforced_for_public(self) -> None:
        ind = RecoveryIndicator(
            indicator_name="health",
            environment="social",
            data_classification="public",
            population_coverage=3,
        )
        assert ind.population_coverage == 3

    def test_k_anonymity_not_enforced_for_non_social(self) -> None:
        ind = RecoveryIndicator(
            indicator_name="air_quality",
            environment="natural",
            data_classification="sensitive",
            population_coverage=2,
        )
        assert ind.population_coverage == 2

    def test_regression_requires_cause(self) -> None:
        with pytest.raises(ValueError, match="regression_cause is required"):
            RecoveryIndicator(
                indicator_name="employment",
                environment="social",
                is_regressed=True,
            )

    def test_regression_with_cause_passes(self) -> None:
        ind = RecoveryIndicator(
            indicator_name="employment",
            environment="social",
            is_regressed=True,
            regression_cause="Economic downturn after second flood",
        )
        assert ind.is_regressed is True


class TestRecoveryEnvironmentTracker:
    """Tests for recovery environment tracker and AIDR indicators."""

    def test_21_indicators_across_4_environments(self) -> None:
        total = sum(len(v) for v in AIDR_INDICATORS.values())
        assert total == 21
        assert len(AIDR_INDICATORS) == 4

    def test_social_has_7_indicators(self) -> None:
        assert len(AIDR_INDICATORS["social"]) == 7

    def test_built_has_5_indicators(self) -> None:
        assert len(AIDR_INDICATORS["built"]) == 5

    def test_economic_has_5_indicators(self) -> None:
        assert len(AIDR_INDICATORS["economic"]) == 5

    def test_natural_has_4_indicators(self) -> None:
        assert len(AIDR_INDICATORS["natural"]) == 4

    def test_valid_recovery_principles(self) -> None:
        tracker = RecoveryEnvironmentTracker(
            tracker_id="TRK-001",
            incident_id="INC-001",
            recovery_principles_applied=["community_led", "build_capacity"],
        )
        assert len(tracker.recovery_principles_applied) == 2

    def test_invalid_recovery_principle_raises(self) -> None:
        with pytest.raises(ValueError, match="Invalid recovery principle"):
            RecoveryEnvironmentTracker(
                tracker_id="TRK-001",
                incident_id="INC-001",
                recovery_principles_applied=["not_a_principle"],
            )

    def test_six_recovery_principles_defined(self) -> None:
        assert len(ALL_RECOVERY_PRINCIPLES) == 6

    def test_empty_principles_passes(self) -> None:
        tracker = RecoveryEnvironmentTracker(
            tracker_id="TRK-001",
            incident_id="INC-001",
        )
        assert tracker.recovery_principles_applied == []


# ---------------------------------------------------------------------------
# Lesson
# ---------------------------------------------------------------------------


class TestLesson:
    """Tests for lesson model validators."""

    @pytest.fixture()
    def base_kwargs(self) -> dict:
        return {
            "lesson_id": "LES-001",
            "title": "Communication delay",
            "description": "Alerts were delayed by 15 minutes",
        }

    def test_at_least_one_context_required(self, base_kwargs: dict) -> None:
        with pytest.raises(ValueError, match="At least one of incident_id or scenario_run_id"):
            Lesson(**base_kwargs)

    def test_incident_id_alone_passes(self, base_kwargs: dict) -> None:
        lesson = Lesson(**base_kwargs, incident_id="INC-001")
        assert lesson.incident_id == "INC-001"

    def test_scenario_run_id_alone_passes(self, base_kwargs: dict) -> None:
        lesson = Lesson(**base_kwargs, scenario_run_id="SCN-001")
        assert lesson.scenario_run_id == "SCN-001"

    def test_both_contexts_pass(self, base_kwargs: dict) -> None:
        lesson = Lesson(**base_kwargs, incident_id="INC-001", scenario_run_id="SCN-001")
        assert lesson.incident_id is not None
        assert lesson.scenario_run_id is not None

    def test_resolved_requires_resolved_at(self, base_kwargs: dict) -> None:
        with pytest.raises(ValueError, match="resolved_at is required"):
            Lesson(**base_kwargs, incident_id="INC-001", status="resolved")

    def test_resolved_requires_resolution_reference(self, base_kwargs: dict) -> None:
        with pytest.raises(ValueError, match="resolution_reference is required"):
            Lesson(
                **base_kwargs,
                incident_id="INC-001",
                status="resolved",
                resolved_at=datetime.now(UTC),
            )

    def test_resolved_with_all_fields_passes(self, base_kwargs: dict) -> None:
        lesson = Lesson(
            **base_kwargs,
            incident_id="INC-001",
            status="resolved",
            resolved_at=datetime.now(UTC),
            resolution_reference="PR-123",
        )
        assert lesson.status == "resolved"

    def test_contradictory_resolved_requires_escalation(self, base_kwargs: dict) -> None:
        with pytest.raises(ValueError, match="escalation_approved_by is required"):
            Lesson(
                **base_kwargs,
                incident_id="INC-001",
                status="resolved",
                resolved_at=datetime.now(UTC),
                resolution_reference="PR-123",
                is_contradictory=True,
            )

    def test_contradictory_resolved_with_escalation_passes(self, base_kwargs: dict) -> None:
        lesson = Lesson(
            **base_kwargs,
            incident_id="INC-001",
            status="resolved",
            resolved_at=datetime.now(UTC),
            resolution_reference="PR-123",
            is_contradictory=True,
            escalation_approved_by="manager@example.com",
        )
        assert lesson.is_contradictory is True
        assert lesson.escalation_approved_by == "manager@example.com"


# ---------------------------------------------------------------------------
# PprrPhaseContext
# ---------------------------------------------------------------------------


class TestPprrPhaseContext:
    """Tests for PPRR phase context model."""

    @pytest.fixture()
    def base_kwargs(self) -> dict:
        return {
            "context_id": "CTX-001",
            "context_type": "region",
            "context_reference_id": "REG-001",
            "activated_by": "admin",
        }

    def test_prevention_phase_accepted(self, base_kwargs: dict) -> None:
        ctx = PprrPhaseContext(**base_kwargs, pprr_phase="prevention")
        assert ctx.pprr_phase == "prevention"

    def test_preparedness_phase_accepted(self, base_kwargs: dict) -> None:
        ctx = PprrPhaseContext(**base_kwargs, pprr_phase="preparedness")
        assert ctx.pprr_phase == "preparedness"

    def test_response_phase_rejected(self, base_kwargs: dict) -> None:
        with pytest.raises(Exception):
            PprrPhaseContext(**base_kwargs, pprr_phase="response")

    def test_recovery_phase_rejected(self, base_kwargs: dict) -> None:
        with pytest.raises(Exception):
            PprrPhaseContext(**base_kwargs, pprr_phase="recovery")

    def test_transition_requires_deactivated_at(self, base_kwargs: dict) -> None:
        with pytest.raises(ValueError, match="deactivated_at must be set"):
            PprrPhaseContext(
                **base_kwargs,
                pprr_phase="preparedness",
                transitioned_to_incident_id="INC-001",
            )

    def test_transition_with_deactivated_at_passes(self, base_kwargs: dict) -> None:
        ctx = PprrPhaseContext(
            **base_kwargs,
            pprr_phase="preparedness",
            transitioned_to_incident_id="INC-001",
            deactivated_at=datetime.now(UTC),
        )
        assert ctx.transitioned_to_incident_id == "INC-001"


# ---------------------------------------------------------------------------
# HandoffStep
# ---------------------------------------------------------------------------


class TestHandoffStep:
    """Tests for handoff step category filters."""

    def test_recovery_assessment_category_accepted(self) -> None:
        step = HandoffStep(
            step_order=1,
            source_agent="recovery_tracker",
            target_agent="reporting",
            category_filter=["recovery_assessment"],
        )
        assert "recovery_assessment" in step.category_filter

    def test_lessons_capture_category_accepted(self) -> None:
        step = HandoffStep(
            step_order=1,
            source_agent="lessons_agent",
            target_agent="planning",
            category_filter=["lessons_capture"],
        )
        assert "lessons_capture" in step.category_filter

    def test_multiple_categories_including_new_ones(self) -> None:
        step = HandoffStep(
            step_order=1,
            source_agent="multi_agent",
            target_agent="coordinator",
            category_filter=["weather", "recovery_assessment", "lessons_capture"],
        )
        assert len(step.category_filter) == 3

    def test_invalid_category_rejected(self) -> None:
        with pytest.raises(Exception):
            HandoffStep(
                step_order=1,
                source_agent="agent_a",
                target_agent="agent_b",
                category_filter=["not_a_category"],
            )
