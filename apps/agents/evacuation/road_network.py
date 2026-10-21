"""Road network loader — JSON parsing, graph construction, and road closure management.

Loads a static road network JSON file into an in-memory graph structure.
Supports zone-based capacity reduction and road closure management.
"""

from __future__ import annotations

import hashlib
import json
import logging
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator
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
    elevation_m: float | None = None
    coastal_exposure: bool | None = None


class RoadEdge(BaseModel):
    """A road segment connecting two nodes."""

    id: str
    from_node: str
    to_node: str
    name: str
    distance_km: float
    capacity_vehicles_per_hour: int
    current_traffic_load_vehicles_per_hour: float = Field(default=0, ge=0)
    surface_type: str = "sealed"  # sealed | unsealed
    accessibility_features: list[str] = Field(default_factory=list)
    closure_status: str = "open"  # open | closed
    closure_reason: str | None = None
    geometry: dict[str, Any] = Field(default_factory=dict)  # GeoJSON LineString
    elevation_m: float | None = None
    coastal_exposure: bool | None = None
    flood_exposure: bool | None = None
    tsunami_inundation_exposure: bool | None = None
    earthquake_damage_status: Literal["none", "suspected", "confirmed"] | None = None


class AssemblyAreaConfig(BaseModel):
    """Pre-configured assembly area from reference data."""

    assembly_area_id: str
    name: str
    coordinates: dict[str, float]  # {lat, lng}
    capacity_persons: int = Field(ge=0)
    current_occupancy_persons: int | None = Field(default=None, ge=0)
    accessibility_features: list[str] = Field(default_factory=list)
    assigned_zones: list[int] = Field(default_factory=list)
    node_id: str  # Linked road network node
    elevation_m: float | None = None
    coastal_exposure: bool | None = None
    flood_exposure: bool | None = None
    tsunami_inundation_exposure: bool | None = None
    shelter_types: list[str] = Field(default_factory=list)
    structural_status: Literal["safe", "uninspected", "unsafe"] | None = None

    @model_validator(mode="after")
    def _validate_occupancy(self) -> AssemblyAreaConfig:
        if self.current_occupancy_persons is not None and self.current_occupancy_persons > self.capacity_persons:
            raise ValueError("assembly occupancy cannot exceed capacity")
        return self


class RoadNetworkMetadata(BaseModel):
    """Metadata about the road network dataset."""

    version: str
    region: str
    coordinate_system: str = "WGS84"
    last_updated: datetime

    @model_validator(mode="after")
    def _require_timezone(self) -> RoadNetworkMetadata:
        if self.last_updated.tzinfo is None:
            raise ValueError("road network last_updated must be timezone-aware")
        return self


class RoadNetworkData(BaseModel):
    """Complete road network dataset parsed from JSON."""

    metadata: RoadNetworkMetadata
    nodes: list[RoadNode]
    edges: list[RoadEdge]
    assembly_areas: list[AssemblyAreaConfig]


class RoadNetworkLoader:
    """Loads and manages a static road network for graph-based routing."""

    def __init__(
        self,
        staleness_hours: int = 6,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        self._staleness_hours = staleness_hours
        self._now = now or (lambda: datetime.now(UTC))
        self._data: RoadNetworkData | None = None
        self._adjacency: dict[str, list[tuple[str, RoadEdge]]] = {}
        self._edges_by_id: dict[str, RoadEdge] = {}
        self._nodes_by_id: dict[str, RoadNode] = {}
        self._assembly_areas_by_id: dict[str, AssemblyAreaConfig] = {}
        self._edge_geometries: dict[str, LineString] = {}
        self._loaded_at: datetime | None = None
        self._data_hash: str = ""
        self._last_refresh_failed = False
        self._refresh_failure_reason = ""

    def load(self, file_path: str) -> None:
        """Load road network from a JSON file and build adjacency graph."""
        try:
            path = Path(file_path)
            if not path.exists():
                raise FileNotFoundError(f"Road network file not found: {file_path}")
            data = json.loads(path.read_text(encoding="utf-8"))
            candidate = RoadNetworkData.model_validate(data)
            if candidate.metadata.last_updated > self._now():
                raise ValueError("road network last_updated cannot be in the future")
            candidate.nodes.sort(key=lambda node: node.id)
            candidate.edges.sort(key=lambda edge: edge.id)
            candidate.assembly_areas.sort(key=lambda area: area.assembly_area_id)
            if len(candidate.nodes) > MAX_NODES:
                raise ValueError(f"Road network exceeds maximum node count: {len(candidate.nodes)} > {MAX_NODES}")
            if len(candidate.edges) > MAX_EDGES:
                raise ValueError(f"Road network exceeds maximum edge count: {len(candidate.edges)} > {MAX_EDGES}")

            nodes_by_id = {node.id: node for node in candidate.nodes}
            edges_by_id = {edge.id: edge for edge in candidate.edges}
            assembly_areas_by_id = {area.assembly_area_id: area for area in candidate.assembly_areas}
            adjacency: dict[str, list[tuple[str, RoadEdge]]] = {node.id: [] for node in candidate.nodes}
            for edge in candidate.edges:
                if edge.from_node not in nodes_by_id or edge.to_node not in nodes_by_id:
                    raise ValueError(f"Road edge {edge.id} references an unknown node")
                adjacency[edge.from_node].append((edge.to_node, edge))
                adjacency[edge.to_node].append((edge.from_node, edge))
            edge_geometries = {}
            for edge in candidate.edges:
                coordinates = edge.geometry.get("coordinates")
                if coordinates and len(coordinates) >= 2:
                    edge_geometries[edge.id] = LineString(coordinates)
            canonical = json.dumps(
                candidate.model_dump(mode="json"),
                sort_keys=True,
                separators=(",", ":"),
            )
        except Exception as exc:
            self._last_refresh_failed = True
            self._refresh_failure_reason = str(exc)
            raise

        self._data = candidate
        self._nodes_by_id = nodes_by_id
        self._edges_by_id = edges_by_id
        self._assembly_areas_by_id = assembly_areas_by_id
        self._adjacency = adjacency
        self._edge_geometries = edge_geometries
        self._loaded_at = self._now()
        self._data_hash = hashlib.sha256(canonical.encode()).hexdigest()[:16]
        self._last_refresh_failed = False
        self._refresh_failure_reason = ""

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

    @property
    def source_updated_at(self) -> datetime | None:
        return self._data.metadata.last_updated if self._data is not None else None

    @property
    def loaded_at(self) -> datetime | None:
        return self._loaded_at

    @property
    def last_refresh_failed(self) -> bool:
        return self._last_refresh_failed

    @property
    def refresh_failure_reason(self) -> str:
        return self._refresh_failure_reason

    def source_age_hours(self, now: datetime | None = None) -> float | None:
        if self.source_updated_at is None:
            return None
        current_time = now or self._now()
        return (current_time - self.source_updated_at).total_seconds() / 3600

    def get_version(self) -> str:
        """Return a content hash of the network's current effective state."""
        if self._data is None:
            return ""
        canonical = json.dumps(
            self._data.model_dump(mode="json"),
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(canonical.encode()).hexdigest()[:16]

    def is_stale(self) -> bool:
        """Check source age, not process load age, against the freshness window."""
        age_hours = self.source_age_hours()
        return age_hours is None or age_hours > self._staleness_hours

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

    def effective_copy(self, edge_overrides: list[dict[str, Any]]) -> RoadNetworkLoader:
        """Return an isolated graph snapshot with per-plan edge state applied."""
        if self._data is None:
            return RoadNetworkLoader(staleness_hours=self._staleness_hours)

        snapshot = RoadNetworkLoader(
            staleness_hours=self._staleness_hours,
            now=self._now,
        )
        snapshot._data = self._data.model_copy(deep=True)
        snapshot._nodes_by_id = {node.id: node for node in snapshot._data.nodes}
        snapshot._edges_by_id = {edge.id: edge for edge in snapshot._data.edges}
        snapshot._assembly_areas_by_id = {area.assembly_area_id: area for area in snapshot._data.assembly_areas}
        snapshot._adjacency = {node.id: [] for node in snapshot._data.nodes}
        for edge in snapshot._data.edges:
            snapshot._adjacency.setdefault(edge.from_node, []).append((edge.to_node, edge))
            snapshot._adjacency.setdefault(edge.to_node, []).append((edge.from_node, edge))
        snapshot._edge_geometries = dict(self._edge_geometries)
        snapshot._loaded_at = self._loaded_at
        snapshot._data_hash = self._data_hash
        snapshot._last_refresh_failed = self._last_refresh_failed
        snapshot._refresh_failure_reason = self._refresh_failure_reason

        for override in edge_overrides:
            overridden_edge = snapshot._edges_by_id.get(str(override.get("id", "")))
            if overridden_edge is None:
                continue
            overridden_edge.capacity_vehicles_per_hour = int(
                override.get("capacity_vehicles_per_hour", overridden_edge.capacity_vehicles_per_hour)
            )
            overridden_edge.closure_status = str(override.get("closure_status", overridden_edge.closure_status))
            overridden_edge.closure_reason = override.get("closure_reason", overridden_edge.closure_reason)
        return snapshot

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
