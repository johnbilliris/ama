"""Contract tests for plan output schema.

Verifies ResourceDeploymentPlan output matches schema per data-model.md.
"""

from __future__ import annotations

import pytest
from datetime import UTC, datetime

from resource_allocation.models import (
    ConfidenceLevel,
    DeploymentTimeline,
    InputSnapshot,
    PlanStatus,
    ResourceAssignment,
    ResourceDemand,
    ResourceDeploymentPlan,
    ResourceType,
    ScoringRationale,
    ShortfallDetail,
    Traceability,
    UrgencyLevel,
)


class TestPlanOutputSchema:
    """Verify plan output has all required fields per data-model.md."""

    def _make_full_plan(self):
        demand = ResourceDemand(
            demand_id="dem-001",
            incident_id="inc001",
            source_id="rec-001",
            source_type="coordination_task",
            resource_type=ResourceType.vehicle,
            resource_sub_type="ambulance",
            required_capabilities=["medical_transport"],
            quantity=1,
            location={"lat": -33.87, "lon": 151.21},
            urgency=UrgencyLevel.critical,
        )

        rationale = ScoringRationale(
            capability_match=1.0,
            distance_km=5.2,
            distance_factor=0.192,
            availability_factor=1.0,
            priority_weight=4.0,
            final_score=0.769,
            selection_reason="Closest available ambulance",
            alternatives_considered=3,
            tie_break_applied=None,
        )

        assignment = ResourceAssignment(
            assignment_id="asgn-001",
            demand_id="dem-001",
            resource_id="veh-amb-001",
            score=0.769,
            scoring_rationale=rationale,
            estimated_travel_minutes=15.2,
            distance_km=5.2,
        )

        shortfall = ShortfallDetail(
            demand_id="dem-002",
            resource_type=ResourceType.personnel,
            resource_sub_type="hazmat",
            quantity_requested=2,
            quantity_assigned=0,
            quantity_unmet=2,
            reason="No hazmat teams available",
            recommendation="Request mutual aid from neighbouring region",
        )

        timeline = DeploymentTimeline(
            assignment_id="asgn-001",
            resource_id="veh-amb-001",
            mobilisation_minutes=10.0,
            travel_minutes=5.2,
            total_deployment_minutes=15.2,
        )

        return ResourceDeploymentPlan(
            plan_id="rdp-inc001-v1",
            incident_id="inc001",
            version=1,
            demands=[demand],
            assignments=[assignment],
            unmet_demands=[shortfall],
            deployment_timelines=[timeline],
            confidence_score=0.85,
            confidence_level=ConfidenceLevel.high,
            status=PlanStatus.proposed,
            generation_method="ai_assisted",
            configuration_version="abc123",
            input_snapshot=InputSnapshot(
                demands_snapshot=[demand.model_dump(mode="json")],
                inventory_snapshot_hash="sha256hash",
                config_version="abc123",
            ),
            traceability=Traceability(
                handoff_id="h-001",
                recommendation_id="rec-001",
                assessment_id="ha-001",
            ),
            summary="Test plan summary",
            incident_scope_key="live:inc001",
        )

    def test_all_required_fields_present(self):
        plan = self._make_full_plan()
        assert plan.plan_id is not None
        assert plan.incident_id is not None
        assert plan.version >= 1
        assert isinstance(plan.demands, list)
        assert isinstance(plan.assignments, list)
        assert isinstance(plan.unmet_demands, list)
        assert isinstance(plan.deployment_timelines, list)
        assert 0.0 <= plan.confidence_score <= 1.0
        assert plan.confidence_level in ConfidenceLevel
        assert plan.status in PlanStatus
        assert plan.generation_method in ("ai_assisted", "template_fallback", "safety_fallback", "commander_override")
        assert isinstance(plan.traceability, Traceability)

    def test_assignment_has_scoring_rationale(self):
        plan = self._make_full_plan()
        for assignment in plan.assignments:
            r = assignment.scoring_rationale
            assert isinstance(r.capability_match, float)
            assert isinstance(r.distance_km, float)
            assert isinstance(r.distance_factor, float)
            assert isinstance(r.availability_factor, float)
            assert isinstance(r.priority_weight, float)
            assert isinstance(r.final_score, float)
            assert isinstance(r.selection_reason, str)
            assert isinstance(r.alternatives_considered, int)

    def test_shortfall_has_quantities(self):
        plan = self._make_full_plan()
        for shortfall in plan.unmet_demands:
            assert shortfall.quantity_unmet == shortfall.quantity_requested - shortfall.quantity_assigned
            assert shortfall.recommendation != ""

    def test_traceability_links(self):
        plan = self._make_full_plan()
        assert plan.traceability.handoff_id == "h-001"
        assert plan.traceability.recommendation_id == "rec-001"
        assert plan.traceability.assessment_id == "ha-001"

    def test_plan_serialisation_roundtrip(self):
        plan = self._make_full_plan()
        json_data = plan.model_dump(mode="json")
        restored = ResourceDeploymentPlan.model_validate(json_data)
        assert restored.plan_id == plan.plan_id
        assert restored.version == plan.version
