"""Tests for evacuation.road_network — graph construction, closures, staleness (T014)."""

import json
from datetime import UTC, datetime, timedelta

import pytest
from evacuation.road_network import (
    MAX_NODES,
    RoadNetworkLoader,
)
from shapely.geometry import LineString

SAMPLE_FILE = "data/road-networks/far-north-qld-sample.json"


# ---------------------------------------------------------------------------
# Loading the sample road network
# ---------------------------------------------------------------------------


class TestLoadSampleRoadNetwork:
    def test_loads_without_error(self):
        loader = RoadNetworkLoader()
        loader.load(SAMPLE_FILE)
        assert loader.is_loaded is True

    def test_node_count(self):
        loader = RoadNetworkLoader()
        loader.load(SAMPLE_FILE)
        assert loader.node_count == 50

    def test_edge_count(self):
        loader = RoadNetworkLoader()
        loader.load(SAMPLE_FILE)
        assert loader.edge_count == 120

    def test_file_not_found_raises(self):
        loader = RoadNetworkLoader()
        with pytest.raises(FileNotFoundError):
            loader.load("data/nonexistent.json")

    def test_is_loaded_false_initially(self):
        loader = RoadNetworkLoader()
        assert loader.is_loaded is False


# ---------------------------------------------------------------------------
# Graph construction (adjacency list)
# ---------------------------------------------------------------------------


class TestGraphConstruction:
    @pytest.fixture(autouse=True)
    def _load(self):
        self.loader = RoadNetworkLoader()
        self.loader.load(SAMPLE_FILE)

    def test_adjacency_not_empty(self):
        assert len(self.loader._adjacency) > 0

    def test_neighbors_exist_for_known_node(self):
        neighbors = self.loader.get_neighbors("node-001")
        assert len(neighbors) > 0

    def test_neighbors_return_edge(self):
        neighbors = self.loader.get_neighbors("node-001")
        for neighbor_id, edge in neighbors:
            assert isinstance(neighbor_id, str)
            assert edge.id is not None

    def test_bidirectional_edges(self):
        """Edges should be bidirectional (added in both directions)."""
        edge = self.loader.get_all_edges()[0]
        from_neighbors = {n_id for n_id, _ in self.loader.get_neighbors(edge.from_node)}
        to_neighbors = {n_id for n_id, _ in self.loader.get_neighbors(edge.to_node)}
        assert edge.to_node in from_neighbors
        assert edge.from_node in to_neighbors

    def test_all_nodes_have_adjacency_entries(self):
        for node in self.loader.get_all_nodes():
            assert node.id in self.loader._adjacency

    def test_get_node_returns_known_node(self):
        node = self.loader.get_node("node-001")
        assert node is not None
        assert node.name == "Cairns CBD"

    def test_get_node_returns_none_for_unknown(self):
        assert self.loader.get_node("nonexistent") is None

    def test_get_edge_returns_known_edge(self):
        edges = self.loader.get_all_edges()
        assert len(edges) > 0
        edge = self.loader.get_edge(edges[0].id)
        assert edge is not None

    def test_get_edge_returns_none_for_unknown(self):
        assert self.loader.get_edge("nonexistent") is None


# ---------------------------------------------------------------------------
# Size limit validation
# ---------------------------------------------------------------------------


class TestSizeLimitValidation:
    def test_max_nodes_exceeded_raises(self, tmp_path):
        """A network with >1000 nodes should raise ValueError."""
        nodes = [
            {
                "id": f"n-{i}",
                "name": f"Node {i}",
                "coordinates": {"lat": -16.9 + i * 0.001, "lng": 145.7},
                "type": "intersection",
                "is_assembly_area": False,
            }
            for i in range(MAX_NODES + 1)
        ]
        data = {
            "metadata": {
                "version": "1.0",
                "region": "Test",
                "coordinate_system": "WGS84",
            },
            "nodes": nodes,
            "edges": [],
            "assembly_areas": [],
        }
        file_path = tmp_path / "too-many-nodes.json"
        file_path.write_text(json.dumps(data))

        loader = RoadNetworkLoader()
        with pytest.raises(ValueError, match="exceeds maximum node count"):
            loader.load(str(file_path))


# ---------------------------------------------------------------------------
# Shapely LineString from edge geometry
# ---------------------------------------------------------------------------


class TestEdgeGeometry:
    @pytest.fixture(autouse=True)
    def _load(self):
        self.loader = RoadNetworkLoader()
        self.loader.load(SAMPLE_FILE)

    def test_some_edges_have_geometry(self):
        """At least some edges should have LineString geometries built."""
        count = sum(1 for e in self.loader.get_all_edges() if self.loader.get_edge_geometry(e.id) is not None)
        assert count > 0

    def test_geometry_is_linestring(self):
        for edge in self.loader.get_all_edges():
            geom = self.loader.get_edge_geometry(edge.id)
            if geom is not None:
                assert isinstance(geom, LineString)
                break

    def test_nonexistent_edge_geometry_returns_none(self):
        assert self.loader.get_edge_geometry("nonexistent") is None


# ---------------------------------------------------------------------------
# Road closure apply / remove
# ---------------------------------------------------------------------------


class TestRoadClosures:
    @pytest.fixture(autouse=True)
    def _load(self):
        self.loader = RoadNetworkLoader()
        self.loader.load(SAMPLE_FILE)

    def test_apply_closure(self):
        edge = self.loader.get_all_edges()[0]
        result = self.loader.apply_closure(edge.id, "flood_cut")
        assert result is True
        assert edge.closure_status == "closed"
        assert edge.closure_reason == "flood_cut"

    def test_apply_closure_unknown_edge(self):
        result = self.loader.apply_closure("nonexistent", "test")
        assert result is False

    def test_remove_closure(self):
        edge = self.loader.get_all_edges()[0]
        self.loader.apply_closure(edge.id, "flood_cut")
        result = self.loader.remove_closure(edge.id)
        assert result is True
        assert edge.closure_status == "open"
        assert edge.closure_reason is None

    def test_remove_closure_unknown_edge(self):
        result = self.loader.remove_closure("nonexistent")
        assert result is False

    def test_get_closed_edges(self):
        edges = self.loader.get_all_edges()
        self.loader.apply_closure(edges[0].id, "flood_cut")
        self.loader.apply_closure(edges[1].id, "fire_proximity")

        closed = self.loader.get_closed_edges()
        assert len(closed) == 2
        closed_ids = {e.id for e in closed}
        assert edges[0].id in closed_ids
        assert edges[1].id in closed_ids

    def test_no_closed_edges_initially(self):
        closed = self.loader.get_closed_edges()
        assert len(closed) == 0


# ---------------------------------------------------------------------------
# Staleness detection
# ---------------------------------------------------------------------------


class TestStalenessDetection:
    def test_stale_before_load(self):
        loader = RoadNetworkLoader()
        assert loader.is_stale() is True

    def test_not_stale_after_load(self):
        loader = RoadNetworkLoader(staleness_hours=6)
        loader.load(SAMPLE_FILE)
        assert loader.is_stale() is False

    def test_stale_when_load_time_old(self):
        loader = RoadNetworkLoader(staleness_hours=6)
        loader.load(SAMPLE_FILE)
        # Simulate old load time
        loader._loaded_at = datetime.now(UTC) - timedelta(hours=7)
        assert loader.is_stale() is True


# ---------------------------------------------------------------------------
# get_version() returns hash
# ---------------------------------------------------------------------------


class TestGetVersion:
    def test_version_is_hash_string(self):
        loader = RoadNetworkLoader()
        loader.load(SAMPLE_FILE)
        version = loader.get_version()
        assert isinstance(version, str)
        assert len(version) == 16  # truncated SHA-256

    def test_version_empty_before_load(self):
        loader = RoadNetworkLoader()
        assert loader.get_version() == ""

    def test_same_file_same_hash(self):
        l1 = RoadNetworkLoader()
        l1.load(SAMPLE_FILE)
        l2 = RoadNetworkLoader()
        l2.load(SAMPLE_FILE)
        assert l1.get_version() == l2.get_version()


# ---------------------------------------------------------------------------
# Assembly areas
# ---------------------------------------------------------------------------


class TestAssemblyAreas:
    @pytest.fixture(autouse=True)
    def _load(self):
        self.loader = RoadNetworkLoader()
        self.loader.load(SAMPLE_FILE)

    def test_assembly_areas_loaded(self):
        areas = self.loader.get_assembly_areas()
        assert len(areas) == 5

    def test_assembly_area_node_ids(self):
        node_ids = self.loader.get_assembly_area_node_ids()
        assert isinstance(node_ids, set)
        assert len(node_ids) > 0
