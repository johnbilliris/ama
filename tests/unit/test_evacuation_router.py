"""Tests for evacuation.router — Dijkstra, closures, multi-path, congestion (T028)."""

import json
from datetime import UTC, datetime

import pytest
from evacuation.config import EvacuationConfig
from evacuation.models import HazardRoutingContext, RoutingMode
from evacuation.road_network import RoadNetworkLoader
from evacuation.router import RouteComputer

SAMPLE_FILE = "data/road-networks/far-north-qld-sample.json"


@pytest.fixture
def loaded_network():
    loader = RoadNetworkLoader()
    loader.load(SAMPLE_FILE)
    return loader


@pytest.fixture
def route_computer(loaded_network):
    return RouteComputer(road_network=loaded_network)


def _edge(edge_id, start, end, distance, **overrides):
    nodes = {
        "origin": [0, 0],
        "danger": [1, 0],
        "safe": [0, 1],
        "destination": [1, 1],
        "west": [-1, 0],
    }
    document = {
        "id": edge_id,
        "from_node": start,
        "to_node": end,
        "name": edge_id,
        "distance_km": distance,
        "capacity_vehicles_per_hour": 1000,
        "surface_type": "sealed",
        "accessibility_features": ["wheelchair_accessible"],
        "closure_status": "open",
        "closure_reason": None,
        "geometry": {
            "type": "LineString",
            "coordinates": [nodes[start], nodes[end]],
        },
        "elevation_m": 100,
        "coastal_exposure": False,
        "flood_exposure": False,
        "tsunami_inundation_exposure": False,
        "earthquake_damage_status": "none",
    }
    document.update(overrides)
    return document


def _assembly_area(area_id="safe-aa", node_id="destination", **overrides):
    coordinates = {
        "destination": {"lng": 1, "lat": 1},
        "danger": {"lng": 1, "lat": 0},
        "safe": {"lng": 0, "lat": 1},
    }
    document = {
        "assembly_area_id": area_id,
        "name": area_id,
        "coordinates": coordinates[node_id],
        "capacity_persons": 1000,
        "current_occupancy_persons": 0,
        "accessibility_features": ["wheelchair_accessible"],
        "assigned_zones": [1, 2, 3],
        "node_id": node_id,
        "elevation_m": 100,
        "coastal_exposure": False,
        "flood_exposure": False,
        "tsunami_inundation_exposure": False,
        "shelter_types": ["cyclone_shelter"],
        "structural_status": "safe",
    }
    document.update(overrides)
    return document


def _micro_network(tmp_path, edges, assembly_areas=None):
    nodes = [
        {"id": "origin", "name": "Origin", "coordinates": {"lng": 0, "lat": 0}},
        {"id": "danger", "name": "Danger", "coordinates": {"lng": 1, "lat": 0}},
        {"id": "safe", "name": "Safe", "coordinates": {"lng": 0, "lat": 1}},
        {"id": "destination", "name": "Destination", "coordinates": {"lng": 1, "lat": 1}},
        {"id": "west", "name": "West", "coordinates": {"lng": -1, "lat": 0}},
    ]
    document = {
        "metadata": {
            "version": "test",
            "region": "micrograph",
            "coordinate_system": "WGS84",
            "last_updated": datetime.now(UTC).isoformat(),
        },
        "nodes": nodes,
        "edges": edges,
        "assembly_areas": ([_assembly_area()] if assembly_areas is None else assembly_areas),
    }
    path = tmp_path / "road-network.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    network = RoadNetworkLoader()
    network.load(str(path))
    return network


def _hazard_context(hazard_type, **overrides):
    values = {"hazard_types": [hazard_type]}
    if hazard_type == "bushfire":
        values.update(
            {
                "bushfire_exclusion_areas": [
                    {
                        "type": "Polygon",
                        "coordinates": [[[0.9, -0.1], [1.1, -0.1], [1.1, 0.1], [0.9, 0.1], [0.9, -0.1]]],
                    }
                ],
                "wind_from_degrees": 0,
            }
        )
    values.update(overrides)
    return HazardRoutingContext(**values)


# ---------------------------------------------------------------------------
# Dijkstra shortest path on simple graph
# ---------------------------------------------------------------------------


class TestDijkstraShortestPath:
    def test_finds_path_between_connected_nodes(self, loaded_network, route_computer):
        """Should find at least one route from a zone node to an assembly area."""
        # Find an assembly area node
        aa_node_ids = loaded_network.get_assembly_area_node_ids()
        # T-AA06 — replace ``len(...) > 0`` with explicit invariant:
        # a road network with no assembly areas is unusable for the
        # evacuation router, so the loader MUST provide ≥1.
        assert len(aa_node_ids) >= 1, "loaded network has zero assembly-area nodes — router cannot run"

        # Pick a non-assembly-area node as origin
        all_nodes = loaded_network.get_all_nodes()
        origin = None
        for node in all_nodes:
            if node.id not in aa_node_ids:
                origin = node.id
                break
        assert origin is not None

        routes = route_computer.compute_routes(
            origin_nodes=[origin],
            zone_number=1,
            population=1000,
            hazard_type="bushfire",
        )
        # T-AA06 — explicit boundary: at least one route must exist OR
        # the test fixture is broken. Carry origin id in the assertion
        # message for diagnostics.
        assert len(routes) >= 1, f"no routes computed from origin {origin}"

    def test_route_has_positive_distance(self, loaded_network, route_computer):
        aa_node_ids = loaded_network.get_assembly_area_node_ids()
        all_nodes = loaded_network.get_all_nodes()
        origin = next(n.id for n in all_nodes if n.id not in aa_node_ids)

        routes = route_computer.compute_routes(
            origin_nodes=[origin],
            zone_number=1,
            population=100,
        )
        if routes:
            assert routes[0].distance_km > 0

    def test_route_has_travel_time(self, loaded_network, route_computer):
        aa_node_ids = loaded_network.get_assembly_area_node_ids()
        all_nodes = loaded_network.get_all_nodes()
        origin = next(n.id for n in all_nodes if n.id not in aa_node_ids)

        routes = route_computer.compute_routes(
            origin_nodes=[origin],
            zone_number=1,
            population=100,
        )
        if routes:
            assert routes[0].estimated_travel_minutes >= 0

    def test_route_fields_populated(self, loaded_network, route_computer):
        aa_node_ids = loaded_network.get_assembly_area_node_ids()
        all_nodes = loaded_network.get_all_nodes()
        origin = next(n.id for n in all_nodes if n.id not in aa_node_ids)

        routes = route_computer.compute_routes(
            origin_nodes=[origin],
            zone_number=2,
            population=500,
        )
        if routes:
            r = routes[0]
            assert r.route_id.startswith("route-")
            assert r.zone_id == "2"
            assert r.assembly_area_id != ""
            assert r.route_name != ""
            assert r.origin_zone == 2
            assert r.destination_assembly_area == r.assembly_area_id
            assert r.path == r.waypoints
            assert r.total_distance_km == r.distance_km
            assert r.estimated_travel_time_normal_min > 0
            assert r.estimated_travel_time_loaded_min > r.estimated_travel_time_normal_min
            assert r.estimated_utilisation_pct == r.uncapped_utilisation_pct

    def test_node_and_edge_paths_are_connected(self, loaded_network, route_computer):
        origin = next(node.id for node in loaded_network.get_all_nodes() if not node.is_assembly_area)
        route = route_computer.compute_routes([origin], 1, 100)[0]

        assert len(route.node_path) == len(route.path) + 1
        for index, edge_id in enumerate(route.path):
            edge = loaded_network.get_edge(edge_id)
            assert edge is not None
            assert {route.node_path[index], route.node_path[index + 1]} == {
                edge.from_node,
                edge.to_node,
            }

    def test_vehicle_suitability_is_structured(self, tmp_path):
        network = _micro_network(
            tmp_path,
            [
                _edge(
                    "unsealed",
                    "origin",
                    "safe",
                    1,
                    surface_type="unsealed",
                    accessibility_features=[],
                )
            ],
            [_assembly_area("safe-aa", "safe")],
        )

        route = RouteComputer(
            network,
            hazard_context=_hazard_context("earthquake"),
        ).compute_routes(["origin"], 1, 10, "earthquake")[0]

        assert route.vehicle_suitability.standard is True
        assert route.vehicle_suitability.heavy is False
        assert route.vehicle_suitability.accessible is False
        assert "heavy=no" not in route.route_name

    def test_route_identity_is_stable_and_bound_to_scope_and_path(self, tmp_path):
        network = _micro_network(
            tmp_path,
            [
                _edge("path-1", "origin", "safe", 1),
                _edge("path-2", "origin", "danger", 1),
            ],
            [
                _assembly_area("safe-aa", "safe"),
                _assembly_area("danger-aa", "danger"),
            ],
        )
        context = _hazard_context(
            "earthquake",
            incident_scope_key="tenant-a:inc-1",
        )

        first = RouteComputer(network, hazard_context=context).compute_routes(["origin"], 1, 10, "earthquake")
        second = RouteComputer(network, hazard_context=context).compute_routes(["origin"], 1, 10, "earthquake")
        foreign = RouteComputer(
            network,
            hazard_context=_hazard_context(
                "earthquake",
                incident_scope_key="tenant-b:inc-1",
            ),
        ).compute_routes(["origin"], 1, 10, "earthquake")

        assert [route.route_id for route in first] == [route.route_id for route in second]
        assert len({route.route_id for route in first}) == len(first)
        assert {route.route_id for route in first}.isdisjoint(route.route_id for route in foreign)

    def test_equal_weight_prefers_lower_current_load_then_path(self, tmp_path):
        network = _micro_network(
            tmp_path,
            [
                _edge(
                    "busy-1",
                    "origin",
                    "danger",
                    1,
                    current_traffic_load_vehicles_per_hour=90,
                ),
                _edge(
                    "busy-2",
                    "danger",
                    "destination",
                    1,
                    current_traffic_load_vehicles_per_hour=90,
                ),
                _edge("quiet-1", "origin", "safe", 1),
                _edge("quiet-2", "safe", "destination", 1),
            ],
        )

        route = RouteComputer(
            network,
            hazard_context=_hazard_context("earthquake"),
        ).compute_routes(["origin"], 1, 10, "earthquake")[0]

        assert route.path == ["quiet-1", "quiet-2"]

    def test_equal_cost_load_and_distance_prefer_lexical_edge_path(self, tmp_path):
        network = _micro_network(
            tmp_path,
            [
                _edge("z-path-1", "origin", "danger", 1),
                _edge("z-path-2", "danger", "destination", 1),
                _edge("a-path-1", "origin", "safe", 1),
                _edge("a-path-2", "safe", "destination", 1),
            ],
        )

        route = RouteComputer(
            network,
            hazard_context=_hazard_context("earthquake"),
        ).compute_routes(["origin"], 1, 10, "earthquake")[0]

        assert route.path == ["a-path-1", "a-path-2"]


# ---------------------------------------------------------------------------
# Closed road exclusion
# ---------------------------------------------------------------------------


class TestClosedRoadExclusion:
    def test_closed_edges_excluded(self, loaded_network, route_computer):
        """Routes should not traverse closed edges."""
        # Close some edges
        edges = loaded_network.get_all_edges()
        for edge in edges[:5]:
            loaded_network.apply_closure(edge.id, "flood_cut")

        aa_node_ids = loaded_network.get_assembly_area_node_ids()
        all_nodes = loaded_network.get_all_nodes()
        origin = next(n.id for n in all_nodes if n.id not in aa_node_ids)

        routes = route_computer.compute_routes(
            origin_nodes=[origin],
            zone_number=1,
            population=100,
        )
        closed_ids = {e.id for e in edges[:5]}
        for route in routes:
            # waypoints contain edge IDs for this route
            for wp in route.waypoints:
                assert wp not in closed_ids

    def test_excluded_edges_parameter(self, loaded_network, route_computer):
        """Explicitly excluded edges should not appear in route waypoints."""
        edges = loaded_network.get_all_edges()
        exclude_set = {edges[0].id, edges[1].id}

        aa_node_ids = loaded_network.get_assembly_area_node_ids()
        all_nodes = loaded_network.get_all_nodes()
        origin = next(n.id for n in all_nodes if n.id not in aa_node_ids)

        routes = route_computer.compute_routes(
            origin_nodes=[origin],
            zone_number=1,
            population=100,
            excluded_edge_ids=exclude_set,
        )
        for route in routes:
            for wp in route.waypoints:
                assert wp not in exclude_set

    def test_all_exclusions_are_reported_without_truncation(self, tmp_path):
        blocked_edges = [_edge(f"blocked-{index:02d}", "origin", "danger", 1) for index in range(12)]
        network = _micro_network(
            tmp_path,
            blocked_edges + [_edge("safe", "origin", "safe", 2)],
            [_assembly_area("safe-aa", "safe")],
        )
        blocked_ids = {edge["id"] for edge in blocked_edges}
        computer = RouteComputer(
            network,
            hazard_context=_hazard_context("earthquake"),
        )

        route = computer.compute_routes(
            ["origin"],
            1,
            10,
            "earthquake",
            excluded_edge_ids=blocked_ids,
        )[0]

        assert len(route.excluded_roads) == 12
        assert {road.edge_id for road in route.excluded_roads} == blocked_ids
        assert all(road.closure_reason.value == "unspecified" for road in route.excluded_roads)
        assert all(
            road.exclusion_reason == "Excluded without a reported closure cause" for road in route.excluded_roads
        )

    def test_zero_routes_retain_complete_exclusion_inventory(self, tmp_path):
        network = _micro_network(
            tmp_path,
            [_edge("only-road", "origin", "safe", 1)],
            [_assembly_area("safe-aa", "safe")],
        )
        computer = RouteComputer(
            network,
            hazard_context=_hazard_context("earthquake"),
        )

        routes = computer.compute_routes(
            ["origin"],
            1,
            10,
            "earthquake",
            excluded_edge_ids={"only-road"},
        )

        assert routes == []
        assert [road.edge_id for road in computer.excluded_roads] == ["only-road"]


class TestHazardSpecificRouting:
    @pytest.mark.parametrize(
        ("hazard_type", "danger_overrides"),
        [
            ("bushfire", {}),
            ("cyclone", {"coastal_exposure": True}),
            ("flood", {"flood_exposure": True}),
            ("earthquake", {"earthquake_damage_status": "confirmed"}),
            ("tsunami", {"tsunami_inundation_exposure": True}),
        ],
    )
    def test_short_dangerous_path_is_excluded_for_each_hazard(
        self,
        tmp_path,
        hazard_type,
        danger_overrides,
    ):
        network = _micro_network(
            tmp_path,
            [
                _edge("danger-1", "origin", "danger", 1, **danger_overrides),
                _edge("danger-2", "danger", "destination", 1, **danger_overrides),
                _edge("safe-1", "origin", "safe", 2),
                _edge("safe-2", "safe", "destination", 2),
            ],
        )
        computer = RouteComputer(
            network,
            hazard_context=_hazard_context(hazard_type),
        )

        routes = computer.compute_routes(
            ["origin"],
            1,
            100,
            hazard_type,
        )

        assert routes
        assert routes[0].waypoints == ["safe-1", "safe-2"]
        excluded = {road.road_id: road for road in routes[0].excluded_roads}
        assert excluded["danger-1"].source_hazard_type == hazard_type
        assert excluded["danger-1"].exclusion_reason
        assert routes[0].routing_mode == RoutingMode.hazard_aware

    @pytest.mark.parametrize(
        ("hazard_type", "unsafe_overrides"),
        [
            ("bushfire", {}),
            ("cyclone", {"coastal_exposure": True}),
            ("flood", {"flood_exposure": True}),
            ("earthquake", {"structural_status": "unsafe"}),
            ("tsunami", {"tsunami_inundation_exposure": True}),
        ],
    )
    def test_unsafe_destination_is_screened_for_each_hazard(
        self,
        tmp_path,
        hazard_type,
        unsafe_overrides,
    ):
        context = _hazard_context(hazard_type)
        if hazard_type == "bushfire":
            context = _hazard_context(
                hazard_type,
                bushfire_exclusion_areas=[
                    {
                        "type": "Polygon",
                        "coordinates": [[[0.9, -0.1], [1.1, -0.1], [1.1, 0.1], [0.9, 0.1], [0.9, -0.1]]],
                    }
                ],
            )
        network = _micro_network(
            tmp_path,
            [
                _edge("to-unsafe", "origin", "danger", 1),
                _edge("to-safe", "origin", "safe", 2),
            ],
            [
                _assembly_area("unsafe-aa", "danger", **unsafe_overrides),
                _assembly_area("safe-aa", "safe"),
            ],
        )
        computer = RouteComputer(network, hazard_context=context)

        routes = computer.compute_routes(["origin"], 1, 100, hazard_type)

        assert {route.assembly_area_id for route in routes} == {"safe-aa"}
        assert computer.destination_exclusions[0].assembly_area_id == "unsafe-aa"
        assert computer.destination_exclusions[0].source_hazard_type == hazard_type

    @pytest.mark.parametrize(
        ("hazard_type", "danger_overrides"),
        [
            ("cyclone", {"elevation_m": 0}),
            ("flood", {"elevation_m": 0}),
            ("earthquake", {"earthquake_damage_status": "suspected"}),
            ("tsunami", {"elevation_m": 0}),
        ],
    )
    def test_longer_lower_risk_path_is_preferred(
        self,
        tmp_path,
        hazard_type,
        danger_overrides,
    ):
        network = _micro_network(
            tmp_path,
            [
                _edge("danger-1", "origin", "danger", 1, **danger_overrides),
                _edge("danger-2", "danger", "destination", 1, **danger_overrides),
                _edge("safe-1", "origin", "safe", 1.5),
                _edge("safe-2", "safe", "destination", 1.5),
            ],
        )
        computer = RouteComputer(
            network,
            hazard_context=_hazard_context(hazard_type),
        )

        routes = computer.compute_routes(["origin"], 1, 100, hazard_type)

        assert routes[0].waypoints == ["safe-1", "safe-2"]
        assert "3.00 km" in routes[0].selection_rationale
        assert "Assigned 100 people" in routes[0].selection_rationale
        assert routes[0].hazard_preference_evidence == []
        assert "Applied preferences" not in routes[0].selection_rationale

    def test_bushfire_wind_reversal_changes_selected_path(self, tmp_path):
        network = _micro_network(
            tmp_path,
            [
                _edge("east-1", "origin", "danger", 1),
                _edge("east-2", "danger", "destination", 1),
                _edge("west-1", "origin", "west", 1),
                _edge("west-2", "west", "destination", 1),
            ],
        )
        remote_area = {
            "type": "Polygon",
            "coordinates": [[[10, 10], [11, 10], [11, 11], [10, 11], [10, 10]]],
        }

        west_wind = RouteComputer(
            network,
            hazard_context=_hazard_context(
                "bushfire",
                bushfire_exclusion_areas=[remote_area],
                wind_from_degrees=270,
            ),
        ).compute_routes(["origin"], 1, 100, "bushfire")
        east_wind = RouteComputer(
            network,
            hazard_context=_hazard_context(
                "bushfire",
                bushfire_exclusion_areas=[remote_area],
                wind_from_degrees=90,
            ),
        ).compute_routes(["origin"], 1, 100, "bushfire")

        assert west_wind[0].waypoints == ["west-1", "west-2"]
        assert east_wind[0].waypoints == ["east-1", "east-2"]

    def test_missing_reference_attributes_are_explicitly_degraded(
        self,
        loaded_network,
    ):
        computer = RouteComputer(
            loaded_network,
            hazard_context=HazardRoutingContext(hazard_types=["tsunami"]),
        )
        origin = next(node.id for node in loaded_network.get_all_nodes() if not node.is_assembly_area)

        routes = computer.compute_routes([origin], 1, 100, "tsunami")

        assert computer.routing_mode == RoutingMode.hazard_constrained_degraded
        assert computer.hazard_data_gaps == [
            "tsunami.destination_coastal_inundation_elevation",
            "tsunami.edge_coastal_inundation_elevation",
        ]
        assert all(route.hazard_data_gaps for route in routes)

    def test_any_active_hazard_can_exclude_a_shared_edge(self, tmp_path):
        network = _micro_network(
            tmp_path,
            [
                _edge(
                    "shared-risk-1",
                    "origin",
                    "danger",
                    1,
                    flood_exposure=True,
                ),
                _edge(
                    "shared-risk-2",
                    "danger",
                    "destination",
                    1,
                    flood_exposure=True,
                ),
                _edge("safe-1", "origin", "safe", 2),
                _edge("safe-2", "safe", "destination", 2),
            ],
        )
        context = HazardRoutingContext(
            hazard_types=["earthquake", "flood"],
        )
        computer = RouteComputer(network, hazard_context=context)

        routes = computer.compute_routes(["origin"], 1, 100, "flood")

        assert routes[0].waypoints == ["safe-1", "safe-2"]
        shared = next(road for road in routes[0].excluded_roads if road.road_id == "shared-risk-1")
        assert shared.source_hazard_type == "flood"


# ---------------------------------------------------------------------------
# Multi-path distribution
# ---------------------------------------------------------------------------


class TestMultiPathDistribution:
    def test_high_population_may_produce_multiple_routes(self, loaded_network, route_computer):
        """With high population, the router may produce multiple alternative paths."""
        aa_node_ids = loaded_network.get_assembly_area_node_ids()
        all_nodes = loaded_network.get_all_nodes()
        origin = next(n.id for n in all_nodes if n.id not in aa_node_ids)

        routes = route_computer.compute_routes(
            origin_nodes=[origin],
            zone_number=1,
            population=100_000,  # Very high to trigger multi-path
        )
        # Should find at least one route; may find more
        assert len(routes) >= 1


class TestPlanWideCorridorAllocation:
    def test_odd_population_is_conserved_across_destinations(self, tmp_path):
        network = _micro_network(
            tmp_path,
            [
                _edge("to-safe", "origin", "safe", 1),
                _edge("to-danger", "origin", "danger", 1),
            ],
            [
                _assembly_area("safe-aa", "safe"),
                _assembly_area("danger-aa", "danger"),
            ],
        )
        routes = RouteComputer(
            network,
            hazard_context=_hazard_context("earthquake"),
        ).compute_routes(["origin"], 1, 101, "earthquake")

        assert sum(route.allocated_population for route in routes) == 101
        assert sorted(route.allocated_population for route in routes) == [50, 51]

    def test_multiple_origins_share_one_population_once(self, tmp_path):
        network = _micro_network(
            tmp_path,
            [
                _edge("origin-route", "origin", "destination", 1),
                _edge("west-route", "west", "destination", 1),
            ],
        )
        routes = RouteComputer(
            network,
            hazard_context=_hazard_context("earthquake"),
        ).compute_routes(
            ["origin", "west"],
            1,
            101,
            "earthquake",
        )

        assert {route.origin_node_id for route in routes} == {"origin", "west"}
        assert sum(route.allocated_population for route in routes) == 101

    def test_disjoint_corridors_add_capacity(self, tmp_path):
        network = _micro_network(
            tmp_path,
            [
                _edge(
                    "to-safe",
                    "origin",
                    "safe",
                    1,
                    capacity_vehicles_per_hour=100,
                ),
                _edge(
                    "to-danger",
                    "origin",
                    "danger",
                    1,
                    capacity_vehicles_per_hour=100,
                ),
            ],
            [
                _assembly_area("safe-aa", "safe"),
                _assembly_area("danger-aa", "danger"),
            ],
        )
        routes = RouteComputer(
            network,
            hazard_context=_hazard_context("earthquake"),
        ).compute_routes(["origin"], 1, 100, "earthquake")

        assert {route.zone_shared_capacity_vehicles_per_hour for route in routes} == {200}

    def test_shared_choke_capacity_is_counted_once(self, tmp_path):
        network = _micro_network(
            tmp_path,
            [
                _edge(
                    "shared-choke",
                    "origin",
                    "danger",
                    1,
                    capacity_vehicles_per_hour=100,
                ),
                _edge(
                    "to-safe",
                    "danger",
                    "safe",
                    1,
                    capacity_vehicles_per_hour=100,
                ),
                _edge(
                    "to-destination",
                    "danger",
                    "destination",
                    1,
                    capacity_vehicles_per_hour=100,
                ),
            ],
            [
                _assembly_area("safe-aa", "safe"),
                _assembly_area("destination-aa", "destination"),
            ],
        )
        computer = RouteComputer(
            network,
            hazard_context=_hazard_context("earthquake"),
        )
        routes = computer.compute_routes(["origin"], 1, 100, "earthquake")

        assert {route.zone_shared_capacity_vehicles_per_hour for route in routes} == {100}
        choke = next(load for load in computer.corridor_loads if load.edge_id == "shared-choke")
        assert len(choke.route_ids) == 2
        assert choke.evacuation_load_vehicles_per_hour == pytest.approx(25)

    @pytest.mark.parametrize(
        ("population", "threshold", "expected_risk"),
        [
            (320, 80, False),
            (321, 80, True),
            (280, 70, False),
            (281, 70, True),
        ],
    )
    def test_congestion_threshold_is_strict_and_configurable(
        self,
        tmp_path,
        population,
        threshold,
        expected_risk,
    ):
        network = _micro_network(
            tmp_path,
            [
                _edge(
                    "direct",
                    "origin",
                    "safe",
                    1,
                    capacity_vehicles_per_hour=100,
                )
            ],
            [_assembly_area("safe-aa", "safe")],
        )
        route = RouteComputer(
            network,
            config=EvacuationConfig(congestion_risk_threshold_pct=threshold),
            hazard_context=_hazard_context("earthquake"),
        ).compute_routes(["origin"], 1, population, "earthquake")[0]

        assert route.congestion_risk is expected_risk
        assert route.uncapped_utilisation_pct == pytest.approx(population / 4)

    def test_current_load_and_excess_demand_remain_uncapped(self, tmp_path):
        network = _micro_network(
            tmp_path,
            [
                _edge(
                    "direct",
                    "origin",
                    "safe",
                    1,
                    capacity_vehicles_per_hour=100,
                    current_traffic_load_vehicles_per_hour=40,
                )
            ],
            [_assembly_area("safe-aa", "safe")],
        )
        computer = RouteComputer(
            network,
            hazard_context=_hazard_context("earthquake"),
        )
        route = computer.compute_routes(
            ["origin"],
            1,
            1000,
            "earthquake",
        )[0]

        assert route.allocated_population == 1000
        assert route.evacuation_load_vehicles_per_hour == pytest.approx(250)
        assert route.uncapped_utilisation_pct == pytest.approx(290)
        assert route.capacity_overloaded is True
        assert route.congestion_risk_pct == 100
        load = computer.corridor_loads[0]
        assert load.current_traffic_load_vehicles_per_hour == 40
        assert load.total_load_vehicles_per_hour == pytest.approx(290)


# ---------------------------------------------------------------------------
# Congestion risk flagging
# ---------------------------------------------------------------------------


class TestCongestionRiskFlagging:
    def test_congestion_risk_present(self, loaded_network, route_computer):
        aa_node_ids = loaded_network.get_assembly_area_node_ids()
        all_nodes = loaded_network.get_all_nodes()
        origin = next(n.id for n in all_nodes if n.id not in aa_node_ids)

        routes = route_computer.compute_routes(
            origin_nodes=[origin],
            zone_number=1,
            population=50_000,
        )
        if routes:
            # Congestion risk should be computed (0-100)
            for route in routes:
                assert 0 <= route.congestion_risk_pct <= 100

    def test_high_population_increases_congestion(self, loaded_network, route_computer):
        aa_node_ids = loaded_network.get_assembly_area_node_ids()
        all_nodes = loaded_network.get_all_nodes()
        origin = next(n.id for n in all_nodes if n.id not in aa_node_ids)

        routes_low = route_computer.compute_routes(
            origin_nodes=[origin],
            zone_number=1,
            population=10,
        )
        # Create a fresh computer to reset penalties
        rc2 = RouteComputer(road_network=loaded_network)
        routes_high = rc2.compute_routes(
            origin_nodes=[origin],
            zone_number=1,
            population=100_000,
        )
        if routes_low and routes_high:
            # Higher population should generally mean higher congestion
            assert routes_high[0].congestion_risk_pct >= routes_low[0].congestion_risk_pct


# ---------------------------------------------------------------------------
# No viable route returns empty
# ---------------------------------------------------------------------------


class TestNoViableRoute:
    def test_empty_origin_nodes(self, loaded_network, route_computer):
        routes = route_computer.compute_routes(
            origin_nodes=[],
            zone_number=1,
            population=100,
        )
        assert routes == []

    def test_isolated_node_returns_empty(self, loaded_network, route_computer):
        """If all edges from a node are closed, no routes can be found."""
        # Close ALL edges in the network
        for edge in loaded_network.get_all_edges():
            loaded_network.apply_closure(edge.id, "flood_cut")

        aa_node_ids = loaded_network.get_assembly_area_node_ids()
        all_nodes = loaded_network.get_all_nodes()
        origin = next(n.id for n in all_nodes if n.id not in aa_node_ids)

        routes = route_computer.compute_routes(
            origin_nodes=[origin],
            zone_number=1,
            population=100,
        )
        assert routes == []
