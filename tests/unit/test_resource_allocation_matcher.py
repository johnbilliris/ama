"""Unit tests for resource-demand matching.

Covers:
- Greedy assignment (highest-scoring to highest-priority)
- Partial allocation with shortfall details
- Demand fulfilment status tracking
- Tie-breaking (capability count, alphabetical)
- Empty inventory handling
- Cross-incident contention detection
"""

from __future__ import annotations

from resource_allocation.matcher import ResourceMatcher
from resource_allocation.models import (
    PriorityTier,
    ResourceDemand,
    ResourceInventoryItem,
    ResourceStatus,
    ResourceType,
    UrgencyLevel,
)


def _make_resource(resource_id, lat=-33.87, lon=151.21, capabilities=None, status="available", sub_type="ambulance"):
    return ResourceInventoryItem(
        resource_id=resource_id,
        resource_type=ResourceType.vehicle,
        resource_sub_type=sub_type,
        capabilities=capabilities or ["medical_transport"],
        location={"lat": lat, "lon": lon},
        status=ResourceStatus(status),
    )


def _make_demand(
    demand_id,
    quantity=1,
    urgency=UrgencyLevel.critical,
    lat=-33.87,
    lon=151.21,
    capabilities=None,
    sub_type="ambulance",
    incident_id="inc001",
):
    return ResourceDemand(
        demand_id=demand_id,
        incident_id=incident_id,
        source_id="rec-001",
        source_type="coordination_task",
        resource_type=ResourceType.vehicle,
        resource_sub_type=sub_type,
        required_capabilities=capabilities or ["medical_transport"],
        quantity=quantity,
        location={"lat": lat, "lon": lon},
        urgency=urgency,
        priority_tier=PriorityTier.tier_1_life_safety,
    )


class TestGreedyAssignment:
    def test_excludes_incompatible_subtypes_from_mixed_pool(self):
        matcher = ResourceMatcher()
        resources = [
            _make_resource("near-minibus", lat=-33.871, lon=151.211, sub_type="minibus"),
            _make_resource("far-ambulance", lat=-34.0, lon=151.5, sub_type="ambulance"),
        ]
        demands = [_make_demand("ambulance-demand", sub_type="ambulance")]

        assignments, shortfalls = matcher.match_demands(demands, resources)

        assert len(shortfalls) == 0
        assert [assignment.resource_id for assignment in assignments] == ["far-ambulance"]

    def test_assigns_closest_resource(self):
        matcher = ResourceMatcher()
        resources = [
            _make_resource("far", lat=-34.0, lon=151.5),
            _make_resource("close", lat=-33.871, lon=151.211),
        ]
        demands = [_make_demand("d1")]

        assignments, shortfalls = matcher.match_demands(demands, resources)
        assert len(assignments) == 1
        assert assignments[0].resource_id == "close"
        assert len(shortfalls) == 0

    def test_multiple_demands(self):
        matcher = ResourceMatcher()
        resources = [
            _make_resource("r1", lat=-33.871, lon=151.211),
            _make_resource("r2", lat=-34.0, lon=151.5),
        ]
        demands = [
            _make_demand("d1", quantity=1),
            _make_demand("d2", quantity=1),
        ]

        assignments, shortfalls = matcher.match_demands(demands, resources)
        assert len(assignments) == 2
        assigned_ids = {a.resource_id for a in assignments}
        assert assigned_ids == {"r1", "r2"}

    def test_resource_not_reused(self):
        matcher = ResourceMatcher()
        resources = [_make_resource("r1")]
        demands = [
            _make_demand("d1", quantity=1),
            _make_demand("d2", quantity=1),
        ]

        assignments, shortfalls = matcher.match_demands(demands, resources)
        assert len(assignments) == 1
        assert len(shortfalls) == 1


class TestPartialAllocation:
    def test_partial_allocation_generates_shortfall(self):
        matcher = ResourceMatcher()
        resources = [_make_resource("r1")]
        demands = [_make_demand("d1", quantity=3)]

        assignments, shortfalls = matcher.match_demands(demands, resources)
        assert len(assignments) == 1
        assert len(shortfalls) == 1
        assert shortfalls[0].quantity_requested == 3
        assert shortfalls[0].quantity_assigned == 1
        assert shortfalls[0].quantity_unmet == 2

    def test_every_demand_appears_in_output(self):
        matcher = ResourceMatcher()
        resources = [_make_resource("r1")]
        demands = [
            _make_demand("d1", quantity=1),
            _make_demand("d2", quantity=1),
        ]

        assignments, shortfalls = matcher.match_demands(demands, resources)
        all_demand_ids = {a.demand_id for a in assignments} | {s.demand_id for s in shortfalls}
        assert "d1" in all_demand_ids
        assert "d2" in all_demand_ids

    def test_fully_met_demand_status(self):
        matcher = ResourceMatcher()
        resources = [_make_resource("r1")]
        demands = [_make_demand("d1", quantity=1)]

        assignments, shortfalls = matcher.match_demands(demands, resources)
        assert demands[0].fulfilment_status == "fully_met"

    def test_unmet_demand_status(self):
        matcher = ResourceMatcher()
        resources = []
        demands = [_make_demand("d1", quantity=1)]

        assignments, shortfalls = matcher.match_demands(demands, resources)
        assert demands[0].fulfilment_status == "unmet"
        assert len(shortfalls) == 1


class TestTieBreaking:
    def test_higher_capability_count_wins(self):
        matcher = ResourceMatcher()
        # Two resources at same location, different capability counts
        r1 = _make_resource("r1", capabilities=["medical_transport"])
        r2 = _make_resource("r2", capabilities=["medical_transport", "advanced_life_support"])

        demands = [_make_demand("d1", capabilities=["medical_transport"])]
        assignments, _ = matcher.match_demands(demands, [r1, r2])
        assert assignments[0].resource_id == "r2"  # more capabilities

    def test_alphabetical_id_breaks_tie(self):
        matcher = ResourceMatcher()
        r1 = _make_resource("b-resource", capabilities=["medical_transport"])
        r2 = _make_resource("a-resource", capabilities=["medical_transport"])

        demands = [_make_demand("d1", capabilities=["medical_transport"])]
        assignments, _ = matcher.match_demands(demands, [r1, r2])
        assert assignments[0].resource_id == "a-resource"


class TestEmptyInventory:
    def test_all_demands_unmet(self):
        matcher = ResourceMatcher()
        demands = [
            _make_demand("d1", quantity=2),
            _make_demand("d2", quantity=1),
        ]

        assignments, shortfalls = matcher.match_demands(demands, [])
        assert len(assignments) == 0
        assert len(shortfalls) == 2
        for s in shortfalls:
            assert s.quantity_assigned == 0


class TestCrossIncidentContention:
    def test_detects_contention(self):
        matcher = ResourceMatcher()
        resources = [_make_resource("r1")]
        demands = [
            _make_demand("d1", incident_id="inc001"),
            _make_demand("d2", incident_id="inc002"),
        ]

        contentions = matcher.detect_cross_incident_contention(demands, resources)
        assert len(contentions) == 1
        assert set(contentions[0]["competing_incidents"]) == {"inc001", "inc002"}

    def test_no_contention_single_incident(self):
        matcher = ResourceMatcher()
        resources = [_make_resource("r1")]
        demands = [
            _make_demand("d1", incident_id="inc001"),
            _make_demand("d2", incident_id="inc001"),
        ]

        contentions = matcher.detect_cross_incident_contention(demands, resources)
        assert len(contentions) == 0
