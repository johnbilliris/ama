"""Unit tests for Resource Allocation Agent models, enums, and validation.

Covers:
- All 8 enum completeness checks
- ResourceDeploymentPlan validation (plan_id regex, version, confidence, confidence_level derivation)
- ResourceDemand, ResourceAssignment, AllocationDecisionRecord validation
- ScoringRationale, ShortfallDetail, ResourceInventoryItem validation
"""

from __future__ import annotations

import pytest
from datetime import UTC, datetime

from resource_allocation.models import (
    AllocationDecisionRecord,
    AuditBufferEntry,
    ConfidenceLevel,
    DecisionType,
    DemandFulfilmentStatus,
    DeploymentTimeline,
    InputSnapshot,
    OverrideMetadata,
    PlanStatus,
    PriorityTier,
    ResourceAssignment,
    ResourceDemand,
    ResourceDeploymentPlan,
    ResourceInventoryItem,
    ResourceStatus,
    ResourceType,
    ScoringRationale,
    ShortfallDetail,
    Traceability,
    TradeOffAnalysis,
    UrgencyLevel,
    confidence_to_level,
)


# ---------------------------------------------------------------------------
# Enum completeness
# ---------------------------------------------------------------------------


class TestEnumCompleteness:
    """Verify all enums have the expected number of values."""

    def test_decision_type_has_16_values(self):
        assert len(DecisionType) == 16

    def test_confidence_level_has_3_values(self):
        assert len(ConfidenceLevel) == 3
        assert set(ConfidenceLevel) == {
            ConfidenceLevel.low,
            ConfidenceLevel.medium,
            ConfidenceLevel.high,
        }

    def test_plan_status_has_6_values(self):
        assert len(PlanStatus) == 6

    def test_resource_status_has_7_values(self):
        assert len(ResourceStatus) == 7
        expected = {"available", "reserved", "assigned", "en_route", "deployed", "returning", "unavailable"}
        assert {s.value for s in ResourceStatus} == expected

    def test_resource_type_has_4_values(self):
        assert len(ResourceType) == 4
        assert set(rt.value for rt in ResourceType) == {"vehicle", "personnel", "supply", "facility"}

    def test_demand_fulfilment_status_has_5_values(self):
        assert len(DemandFulfilmentStatus) == 5

    def test_priority_tier_has_3_values(self):
        assert len(PriorityTier) == 3

    def test_urgency_level_has_4_values(self):
        assert len(UrgencyLevel) == 4


# ---------------------------------------------------------------------------
# Confidence level derivation
# ---------------------------------------------------------------------------


class TestConfidenceToLevel:
    def test_low_confidence(self):
        assert confidence_to_level(0.0) == ConfidenceLevel.low
        assert confidence_to_level(0.39) == ConfidenceLevel.low

    def test_medium_confidence(self):
        assert confidence_to_level(0.4) == ConfidenceLevel.medium
        assert confidence_to_level(0.69) == ConfidenceLevel.medium

    def test_high_confidence(self):
        assert confidence_to_level(0.7) == ConfidenceLevel.high
        assert confidence_to_level(1.0) == ConfidenceLevel.high


# ---------------------------------------------------------------------------
# ResourceDeploymentPlan validation
# ---------------------------------------------------------------------------


class TestResourceDeploymentPlan:
    def _make_plan(self, **overrides):
        defaults = {
            "plan_id": "rdp-inc001-v1",
            "incident_id": "inc001",
            "version": 1,
            "confidence_score": 0.85,
            "confidence_level": "high",
            "traceability": Traceability(handoff_id="h-001"),
        }
        defaults.update(overrides)
        return ResourceDeploymentPlan(**defaults)

    def test_valid_plan_id(self):
        plan = self._make_plan()
        assert plan.plan_id == "rdp-inc001-v1"

    def test_invalid_plan_id_rejected(self):
        with pytest.raises(ValueError, match="plan_id must match"):
            self._make_plan(plan_id="invalid-format")

    def test_plan_id_regex_various(self):
        # Valid formats
        self._make_plan(plan_id="rdp-inc001-v1")
        self._make_plan(plan_id="rdp-flood-2024-v99")
        self._make_plan(plan_id="rdp-a-v1")

        # Invalid formats
        with pytest.raises(ValueError):
            self._make_plan(plan_id="rdp--v1")  # needs content between rdp- and -v

    def test_version_must_be_positive(self):
        plan = self._make_plan(version=1)
        assert plan.version == 1

        with pytest.raises(ValueError, match="version must be >= 1"):
            self._make_plan(version=0)

        with pytest.raises(ValueError, match="version must be >= 1"):
            self._make_plan(version=-1)

    def test_confidence_clamped_to_range(self):
        plan = self._make_plan(confidence_score=1.5)
        assert plan.confidence_score == 1.0

        plan = self._make_plan(confidence_score=-0.5)
        assert plan.confidence_score == 0.0

    def test_confidence_normal_values(self):
        plan = self._make_plan(confidence_score=0.5)
        assert plan.confidence_score == 0.5

    def test_default_status_is_proposed(self):
        plan = self._make_plan()
        assert plan.status == PlanStatus.proposed

    def test_plan_has_all_required_fields(self):
        plan = self._make_plan()
        assert plan.incident_id == "inc001"
        assert plan.version >= 1
        assert isinstance(plan.demands, list)
        assert isinstance(plan.assignments, list)
        assert isinstance(plan.unmet_demands, list)
        assert isinstance(plan.deployment_timelines, list)
        assert isinstance(plan.input_snapshot, InputSnapshot)
        assert isinstance(plan.traceability, Traceability)


# ---------------------------------------------------------------------------
# ResourceDemand validation
# ---------------------------------------------------------------------------


class TestResourceDemand:
    def test_required_fields(self):
        demand = ResourceDemand(
            demand_id="dem-001",
            incident_id="inc001",
            source_id="rec-001",
            source_type="coordination_task",
            resource_type=ResourceType.vehicle,
            resource_sub_type="ambulance",
        )
        assert demand.demand_id == "dem-001"
        assert demand.quantity == 1
        assert demand.fulfilment_status == DemandFulfilmentStatus.pending

    def test_default_values(self):
        demand = ResourceDemand(
            demand_id="dem-002",
            incident_id="inc001",
            source_id="rec-001",
            source_type="coordination_task",
            resource_type=ResourceType.personnel,
            resource_sub_type="paramedic",
        )
        assert demand.urgency == UrgencyLevel.moderate
        assert demand.priority_tier == PriorityTier.tier_2_property


# ---------------------------------------------------------------------------
# ResourceAssignment validation
# ---------------------------------------------------------------------------


class TestResourceAssignment:
    def test_required_fields(self):
        assignment = ResourceAssignment(
            assignment_id="asgn-001",
            demand_id="dem-001",
            resource_id="res-001",
        )
        assert assignment.assignment_status == "proposed"
        assert assignment.score == 0.0
        assert isinstance(assignment.scoring_rationale, ScoringRationale)

    def test_scoring_rationale_defaults(self):
        rationale = ScoringRationale()
        assert rationale.capability_match == 0.0
        assert rationale.alternatives_considered == 0
        assert rationale.tie_break_applied is None


# ---------------------------------------------------------------------------
# AllocationDecisionRecord validation
# ---------------------------------------------------------------------------


class TestAllocationDecisionRecord:
    def test_required_fields(self):
        record = AllocationDecisionRecord(
            handoff_id="h-001",
            decision_type=DecisionType.handoff_received,
        )
        assert record.handoff_id == "h-001"
        assert record.id  # auto-generated UUID
        assert record.confidence_score == 0.0

    def test_confidence_clamped(self):
        record = AllocationDecisionRecord(
            handoff_id="h-001",
            decision_type=DecisionType.plan_generated,
            confidence_score=1.5,
        )
        assert record.confidence_score == 1.0

    def test_optional_fields_default_none(self):
        record = AllocationDecisionRecord(
            handoff_id="h-001",
            decision_type=DecisionType.handoff_received,
        )
        assert record.plan_id is None
        assert record.demand_id is None
        assert record.resource_id is None
        assert record.override_by_user_id is None
        assert record.buffered_at is None
        assert record.flush_source is None


# ---------------------------------------------------------------------------
# ResourceInventoryItem
# ---------------------------------------------------------------------------


class TestResourceInventoryItem:
    def test_default_status_is_available(self):
        item = ResourceInventoryItem(
            resource_id="res-001",
            resource_type=ResourceType.vehicle,
            resource_sub_type="ambulance",
        )
        assert item.status == ResourceStatus.available
        assert item.capabilities == []
        assert item.flags == []

    def test_capability_list(self):
        item = ResourceInventoryItem(
            resource_id="res-002",
            resource_type=ResourceType.vehicle,
            resource_sub_type="ambulance",
            capabilities=["medical_transport", "patient_stabilization"],
        )
        assert len(item.capabilities) == 2
        assert "medical_transport" in item.capabilities


# ---------------------------------------------------------------------------
# ShortfallDetail
# ---------------------------------------------------------------------------


class TestShortfallDetail:
    def test_quantity_invariant(self):
        shortfall = ShortfallDetail(
            demand_id="dem-001",
            resource_type=ResourceType.vehicle,
            resource_sub_type="ambulance",
            quantity_requested=5,
            quantity_assigned=3,
            quantity_unmet=2,
            reason="Insufficient ambulances",
            recommendation="Request mutual aid",
        )
        assert shortfall.quantity_unmet == shortfall.quantity_requested - shortfall.quantity_assigned


# ---------------------------------------------------------------------------
# AuditBufferEntry
# ---------------------------------------------------------------------------


class TestAuditBufferEntry:
    def test_wraps_record(self):
        record = AllocationDecisionRecord(
            handoff_id="h-001",
            decision_type=DecisionType.handoff_received,
        )
        entry = AuditBufferEntry(record=record)
        assert entry.record.handoff_id == "h-001"
        assert entry.retry_count == 0
