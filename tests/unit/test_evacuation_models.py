"""Tests for evacuation.models — enums, validators, and serialisation (T012)."""

from datetime import UTC, datetime

import pytest

from evacuation.models import (
    AuditBufferEntry,
    ClosureReason,
    ConfidenceLevel,
    DecisionType,
    EvacuationDecisionRecord,
    EvacuationPlan,
    HazardSummary,
    PlanStatus,
    Traceability,
    VulnerabilityCategory,
    confidence_to_level,
)


# ---------------------------------------------------------------------------
# DecisionType enum
# ---------------------------------------------------------------------------


class TestDecisionType:
    def test_has_exactly_fifteen_values(self):
        assert len(DecisionType) == 15

    def test_all_expected_values_present(self):
        expected = {
            "handoff_received",
            "handoff_rejected",
            "duplicate_discarded",
            "assessment_retrieved",
            "road_network_loaded",
            "zones_computed",
            "routes_computed",
            "transport_coordinated",
            "timeline_estimated",
            "plan_generated",
            "plan_updated",
            "override_applied",
            "shelter_in_place_recommended",
            "degradation_detected",
            "content_safety_failure",
        }
        assert {e.value for e in DecisionType} == expected


# ---------------------------------------------------------------------------
# ConfidenceLevel enum
# ---------------------------------------------------------------------------


class TestConfidenceLevel:
    def test_has_three_values(self):
        assert len(ConfidenceLevel) == 3

    def test_expected_values(self):
        assert {e.value for e in ConfidenceLevel} == {"low", "medium", "high"}


# ---------------------------------------------------------------------------
# PlanStatus enum
# ---------------------------------------------------------------------------


class TestPlanStatus:
    def test_has_seven_values(self):
        assert len(PlanStatus) == 7

    def test_expected_values(self):
        expected = {
            "proposed",
            "approved",
            "rejected",
            "superseded",
            "expired",
            "cancelled",
            "paused",
        }
        assert {e.value for e in PlanStatus} == expected


# ---------------------------------------------------------------------------
# VulnerabilityCategory enum
# ---------------------------------------------------------------------------


class TestVulnerabilityCategory:
    def test_has_four_values(self):
        assert len(VulnerabilityCategory) == 4

    def test_expected_values(self):
        expected = {
            "mobility_impaired",
            "medical_dependent",
            "elderly_aged_care",
            "children_schools_childcare",
        }
        assert {e.value for e in VulnerabilityCategory} == expected


# ---------------------------------------------------------------------------
# ClosureReason enum
# ---------------------------------------------------------------------------


class TestClosureReason:
    def test_has_six_values(self):
        assert len(ClosureReason) == 6

    def test_expected_values(self):
        expected = {
            "emergency_services_closure",
            "flood_cut",
            "fire_proximity",
            "structural_damage",
            "zone_1_closure",
            "capacity_exhausted",
        }
        assert {e.value for e in ClosureReason} == expected


# ---------------------------------------------------------------------------
# confidence_to_level mapping
# ---------------------------------------------------------------------------


class TestConfidenceToLevel:
    @pytest.mark.parametrize(
        "score, expected",
        [
            (0.0, ConfidenceLevel.low),
            (0.39, ConfidenceLevel.low),
            (0.4, ConfidenceLevel.medium),
            (0.5, ConfidenceLevel.medium),
            (0.69, ConfidenceLevel.medium),
            (0.7, ConfidenceLevel.high),
            (0.85, ConfidenceLevel.high),
            (1.0, ConfidenceLevel.high),
        ],
    )
    def test_maps_correctly(self, score, expected):
        assert confidence_to_level(score) == expected

    def test_boundary_below_0_4(self):
        assert confidence_to_level(0.399) == ConfidenceLevel.low

    def test_boundary_at_0_4(self):
        assert confidence_to_level(0.4) == ConfidenceLevel.medium

    def test_boundary_below_0_7(self):
        assert confidence_to_level(0.699) == ConfidenceLevel.medium

    def test_boundary_at_0_7(self):
        assert confidence_to_level(0.7) == ConfidenceLevel.high


# ---------------------------------------------------------------------------
# EvacuationPlan validation
# ---------------------------------------------------------------------------


class TestEvacuationPlan:
    def _minimal(self, **overrides):
        defaults = dict(
            plan_id="ep-inc-001-v1",
            incident_id="inc-001",
        )
        defaults.update(overrides)
        return EvacuationPlan(**defaults)

    def test_valid_construction(self):
        plan = self._minimal()
        assert plan.plan_id == "ep-inc-001-v1"
        assert plan.incident_id == "inc-001"
        assert plan.version == 1
        assert plan.status == PlanStatus.proposed

    def test_confidence_score_clamped_above_one(self):
        plan = self._minimal(confidence_score=1.5)
        assert plan.confidence_score == 1.0

    def test_confidence_score_clamped_below_zero(self):
        plan = self._minimal(confidence_score=-0.5)
        assert plan.confidence_score == 0.0

    def test_confidence_score_normal_range(self):
        plan = self._minimal(confidence_score=0.75)
        assert plan.confidence_score == 0.75

    def test_version_must_be_gte_one(self):
        with pytest.raises(Exception):
            self._minimal(version=0)

    def test_version_negative_raises(self):
        with pytest.raises(Exception):
            self._minimal(version=-1)

    def test_plan_id_format_valid(self):
        plan = self._minimal(plan_id="ep-my-incident-v3")
        assert plan.plan_id == "ep-my-incident-v3"

    def test_plan_id_invalid_format_raises(self):
        with pytest.raises(Exception):
            self._minimal(plan_id="bad-format")

    def test_plan_id_missing_prefix_raises(self):
        with pytest.raises(Exception):
            self._minimal(plan_id="plan-inc-v1")

    def test_plan_id_missing_version_suffix_raises(self):
        with pytest.raises(Exception):
            self._minimal(plan_id="ep-inc-001")

    def test_confidence_level_auto_derived_low(self):
        plan = self._minimal(confidence_score=0.2)
        assert plan.confidence_level == ConfidenceLevel.low

    def test_confidence_level_auto_derived_medium(self):
        plan = self._minimal(confidence_score=0.5)
        assert plan.confidence_level == ConfidenceLevel.medium

    def test_confidence_level_auto_derived_high(self):
        plan = self._minimal(confidence_score=0.8)
        assert plan.confidence_level == ConfidenceLevel.high

    def test_default_lists_empty(self):
        plan = self._minimal()
        assert plan.zones == []
        assert plan.routes == []
        assert plan.assembly_areas == []
        assert plan.phases == []
        assert plan.transport_requirements == []
        assert plan.overrides == []
        assert plan.shelter_in_place_zones == []

    def test_timestamps_populated(self):
        plan = self._minimal()
        assert plan.created_at is not None
        assert plan.updated_at is not None


# ---------------------------------------------------------------------------
# EvacuationDecisionRecord serialisation/deserialisation
# ---------------------------------------------------------------------------


class TestEvacuationDecisionRecord:
    def test_required_fields(self):
        record = EvacuationDecisionRecord(
            handoff_id="hf-1",
            decision_type=DecisionType.handoff_received,
        )
        assert record.handoff_id == "hf-1"
        assert record.decision_type == DecisionType.handoff_received

    def test_confidence_clamped_above_one(self):
        record = EvacuationDecisionRecord(
            handoff_id="hf-2",
            decision_type=DecisionType.plan_generated,
            confidence_raw=1.5,
            confidence_adjusted=2.0,
        )
        assert record.confidence_raw == 1.0
        assert record.confidence_adjusted == 1.0

    def test_confidence_clamped_below_zero(self):
        record = EvacuationDecisionRecord(
            handoff_id="hf-3",
            decision_type=DecisionType.plan_generated,
            confidence_raw=-0.5,
            confidence_adjusted=-1.0,
        )
        assert record.confidence_raw == 0.0
        assert record.confidence_adjusted == 0.0

    def test_default_values(self):
        record = EvacuationDecisionRecord(
            handoff_id="hf-4",
            decision_type=DecisionType.handoff_received,
        )
        assert record.zone_ids == []
        assert record.route_ids == []
        assert record.escalation_targets == []
        assert record.confidence_raw == 0.0
        assert record.confidence_adjusted == 0.0
        assert record.agent_version == "0.1.0"
        assert record.prompt_template_version == "1.0"
        assert record.generation_method == "llm"
        assert record.tenant_id == "live"

    def test_serialisation_round_trip(self):
        record = EvacuationDecisionRecord(
            handoff_id="hf-rt",
            decision_type=DecisionType.routes_computed,
            plan_id="ep-inc-v1",
            incident_id="inc-1",
            hazard_type="cyclone",
            zone_ids=["1", "2"],
            route_ids=["r-1"],
            population_affected=5000,
            confidence_raw=0.85,
            decision_rationale="Routes computed successfully",
        )
        data = record.model_dump(mode="json")
        restored = EvacuationDecisionRecord.model_validate(data)
        assert restored.handoff_id == "hf-rt"
        assert restored.decision_type == DecisionType.routes_computed
        assert restored.zone_ids == ["1", "2"]
        assert restored.confidence_raw == 0.85

    def test_missing_handoff_id_raises(self):
        with pytest.raises(Exception):
            EvacuationDecisionRecord(
                decision_type=DecisionType.handoff_received,
            )

    def test_missing_decision_type_raises(self):
        with pytest.raises(Exception):
            EvacuationDecisionRecord(handoff_id="hf-5")

    def test_id_auto_generated(self):
        r1 = EvacuationDecisionRecord(
            handoff_id="hf-a", decision_type=DecisionType.handoff_received
        )
        r2 = EvacuationDecisionRecord(
            handoff_id="hf-b", decision_type=DecisionType.handoff_received
        )
        assert r1.id != r2.id  # UUIDs should be unique


# ---------------------------------------------------------------------------
# AuditBufferEntry
# ---------------------------------------------------------------------------


class TestAuditBufferEntry:
    def test_wraps_record(self):
        record = EvacuationDecisionRecord(
            handoff_id="hf-6",
            decision_type=DecisionType.handoff_received,
        )
        entry = AuditBufferEntry(record=record)
        assert entry.record.handoff_id == "hf-6"
        assert entry.retry_count == 0
        assert entry.last_retry_at is None
        assert entry.buffered_at is not None

    def test_serialisation(self):
        record = EvacuationDecisionRecord(
            handoff_id="hf-7",
            decision_type=DecisionType.degradation_detected,
        )
        entry = AuditBufferEntry(record=record)
        data = entry.model_dump(mode="json")
        restored = AuditBufferEntry.model_validate(data)
        assert restored.record.handoff_id == "hf-7"
        assert restored.retry_count == 0
