"""Route computation — Dijkstra's algorithm with capacity weighting and hazard-aware strategies.

Implements graph-based shortest path computation with:
- Capacity-weighted edge costs
- Closed road and zone-based exclusion
- Multi-path distribution for congestion avoidance
- Hazard-type-specific routing strategies
- Congestion risk flagging
- Deterministic tie-breaking for reproducibility
"""

from __future__ import annotations

import heapq
import logging
from typing import Any
from uuid import uuid4

from evacuation.config import EvacuationConfig
from evacuation.models import ClosureReason, EvacuationRoute, ExcludedRoad
from evacuation.road_network import RoadNetworkLoader

logger = logging.getLogger(__name__)

# Penalty multiplier for edges on previously computed paths (for multi-path distribution)
MULTI_PATH_PENALTY = 3.0

# Maximum number of alternative paths to compute per origin-destination pair
MAX_ALTERNATIVE_PATHS = 3

# Closure-reason string → ClosureReason enum mapping
_CLOSURE_REASON_MAP: dict[str, ClosureReason] = {
    "emergency_services_closure": ClosureReason.emergency_services_closure,
    "flood_cut": ClosureReason.flood_cut,
    "fire_proximity": ClosureReason.fire_proximity,
    "structural_damage": ClosureReason.structural_damage,
    "zone_1_closure": ClosureReason.zone_1_closure,
    "capacity_exhausted": ClosureReason.capacity_exhausted,
}


def _to_closure_reason(reason: str | None) -> ClosureReason:
    """Map a free-text closure reason to the nearest ClosureReason enum value."""
    if reason and reason in _CLOSURE_REASON_MAP:
        return _CLOSURE_REASON_MAP[reason]
    # Map hazard-specific reasons to closest enum value
    if reason in ("storm_surge", "coastal_closure", "low_elevation"):
        return ClosureReason.emergency_services_closure
    if reason in ("low_lying",):
        return ClosureReason.flood_cut
    return ClosureReason.emergency_services_closure


class RouteComputer:
    """Computes evacuation routes using Dijkstra's algorithm with capacity weighting."""

    def __init__(
        self,
        road_network: RoadNetworkLoader,
        config: EvacuationConfig | None = None,
    ) -> None:
        self._network = road_network
        self._config = config or EvacuationConfig()
        self._edge_penalties: dict[str, float] = {}

    def compute_routes(
        self,
        origin_nodes: list[str],
        zone_number: int,
        population: int,
        hazard_type: str = "bushfire",
        excluded_edge_ids: set[str] | None = None,
    ) -> list[EvacuationRoute]:
        """Compute evacuation routes from origin nodes to assembly areas.

        Args:
            origin_nodes: List of node IDs in the evacuation zone.
            zone_number: Source evacuation zone number.
            population: Estimated population to evacuate.
            hazard_type: Hazard type for routing strategy selection.
            excluded_edge_ids: Additional edges to exclude beyond closures.

        Returns:
            List of EvacuationRoute records.
        """
        if not origin_nodes:
            return []

        assembly_node_ids = self._network.get_assembly_area_node_ids()
        if not assembly_node_ids:
            logger.warning("No assembly areas found in road network")
            return []

        # Apply hazard-type-specific edge exclusions
        hazard_excluded = self._get_hazard_exclusions(hazard_type)
        all_excluded = (excluded_edge_ids or set()) | hazard_excluded

        routes: list[EvacuationRoute] = []
        self._edge_penalties.clear()

        for origin in origin_nodes:
            # Try to find paths to each assembly area
            for aa in self._network.get_assembly_areas():
                if aa.node_id == origin:
                    continue

                path_routes = self._compute_paths(
                    origin=origin,
                    destination=aa.node_id,
                    zone_number=zone_number,
                    population=population,
                    assembly_area=aa,
                    hazard_type=hazard_type,
                    excluded_edges=all_excluded,
                )
                routes.extend(path_routes)

        # Sort routes by estimated travel time for deterministic ordering
        routes.sort(key=lambda r: (r.estimated_travel_minutes, r.route_id))
        return routes

    def _compute_paths(
        self,
        origin: str,
        destination: str,
        zone_number: int,
        population: int,
        assembly_area: Any,
        hazard_type: str,
        excluded_edges: set[str],
    ) -> list[EvacuationRoute]:
        """Compute one or more paths between origin and destination."""
        routes: list[EvacuationRoute] = []

        # First path via standard Dijkstra's
        path = self._dijkstra(origin, destination, excluded_edges)
        if path is None:
            return []

        route = self._build_route(
            path=path,
            zone_number=zone_number,
            population=population,
            assembly_area=assembly_area,
            hazard_type=hazard_type,
            excluded_edges=excluded_edges,
        )
        routes.append(route)

        # Check if multi-path distribution is needed
        bottleneck_capacity = path["bottleneck_capacity"]
        # Rough estimate: 2 people per vehicle, routes needed = pop / (capacity * duration in hours)
        if population > 0 and bottleneck_capacity > 0:
            estimated_throughput = bottleneck_capacity * 2  # persons per hour
            if population > estimated_throughput:
                # Need additional paths — penalise first path edges
                for edge_id in path["edge_ids"]:
                    self._edge_penalties[edge_id] = self._edge_penalties.get(edge_id, 1.0) * MULTI_PATH_PENALTY

                for _ in range(MAX_ALTERNATIVE_PATHS - 1):
                    alt_path = self._dijkstra(origin, destination, excluded_edges)
                    if alt_path is None:
                        break
                    # Don't add duplicate paths
                    if alt_path["edge_ids"] == path["edge_ids"]:
                        break

                    alt_route = self._build_route(
                        path=alt_path,
                        zone_number=zone_number,
                        population=population,
                        assembly_area=assembly_area,
                        hazard_type=hazard_type,
                        excluded_edges=excluded_edges,
                    )
                    routes.append(alt_route)

                    # Penalise this path too
                    for edge_id in alt_path["edge_ids"]:
                        self._edge_penalties[edge_id] = self._edge_penalties.get(edge_id, 1.0) * MULTI_PATH_PENALTY

        # Distribute population across routes
        if len(routes) > 1:
            self._distribute_population(routes, population)

        return routes

    def _dijkstra(
        self,
        origin: str,
        destination: str,
        excluded_edges: set[str],
    ) -> dict[str, Any] | None:
        """Run Dijkstra's algorithm from origin to destination.

        Uses capacity-weighted edge costs with deterministic tie-breaking by
        a monotonically increasing counter (T045).

        Weight formula: ``distance / (capacity × utilisation_factor)``
        where utilisation_factor starts at 1.0 and is adjusted via penalty map.

        Returns dict with 'node_path', 'edge_ids', 'total_distance_km', 'bottleneck_capacity'.
        Returns None if no path exists (shelter-in-place detection).
        """
        # Priority queue: (cost, tie_break_counter, node_id)
        counter = 0
        pq: list[tuple[float, int, str]] = [(0.0, counter, origin)]
        dist: dict[str, float] = {origin: 0.0}
        prev: dict[str, tuple[str, str]] = {}  # node -> (prev_node, edge_id)

        while pq:
            cost, _, current = heapq.heappop(pq)

            if current == destination:
                # Reconstruct path
                return self._reconstruct_path(origin, destination, prev)

            if cost > dist.get(current, float("inf")):
                continue

            # Get neighbors and sort by edge id for deterministic tie-breaking (T045)
            neighbors = sorted(
                self._network.get_neighbors(current),
                key=lambda item: item[1].id,
            )

            for neighbor, edge in neighbors:
                # Skip closed or excluded edges
                if edge.closure_status == "closed":
                    continue
                if edge.id in excluded_edges:
                    continue
                if edge.capacity_vehicles_per_hour <= 0:
                    continue

                # Compute edge weight: distance / (capacity × utilisation_factor)
                capacity = max(1, edge.capacity_vehicles_per_hour)
                penalty = self._edge_penalties.get(edge.id, 1.0)
                weight = (edge.distance_km / capacity) * penalty

                new_cost = cost + weight
                if new_cost < dist.get(neighbor, float("inf")):
                    dist[neighbor] = new_cost
                    prev[neighbor] = (current, edge.id)
                    counter += 1
                    heapq.heappush(pq, (new_cost, counter, neighbor))

        return None  # No path found — shelter-in-place

    def _reconstruct_path(self, origin: str, destination: str, prev: dict[str, tuple[str, str]]) -> dict[str, Any]:
        """Reconstruct path from Dijkstra's predecessor map."""
        node_path: list[str] = []
        edge_ids: list[str] = []
        total_distance = 0.0
        bottleneck_capacity = float("inf")

        current = destination
        while current != origin:
            node_path.append(current)
            prev_node, edge_id = prev[current]
            edge_ids.append(edge_id)
            edge = self._network.get_edge(edge_id)
            if edge:
                total_distance += edge.distance_km
                bottleneck_capacity = min(bottleneck_capacity, edge.capacity_vehicles_per_hour)
            current = prev_node

        node_path.append(origin)
        node_path.reverse()
        edge_ids.reverse()

        if bottleneck_capacity == float("inf"):
            bottleneck_capacity = 0

        return {
            "node_path": node_path,
            "edge_ids": edge_ids,
            "total_distance_km": round(total_distance, 2),
            "bottleneck_capacity": int(bottleneck_capacity),
        }

    def _build_route(
        self,
        path: dict[str, Any],
        zone_number: int,
        population: int,
        assembly_area: Any,
        hazard_type: str,
        excluded_edges: set[str],
    ) -> EvacuationRoute:
        """Build an EvacuationRoute from a computed path.

        Maps internal path representation to the EvacuationRoute Pydantic model.
        """
        total_distance: float = path["total_distance_km"]
        bottleneck_capacity: int = path["bottleneck_capacity"]

        # Estimate travel time under evacuation load (30 km/h loaded speed)
        avg_speed_loaded = 30.0  # km/h under evacuation load
        loaded_time_min = (total_distance / avg_speed_loaded) * 60 if total_distance > 0 else 0.0

        # Estimate utilisation as congestion_risk_pct (0-100)
        congestion_risk_pct = 0
        if bottleneck_capacity > 0 and population > 0:
            # Rough: assume evacuation over 2 hours, 2 people per vehicle
            vehicles_needed = population / 2
            vehicles_per_hour = vehicles_needed / 2
            congestion_risk_pct = min(100, int((vehicles_per_hour / bottleneck_capacity) * 100))

        # Vehicle suitability assessment (stored in route_name for context)
        vehicle_suitability = self._assess_vehicle_suitability(path["edge_ids"])

        # Collect excluded roads for this route
        excluded_roads = self._collect_excluded_roads(excluded_edges)

        route_id = f"route-{uuid4().hex[:8]}"

        suitability_note = ", ".join(f"{k}={'yes' if v else 'no'}" for k, v in vehicle_suitability.items())
        route_name = (
            f"Capacity-weighted path from Zone {zone_number} "
            f"to {assembly_area.name} ({hazard_type}; {suitability_note})"
        )

        return EvacuationRoute(
            route_id=route_id,
            zone_id=str(zone_number),
            assembly_area_id=assembly_area.assembly_area_id,
            route_name=route_name,
            distance_km=round(total_distance, 2),
            estimated_travel_minutes=int(round(loaded_time_min)),
            capacity_vehicles_per_hour=bottleneck_capacity,
            congestion_risk_pct=congestion_risk_pct,
            excluded_roads=excluded_roads,
            waypoints=path["edge_ids"],
        )

    def _assess_vehicle_suitability(self, edge_ids: list[str]) -> dict[str, bool]:
        """Assess vehicle suitability based on edge surface_type and accessibility_features."""
        has_unsealed = False
        has_accessible = True

        for edge_id in edge_ids:
            edge = self._network.get_edge(edge_id)
            if edge:
                if edge.surface_type == "unsealed":
                    has_unsealed = True
                if "wheelchair_accessible" not in edge.accessibility_features:
                    has_accessible = False

        return {
            "standard": True,
            "heavy": not has_unsealed,
            "accessible": has_accessible,
        }

    def _collect_excluded_roads(self, excluded_edges: set[str]) -> list[ExcludedRoad]:
        """Collect excluded road information for route reporting."""
        excluded: list[ExcludedRoad] = []
        for edge_id in sorted(excluded_edges)[:10]:  # Limit to 10 for readability
            edge = self._network.get_edge(edge_id)
            if edge:
                excluded.append(
                    ExcludedRoad(
                        road_id=edge.id,
                        road_name=edge.name,
                        closure_reason=_to_closure_reason(edge.closure_reason),
                    )
                )
        return excluded

    def _get_hazard_exclusions(self, hazard_type: str) -> set[str]:
        """Get additional edge exclusions based on hazard type routing strategy (T026).

        Five strategies per data-model.md:
        - bushfire: away from fire front, close roads within 2km fire perimeter
        - cyclone: inland shelters, close coastal roads in storm surge zone
        - flood: higher ground, close flood-prone/low-lying crossings
        - earthquake: away from damaged infrastructure
        - tsunami: elevated ground inland, close all coastal/low-elevation roads
        """
        excluded: set[str] = set()

        for edge in self._network.get_all_edges():
            if hazard_type == "bushfire":
                if edge.closure_reason == "fire_proximity":
                    excluded.add(edge.id)
            elif hazard_type == "cyclone":
                if edge.closure_reason in ("storm_surge", "coastal_closure"):
                    excluded.add(edge.id)
            elif hazard_type == "flood":
                if edge.closure_reason in ("flood_cut", "low_lying"):
                    excluded.add(edge.id)
            elif hazard_type == "earthquake":
                if edge.closure_reason == "structural_damage":
                    excluded.add(edge.id)
            elif hazard_type == "tsunami":
                if edge.closure_reason in ("coastal_closure", "low_elevation"):
                    excluded.add(edge.id)

        return excluded

    def _distribute_population(self, routes: list[EvacuationRoute], total_population: int) -> None:
        """Distribute population across multiple routes based on capacity (T025).

        Updates congestion_risk_pct on each route proportionally.
        """
        total_capacity = sum(r.capacity_vehicles_per_hour for r in routes)
        if total_capacity == 0:
            return

        for route in routes:
            fraction = route.capacity_vehicles_per_hour / total_capacity
            route_pop = int(total_population * fraction)
            if route.capacity_vehicles_per_hour > 0:
                vehicles_per_hour = (route_pop / 2) / 2  # 2 persons/vehicle over 2 hours
                utilisation_pct = min(100.0, (vehicles_per_hour / route.capacity_vehicles_per_hour) * 100)
                route.congestion_risk_pct = int(round(utilisation_pct))
