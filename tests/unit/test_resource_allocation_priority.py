"""Unit tests for priority normalisation and demand queue.

Covers:
- AIDR 4-level mapping from Risk Assessment
- Evacuation priority mapping (immediate→critical)
- Three-tier hierarchy ordering
- Demand queue priority-ordered insertion
- Four-level tiebreaking
- Proportional distribution for true ties
"""

from __future__ import annotations

from datetime import UTC, datetime

from resource_allocation.models import (
    PriorityTier,
    ResourceDemand,
    ResourceType,
    UrgencyLevel,
)
from resource_allocation.priority import (
    DemandQueue,
    classify_priority_tier,
    distribute_proportionally,
    normalise_urgency,
)


class TestNormaliseUrgency:
    def test_risk_assessment_critical(self):
        assert normalise_urgency("critical", "risk_assessment") == UrgencyLevel.critical

    def test_risk_assessment_high(self):
        assert normalise_urgency("high", "risk_assessment") == UrgencyLevel.high

    def test_risk_assessment_medium_to_moderate(self):
        assert normalise_urgency("medium", "risk_assessment") == UrgencyLevel.moderate

    def test_risk_assessment_low(self):
        assert normalise_urgency("low", "risk_assessment") == UrgencyLevel.low

    def test_evacuation_immediate_to_critical(self):
        assert normalise_urgency("immediate", "evacuation") == UrgencyLevel.critical

    def test_evacuation_critical(self):
        assert normalise_urgency("critical", "evacuation") == UrgencyLevel.critical

    def test_evacuation_high(self):
        assert normalise_urgency("high", "evacuation") == UrgencyLevel.high

    def test_unknown_defaults_to_moderate(self):
        assert normalise_urgency("unknown", "risk_assessment") == UrgencyLevel.moderate
        assert normalise_urgency("unknown", "evacuation") == UrgencyLevel.moderate


class TestClassifyPriorityTier:
    def test_transport_is_tier1(self):
        context = {"source_type": "transport_requirement"}
        assert classify_priority_tier(context) == PriorityTier.tier_1_life_safety

    def test_medical_is_tier1(self):
        context = {"resource_sub_type": "ambulance"}
        assert classify_priority_tier(context) == PriorityTier.tier_1_life_safety

    def test_evacuation_is_tier1(self):
        context = {"demand_type": "evacuation"}
        assert classify_priority_tier(context) == PriorityTier.tier_1_life_safety

    def test_containment_is_tier3(self):
        context = {"resource_sub_type": "containment"}
        assert classify_priority_tier(context) == PriorityTier.tier_3_environment

    def test_default_is_tier2(self):
        context = {"resource_sub_type": "fire_truck"}
        assert classify_priority_tier(context) == PriorityTier.tier_2_property


class TestDemandQueue:
    def _make_demand(self, demand_id, tier, urgency, created_at=None):
        return ResourceDemand(
            demand_id=demand_id,
            incident_id="inc001",
            source_id="rec-001",
            source_type="coordination_task",
            resource_type=ResourceType.vehicle,
            resource_sub_type="ambulance",
            priority_tier=tier,
            urgency=urgency,
            created_at=created_at or datetime.now(UTC),
        )

    def test_tier_ordering(self):
        queue = DemandQueue()
        d1 = self._make_demand("d1", PriorityTier.tier_3_environment, UrgencyLevel.critical)
        d2 = self._make_demand("d2", PriorityTier.tier_1_life_safety, UrgencyLevel.critical)
        d3 = self._make_demand("d3", PriorityTier.tier_2_property, UrgencyLevel.critical)

        queue.insert(d1)
        queue.insert(d2)
        queue.insert(d3)

        result = queue.to_list()
        assert result[0].demand_id == "d2"  # Tier 1 first
        assert result[1].demand_id == "d3"  # Tier 2 second
        assert result[2].demand_id == "d1"  # Tier 3 last

    def test_urgency_ordering_within_tier(self):
        queue = DemandQueue()
        d1 = self._make_demand("d1", PriorityTier.tier_1_life_safety, UrgencyLevel.low)
        d2 = self._make_demand("d2", PriorityTier.tier_1_life_safety, UrgencyLevel.critical)
        d3 = self._make_demand("d3", PriorityTier.tier_1_life_safety, UrgencyLevel.high)

        queue.insert(d1)
        queue.insert(d2)
        queue.insert(d3)

        result = queue.to_list()
        assert result[0].demand_id == "d2"  # critical first
        assert result[1].demand_id == "d3"  # high second
        assert result[2].demand_id == "d1"  # low last

    def test_queue_length(self):
        queue = DemandQueue()
        assert len(queue) == 0
        queue.insert(self._make_demand("d1", PriorityTier.tier_1_life_safety, UrgencyLevel.critical))
        assert len(queue) == 1

    def test_iteration(self):
        queue = DemandQueue()
        queue.insert(self._make_demand("d1", PriorityTier.tier_1_life_safety, UrgencyLevel.critical))
        queue.insert(self._make_demand("d2", PriorityTier.tier_2_property, UrgencyLevel.low))

        demands = list(queue)
        assert len(demands) == 2
        assert demands[0].demand_id == "d1"


class TestDistributeProportionally:
    def test_equal_distribution(self):
        demands = [
            ResourceDemand(
                demand_id="d1",
                incident_id="inc1",
                source_id="r1",
                source_type="coordination_task",
                resource_type=ResourceType.vehicle,
                resource_sub_type="bus",
                quantity=5,
            ),
            ResourceDemand(
                demand_id="d2",
                incident_id="inc2",
                source_id="r2",
                source_type="coordination_task",
                resource_type=ResourceType.vehicle,
                resource_sub_type="bus",
                quantity=5,
            ),
        ]
        result = distribute_proportionally(demands, 10, ["inc1", "inc2"])
        assert result["inc1"] == 5
        assert result["inc2"] == 5

    def test_proportional_distribution(self):
        demands = [
            ResourceDemand(
                demand_id="d1",
                incident_id="inc1",
                source_id="r1",
                source_type="coordination_task",
                resource_type=ResourceType.vehicle,
                resource_sub_type="bus",
                quantity=6,
            ),
            ResourceDemand(
                demand_id="d2",
                incident_id="inc2",
                source_id="r2",
                source_type="coordination_task",
                resource_type=ResourceType.vehicle,
                resource_sub_type="bus",
                quantity=4,
            ),
        ]
        result = distribute_proportionally(demands, 10, ["inc1", "inc2"])
        assert result["inc1"] == 6
        assert result["inc2"] == 4

    def test_zero_available(self):
        result = distribute_proportionally([], 0, ["inc1"])
        assert result["inc1"] == 0

    def test_empty_incidents(self):
        result = distribute_proportionally([], 10, [])
        assert result == {}
