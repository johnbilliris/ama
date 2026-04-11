"""Road network loader — JSON parsing, graph construction, and road closure management.

Loads a static road network JSON file into an in-memory graph structure.
Supports zone-based capacity reduction and road closure management.
"""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field
from shapely.geometry import LineString

logger = logging.getLogger(__name__)

# Size constraints for MVP
MAX_NODES = 1_000
MAX_EDGES = 5_000


class RoadNode(BaseModel):
    """A node (intersection) in the road network."""
    id: str
    name: str
    coordinates: dict[str, float]  # {lat, lng}
    type: str = "intersection"  # intersection | endpoint
    is_assembly_area: bool = False
    zone_membership: int | None = None  # computed at runtime


class RoadEdge(BaseModel):
    """A road segment connecting two nodes."""
    id: str
    from_node: str
    to_node: str
    name: str
    distance_km: float
    capacity_vehicles_per_hour: int
    surface_type: str = "sealed"  # sealed | unsealed
    accessibility_features: list[str] = Field(default_factory=list)
    closure_status: str = "open"  # open | closed
    closure_reason: str | None = None
    geometry: dict[str, Any] = Field(default_factory=dict)  # GeoJSON LineString


class AssemblyAreaConfig(BaseModel):
    """Pre-configured assembly area from reference data."""
    assembly_area_id: str
    name: str
    coordinates: dict[str, float]  # {lat, lng}
    capacity_persons: int
    accessibility_features: list[str] = Field(default_factory=list)
    assigned_zones: list[int] = Field(default_factory=list)
    node_id: str  # Linked road network node


class RoadNetworkMetadata(BaseModel):
    """Metadata about the road network dataset."""
    version: str
    region: str
    coordinate_system: str = "WGS84"
    last_updated: str = ""


class RoadNetworkData(BaseModel):
    """Complete road network dataset parsed from JSON."""
    metadata: RoadNetworkMetadata
    nodes: list[RoadNode]
    edges: list[RoadEdge]
    assembly_areas: list[AssemblyAreaConfig]


class RoadNetworkLoader:
    """Loads and manages a static road network for graph-based routing."""

    def __init__(self, staleness_hours: int = 6) -> None:
        self._staleness_hours = staleness_hours
        self._data: RoadNetworkData | None = None
        self._adjacency: dict[str, list[tuple[str, RoadEdge]]] = {}
        self._edges_by_id: dict[str, RoadEdge] = {}
        self._nodes_by_id: dict[str, RoadNode] = {}
        self._assembly_areas_by_id: dict[str, AssemblyAreaConfig] = {}
        self._edge_geometries: dict[str, LineString] = {}
        self._loaded_at: datetime | None = None
        self._data_hash: str = ""

    def load(self, file_path: str) -> None:
        """Load road network from a JSON file and build adjacency graph."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Road network file not found: {file_path}")

        raw = path.read_text(encoding="utf-8")
        data = json.loads(raw)

        # Validate with Pydantic
        self._data = RoadNetworkData.model_validate(data)

        # Size validation
        if len(self._data.nodes) > MAX_NODES:
            raise ValueError(
                f"Road network exceeds maximum node count: "
                f"{len(self._data.nodes)} > {MAX_NODES}"
            )
        if len(self._data.edges) > MAX_EDGES:
            raise ValueError(
                f"Road network exceeds maximum edge count: "
                f"{len(self._data.edges)} > {MAX_EDGES}"
            )

        # Build indices
        self._nodes_by_id = {n.id: n for n in self._data.nodes}
        self._edges_by_id = {e.id: e for e in self._data.edges}
        self._assembly_areas_by_id = {
            a.assembly_area_id: a for a in self._data.assembly_areas
        }

        # Build adjacency list (bidirectional)
        self._adjacency = {}
        for node in self._data.nodes:
            self._adjacency[node.id] = []

        for edge in self._data.edges:
            self._adjacency.setdefault(edge.from_node, []).append((edge.to_node, edge))
            self._adjacency.setdefault(edge.to_node, []).append((edge.from_node, edge))

        # Build Shapely geometries from GeoJSON coordinates
        self._edge_geometries = {}
        for edge in self._data.edges:
            if edge.geometry and edge.geometry.get("coordinates"):
                coords = edge.geometry["coordinates"]
                if len(coords) >= 2:
                    self._edge_geometries[edge.id] = LineString(coords)

        self._loaded_at = datetime.now(UTC)
        self._data_hash = hashlib.sha256(raw.encode()).hexdigest()[:16]

        logger.info(
            "Road network loaded: %d nodes, %d edges, %d assembly areas, hash=%s",
            len(self._data.nodes),
            len(self._data.edges),
            len(self._data.assembly_areas),
            self._data_hash,
        )

    @property
    def is_loaded(self) -> bool:
        return self._data is not None

    @property
    def node_count(self) -> int:
        return len(self._nodes_by_id)

    @property
    def edge_count(self) -> int:
        return len(self._edges_by_id)

    def get_version(self) -> str:
        """Return hash of loaded road network data for reproducibility."""
        return self._data_hash

    def is_stale(self) -> bool:
        """Check if road data is older than staleness threshold."""
        if self._loaded_at is None:
            return True
        age_hours = (datetime.now(UTC) - self._loaded_at).total_seconds() / 3600
        return age_hours > self._staleness_hours

    def get_node(self, node_id: str) -> RoadNode | None:
        return self._nodes_by_id.get(node_id)

    def get_edge(self, edge_id: str) -> RoadEdge | None:
        return self._edges_by_id.get(edge_id)

    def get_edge_geometry(self, edge_id: str) -> LineString | None:
        return self._edge_geometries.get(edge_id)

    def get_neighbors(self, node_id: str) -> list[tuple[str, RoadEdge]]:
        """Return list of (neighbor_node_id, edge) for a node."""
        return self._adjacency.get(node_id, [])

    def get_assembly_areas(self) -> list[AssemblyAreaConfig]:
        return list(self._assembly_areas_by_id.values())

    def get_assembly_area(self, area_id: str) -> AssemblyAreaConfig | None:
        return self._assembly_areas_by_id.get(area_id)

    def get_all_edges(self) -> list[RoadEdge]:
        return list(self._edges_by_id.values())

    def get_all_nodes(self) -> list[RoadNode]:
        return list(self._nodes_by_id.values())

    def apply_closure(self, edge_id: str, reason: str) -> bool:
        """Close a road segment. Returns True if edge was found and closed."""
        edge = self._edges_by_id.get(edge_id)
        if edge is None:
            return False
        edge.closure_status = "closed"
        edge.closure_reason = reason
        return True

    def remove_closure(self, edge_id: str) -> bool:
        """Reopen a closed road segment. Returns True if edge was found and reopened."""
        edge = self._edges_by_id.get(edge_id)
        if edge is None:
            return False
        edge.closure_status = "open"
        edge.closure_reason = None
        return True

    def get_closed_edges(self) -> list[RoadEdge]:
        """Return all currently closed road segments."""
        return [e for e in self._edges_by_id.values() if e.closure_status == "closed"]

    def get_assembly_area_node_ids(self) -> set[str]:
        """Return node IDs that are assembly area locations."""
        return {a.node_id for a in self._assembly_areas_by_id.values()}
