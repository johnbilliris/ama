"""Tests for shared assembly-area destination allocation."""

from evacuation.destinations import DestinationAllocator
from evacuation.models import EvacuationRoute, VehicleSuitability

from tests.unit.test_evacuation_router import (
    _assembly_area,
    _edge,
    _micro_network,
)


def _route(route_id, zone, destination, path, distance=1):
    return EvacuationRoute(
        route_id=route_id,
        zone_id=str(zone),
        origin_node_id="origin",
        assembly_area_id=destination,
        route_name=route_id,
        distance_km=distance,
        total_distance_km=distance,
        estimated_travel_minutes=distance * 2,
        estimated_travel_time_loaded_min=distance * 2,
        capacity_vehicles_per_hour=100,
        waypoints=path,
        node_path=["origin", "safe" if destination == "safe-aa" else "danger"],
        vehicle_suitability=VehicleSuitability(accessible=True),
    )


class TestDestinationAllocator:
    def test_vulnerable_population_uses_farther_accessible_area(self, tmp_path):
        network = _micro_network(
            tmp_path,
            [
                _edge("near", "origin", "danger", 1),
                _edge("far", "origin", "safe", 2),
            ],
            [
                _assembly_area(
                    "near-aa",
                    "danger",
                    accessibility_features=[],
                ),
                _assembly_area("safe-aa", "safe"),
            ],
        )
        routes = [
            _route("near-route", 1, "near-aa", ["near"], 1),
            _route("safe-route", 1, "safe-aa", ["far"], 2),
        ]

        result = DestinationAllocator(network).allocate(
            routes,
            {1: 40},
            {1: 40},
        )

        assert routes[0].allocated_population == 0
        assert routes[1].allocated_population == 40
        assert result.allocations[0].assembly_area_id == "safe-aa"
        assert result.allocations[0].assigned_vulnerable_population == 40

    def test_full_near_area_uses_farther_available_area(self, tmp_path):
        network = _micro_network(
            tmp_path,
            [
                _edge("near", "origin", "danger", 1),
                _edge("far", "origin", "safe", 2),
            ],
            [
                _assembly_area(
                    "near-aa",
                    "danger",
                    capacity_persons=100,
                    current_occupancy_persons=100,
                ),
                _assembly_area(
                    "safe-aa",
                    "safe",
                    capacity_persons=100,
                ),
            ],
        )
        routes = [
            _route("near-route", 1, "near-aa", ["near"], 1),
            _route("safe-route", 1, "safe-aa", ["far"], 2),
        ]

        result = DestinationAllocator(network).allocate(routes, {1: 80})

        assert result.allocations[0].assembly_area_id == "safe-aa"
        assert result.allocations[0].assigned_population == 80
        assert result.unresolved == []

    def test_all_full_is_explicit_unresolved_demand(self, tmp_path):
        network = _micro_network(
            tmp_path,
            [_edge("near", "origin", "danger", 1)],
            [
                _assembly_area(
                    "near-aa",
                    "danger",
                    capacity_persons=50,
                    current_occupancy_persons=50,
                )
            ],
        )
        routes = [_route("near-route", 1, "near-aa", ["near"])]

        result = DestinationAllocator(network).allocate(routes, {1: 40})

        assert routes[0].allocated_population == 0
        assert result.unallocated_population_by_zone == {1: 40}
        assert result.unresolved[0].reason == "capacity_exhausted"

    def test_unknown_occupancy_is_not_assumed_empty(self, tmp_path):
        network = _micro_network(
            tmp_path,
            [_edge("near", "origin", "danger", 1)],
            [
                _assembly_area(
                    "near-aa",
                    "danger",
                    current_occupancy_persons=None,
                )
            ],
        )
        routes = [_route("near-route", 1, "near-aa", ["near"])]

        result = DestinationAllocator(network).allocate(routes, {1: 40})

        assert result.unresolved[0].reason == "capacity_unverified"
        assert result.allocations == []

    def test_wrong_zone_area_is_not_allocated(self, tmp_path):
        network = _micro_network(
            tmp_path,
            [_edge("near", "origin", "danger", 1)],
            [_assembly_area("near-aa", "danger", assigned_zones=[2])],
        )
        routes = [_route("near-route", 1, "near-aa", ["near"])]

        result = DestinationAllocator(network).allocate(routes, {1: 40})

        assert result.unresolved[0].reason == "no_reachable_destination"
        assert routes[0].allocated_population == 0

    def test_absent_assembly_registry_is_explicit_unresolved_demand(self, tmp_path):
        network = _micro_network(
            tmp_path,
            [_edge("road", "origin", "safe", 1)],
            [],
        )

        result = DestinationAllocator(network).allocate([], {1: 40}, {1: 10})

        assert result.allocations == []
        assert result.unallocated_population_by_zone == {1: 40}
        assert result.unresolved[0].reason == "no_reachable_destination"
        assert sum(item.population for item in result.unresolved) == 40

    def test_cross_zone_capacity_is_consumed_in_priority_order(self, tmp_path):
        network = _micro_network(
            tmp_path,
            [_edge("shared", "origin", "safe", 1)],
            [
                _assembly_area(
                    "safe-aa",
                    "safe",
                    capacity_persons=100,
                    assigned_zones=[1, 2],
                )
            ],
        )
        routes = [
            _route("zone-1", 1, "safe-aa", ["shared"]),
            _route("zone-2", 2, "safe-aa", ["shared"]),
        ]

        result = DestinationAllocator(network).allocate(
            routes,
            {1: 80, 2: 80},
        )

        assert routes[0].allocated_population == 80
        assert routes[1].allocated_population == 20
        assert result.unallocated_population_by_zone == {1: 0, 2: 60}
        assert result.unresolved[0].zone_number == 2
        assert result.unresolved[0].reason == "capacity_exhausted"
