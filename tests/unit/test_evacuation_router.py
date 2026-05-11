"""Tests for evacuation.router — Dijkstra, closures, multi-path, congestion (T028)."""

import pytest
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
