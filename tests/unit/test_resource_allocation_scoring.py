"""Unit tests for scoring algorithm.

Covers:
- Haversine formula at equator/poles/antipodes/known city pairs
- Distance floor enforcement
- Full scoring formula
- Binary capability match
- Type/sub-type compatibility
- Availability factor integration
- Priority weight integration
"""

from __future__ import annotations

import pytest
from resource_allocation.config import ResourceAllocationConfig
from resource_allocation.models import (
    ResourceDemand,
    ResourceInventoryItem,
    ResourceStatus,
    ResourceType,
    UrgencyLevel,
)
from resource_allocation.scoring import (
    check_capability_match,
    check_type_compatibility,
    compute_score,
    estimate_travel_time,
    get_availability_factor,
    haversine_distance,
)


class TestHaversineDistance:
    def test_same_point_is_zero(self):
        assert haversine_distance(0, 0, 0, 0) == 0.0

    def test_equator_90_degrees(self):
        # 90 degrees along equator ≈ 10018 km
        dist = haversine_distance(0, 0, 0, 90)
        assert 10000 < dist < 10050

    def test_pole_to_pole(self):
        # North pole to south pole ≈ 20015 km
        dist = haversine_distance(90, 0, -90, 0)
        assert 20000 < dist < 20050

    def test_antipodal_points(self):
        # Antipodes (diametrically opposite) ≈ 20015 km
        dist = haversine_distance(0, 0, 0, 180)
        assert 20000 < dist < 20050

    def test_sydney_to_melbourne(self):
        # Sydney (-33.8688, 151.2093) to Melbourne (-37.8136, 144.9631) ≈ 714 km
        dist = haversine_distance(-33.8688, 151.2093, -37.8136, 144.9631)
        assert 700 < dist < 730

    def test_symmetry(self):
        d1 = haversine_distance(-33.8688, 151.2093, -37.8136, 144.9631)
        d2 = haversine_distance(-37.8136, 144.9631, -33.8688, 151.2093)
        assert abs(d1 - d2) < 0.001

    def test_very_close_points(self):
        # ~100 meters apart
        dist = haversine_distance(-33.8688, 151.2093, -33.8689, 151.2094)
        assert dist < 0.02  # less than 20 meters


class TestCapabilityMatch:
    def test_empty_required_is_full_match(self):
        assert check_capability_match(["a", "b"], []) == 1.0

    def test_full_match(self):
        assert (
            check_capability_match(
                ["medical_transport", "patient_stabilization"],
                ["medical_transport"],
            )
            == 1.0
        )

    def test_no_match(self):
        assert (
            check_capability_match(
                ["firefighting"],
                ["medical_transport"],
            )
            == 0.0
        )

    def test_partial_match_is_zero(self):
        # Binary: must have ALL required
        assert (
            check_capability_match(
                ["medical_transport"],
                ["medical_transport", "advanced_life_support"],
            )
            == 0.0
        )

    def test_superset_is_full_match(self):
        assert (
            check_capability_match(
                ["a", "b", "c", "d"],
                ["b", "c"],
            )
            == 1.0
        )


class TestTypeCompatibility:
    def test_same_type_and_subtype(self):
        assert check_type_compatibility("vehicle", "ambulance", "vehicle", "ambulance")

    def test_different_type(self):
        assert not check_type_compatibility("vehicle", "ambulance", "personnel", "paramedic")

    def test_same_type_different_subtype(self):
        assert not check_type_compatibility("vehicle", "ambulance", "vehicle", "fire_truck")

    def test_same_type_no_subtype_required(self):
        assert check_type_compatibility("vehicle", "ambulance", "vehicle", "")


class TestAvailabilityFactor:
    def test_available(self):
        config = ResourceAllocationConfig()
        assert get_availability_factor("available", config) == 1.0

    def test_returning(self):
        config = ResourceAllocationConfig()
        assert get_availability_factor("returning", config) == 0.5

    def test_assigned_is_zero(self):
        config = ResourceAllocationConfig()
        assert get_availability_factor("assigned", config) == 0.0

    def test_deployed_is_zero(self):
        config = ResourceAllocationConfig()
        assert get_availability_factor("deployed", config) == 0.0

    def test_unavailable_is_zero(self):
        config = ResourceAllocationConfig()
        assert get_availability_factor("unavailable", config) == 0.0


class TestComputeScore:
    def _make_resource(self, **kwargs):
        defaults = {
            "resource_id": "res-001",
            "resource_type": ResourceType.vehicle,
            "resource_sub_type": "ambulance",
            "capabilities": ["medical_transport"],
            "location": {"lat": -33.8688, "lon": 151.2093},
            "status": ResourceStatus.available,
        }
        defaults.update(kwargs)
        return ResourceInventoryItem(**defaults)

    def _make_demand(self, **kwargs):
        defaults = {
            "demand_id": "dem-001",
            "incident_id": "inc001",
            "source_id": "rec-001",
            "source_type": "coordination_task",
            "resource_type": ResourceType.vehicle,
            "resource_sub_type": "ambulance",
            "required_capabilities": ["medical_transport"],
            "location": {"lat": -33.87, "lon": 151.21},
            "urgency": UrgencyLevel.critical,
        }
        defaults.update(kwargs)
        return ResourceDemand(**defaults)

    def test_full_formula(self):
        config = ResourceAllocationConfig()
        resource = self._make_resource()
        demand = self._make_demand()
        score, rationale = compute_score(resource, demand, config)

        # All factors should be positive
        assert score > 0
        assert rationale["capability_match"] == 1.0
        assert rationale["availability_factor"] == 1.0
        assert rationale["priority_weight"] == 4.0  # critical

    def test_zero_score_when_capability_mismatch(self):
        config = ResourceAllocationConfig()
        resource = self._make_resource(capabilities=["firefighting"])
        demand = self._make_demand(required_capabilities=["medical_transport"])
        score, rationale = compute_score(resource, demand, config)
        assert score == 0.0

    def test_distance_floor_enforcement(self):
        config = ResourceAllocationConfig()
        # Co-located resource and demand
        resource = self._make_resource(location={"lat": -33.87, "lon": 151.21})
        demand = self._make_demand(location={"lat": -33.87, "lon": 151.21})
        score, rationale = compute_score(resource, demand, config)
        # Distance factor should be 1/0.1 = 10.0 (floor applied)
        assert rationale["distance_factor"] == pytest.approx(10.0, rel=0.01)

    def test_returning_resource_half_score(self):
        config = ResourceAllocationConfig()
        resource_avail = self._make_resource(status=ResourceStatus.available)
        resource_return = self._make_resource(resource_id="res-002", status=ResourceStatus.returning)
        demand = self._make_demand()

        score_avail, _ = compute_score(resource_avail, demand, config)
        score_return, _ = compute_score(resource_return, demand, config)
        assert score_return == pytest.approx(score_avail * 0.5, rel=0.01)

    def test_priority_weight_affects_score(self):
        config = ResourceAllocationConfig()
        resource = self._make_resource()
        demand_crit = self._make_demand(urgency=UrgencyLevel.critical)
        demand_low = self._make_demand(urgency=UrgencyLevel.low)

        score_crit, _ = compute_score(resource, demand_crit, config)
        score_low, _ = compute_score(resource, demand_low, config)
        assert score_crit == pytest.approx(score_low * 4.0, rel=0.01)


class TestEstimateTravelTime:
    def test_vehicle_speed(self):
        config = ResourceAllocationConfig()
        time = estimate_travel_time(60, "vehicle", config)
        # 60 km / 60 km/h = 1 hour = 60 min + 10 min mobilisation = 70
        assert time == pytest.approx(70.0, rel=0.01)

    def test_personnel_speed(self):
        config = ResourceAllocationConfig()
        time = estimate_travel_time(40, "personnel", config)
        # 40 km / 40 km/h = 60 min + 15 min mobilisation = 75
        assert time == pytest.approx(75.0, rel=0.01)

    def test_helicopter_speed(self):
        config = ResourceAllocationConfig()
        time = estimate_travel_time(200, "vehicle", config, resource_sub_type="helicopter")
        # 200 km / 200 km/h = 60 min + 5 min mobilisation = 65
        assert time == pytest.approx(65.0, rel=0.01)

    def test_zero_distance(self):
        config = ResourceAllocationConfig()
        time = estimate_travel_time(0, "vehicle", config)
        assert time == pytest.approx(10.0, rel=0.01)  # mobilisation only
