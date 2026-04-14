"""Unit tests for EmergencyPlan domain model and RecoveryIndicator extension.

Tests: 7-state lifecycle, 27 sections, 8 planning principles, endorsement rules.
"""
from datetime import UTC, datetime

import pytest

from packages.domain.src.domain.models.emergency_plan import (
    PLAN_SECTION_SLUGS,
    PLANNING_PRINCIPLES,
    EmergencyPlan,
    PlanActivationRecord,
    PlanAmendment,
    PlanSection,
)
from packages.domain.src.domain.models.recovery_environment_tracker import RecoveryIndicator


class TestEmergencyPlan:
    def test_valid_draft_plan(self):
        plan = EmergencyPlan(plan_id="ep-1", title="Flood Plan", region_id="r-au-nsw", hazard_types=["flood"])
        assert plan.lifecycle_state == "draft"
        assert plan.version == 1

    def test_all_lifecycle_states_valid(self):
        states = [
            "draft", "in_consultation", "under_review", "endorsed",
            "activated", "post_event_review", "superseded",
        ]
        assert len(states) == 7
        # endorsed+ states need endorsed_by/endorsed_at
        for state in ["endorsed", "activated", "post_event_review"]:
            plan = EmergencyPlan(
                plan_id="ep-1", title="Test", region_id="r-1", hazard_types=["flood"],
                lifecycle_state=state, endorsed_by="auth-1", endorsed_at=datetime.now(UTC),
            )
            assert plan.lifecycle_state == state

    def test_endorsed_requires_endorsed_by(self):
        with pytest.raises(ValueError, match="endorsed_by required"):
            EmergencyPlan(
                plan_id="ep-1", title="Test", region_id="r-1", hazard_types=["flood"],
                lifecycle_state="endorsed",
            )

    def test_endorsed_requires_endorsed_at(self):
        with pytest.raises(ValueError, match="endorsed_at required"):
            EmergencyPlan(
                plan_id="ep-1", title="Test", region_id="r-1", hazard_types=["flood"],
                lifecycle_state="endorsed", endorsed_by="auth-1",
            )

    def test_hazard_types_non_empty(self):
        with pytest.raises(ValueError, match="hazard_types must be non-empty"):
            EmergencyPlan(plan_id="ep-1", title="Test", region_id="r-1", hazard_types=[])

    def test_section_slugs_count(self):
        assert len(PLAN_SECTION_SLUGS) == 27

    def test_planning_principles_count(self):
        assert len(PLANNING_PRINCIPLES) == 8

    def test_valid_planning_principles_checklist(self):
        plan = EmergencyPlan(
            plan_id="ep-1", title="Test", region_id="r-1", hazard_types=["flood"],
            planning_principles_checklist={"risk_informed": True, "strategic": False},
        )
        assert plan.planning_principles_checklist["risk_informed"] is True

    def test_invalid_planning_principle_key(self):
        with pytest.raises(ValueError, match="Invalid planning principle key"):
            EmergencyPlan(
                plan_id="ep-1", title="Test", region_id="r-1", hazard_types=["flood"],
                planning_principles_checklist={"invalid_principle": True},
            )

    def test_plan_section_nesting(self):
        section = PlanSection(section_slug="authority", title="Authority")
        plan = EmergencyPlan(
            plan_id="ep-1", title="Test", region_id="r-1", hazard_types=["flood"],
            plan_sections={"authority": section},
        )
        assert plan.plan_sections["authority"].section_slug == "authority"

    def test_activation_record_nesting(self):
        record = PlanActivationRecord(incident_id="inc-1", activated_at=datetime.now(UTC), activated_by="ic-1")
        plan = EmergencyPlan(
            plan_id="ep-1", title="Test", region_id="r-1", hazard_types=["flood"],
            activation_records=[record],
        )
        assert len(plan.activation_records) == 1
        assert plan.activation_records[0].incident_id == "inc-1"

    def test_amendment_nesting(self):
        amendment = PlanAmendment(
            amendment_number=1, description="Update", amended_by="user-1", amended_at=datetime.now(UTC)
        )
        plan = EmergencyPlan(
            plan_id="ep-1", title="Test", region_id="r-1", hazard_types=["flood"],
            amendment_register=[amendment],
        )
        assert len(plan.amendment_register) == 1


class TestRecoveryIndicatorExtension:
    def test_valid_catalogue_indicator_id(self):
        ri = RecoveryIndicator(
            indicator_name="health", environment="social",
            catalogue_indicator_id="aidr:social:community-health-levels:ind:1",
        )
        assert ri.catalogue_indicator_id == "aidr:social:community-health-levels:ind:1"

    def test_none_catalogue_indicator_id(self):
        ri = RecoveryIndicator(indicator_name="health", environment="social")
        assert ri.catalogue_indicator_id is None

    def test_invalid_catalogue_indicator_id(self):
        with pytest.raises(ValueError, match="catalogue_indicator_id must match"):
            RecoveryIndicator(
                indicator_name="health", environment="social",
                catalogue_indicator_id="invalid-format",
            )

    def test_catalogue_id_wrong_domain(self):
        with pytest.raises(ValueError, match="catalogue_indicator_id must match"):
            RecoveryIndicator(
                indicator_name="health", environment="social",
                catalogue_indicator_id="aidr:invalid:test:ind:1",
            )
