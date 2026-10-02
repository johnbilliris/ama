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

import hashlib
import heapq
import logging
import math
from typing import Any

from evacuation import telemetry as tel
from evacuation.config import EvacuationConfig
from evacuation.destinations import DestinationAllocator
from evacuation.models import (
    ClosureReason,
    CorridorLoad,
    DestinationAllocation,
    DestinationExclusion,
    EvacuationRoute,
    ExcludedRoad,
    HazardPreferenceEvidence,
    HazardRoutingContext,
    RoutingMode,
    UnresolvedDestinationDemand,
    VehicleSuitability,
)
from evacuation.road_network import RoadNetworkLoader
from evacuation.templates import generate_route_rationale_template

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
    return ClosureReason.unspecified


class RouteComputer:
    """Computes evacuation routes using Dijkstra's algorithm with capacity weighting."""

    def __init__(
        self,
        road_network: RoadNetworkLoader,
        config: EvacuationConfig | None = None,
        hazard_context: HazardRoutingContext | None = None,
    ) -> None:
        self._network = road_network
        self._config = config or EvacuationConfig()
        self._hazard_context = hazard_context
        self._edge_penalties: dict[str, float] = {}
        self._hazard_exclusion_reasons: dict[str, tuple[str, str]] = {}
        self._destination_exclusions: list[DestinationExclusion] = []
        self._hazard_data_gaps: list[str] = []
        self._active_hazard_types: set[str] = set()
        self._routing_mode = RoutingMode.hazard_constrained_degraded
        self._elevation_range: tuple[float, float] | None = None
        self._corridor_loads: list[CorridorLoad] = []
        self._unallocated_population_by_zone: dict[int, int] = {}
        self._unallocated_vulnerable_population_by_zone: dict[int, int] = {}
        self._excluded_roads: list[ExcludedRoad] = []
        self._destination_allocations: list[DestinationAllocation] = []
        self._unresolved_destination_demands: list[UnresolvedDestinationDemand] = []

    @property
    def routing_mode(self) -> RoutingMode:
        return self._routing_mode

    @property
    def hazard_data_gaps(self) -> list[str]:
        return list(self._hazard_data_gaps)

    @property
    def destination_exclusions(self) -> list[DestinationExclusion]:
        return list(self._destination_exclusions)

    @property
    def corridor_loads(self) -> list[CorridorLoad]:
        return [load.model_copy(deep=True) for load in self._corridor_loads]

    @property
    def unallocated_population_by_zone(self) -> dict[int, int]:
        return dict(self._unallocated_population_by_zone)

    @property
    def unallocated_vulnerable_population_by_zone(self) -> dict[int, int]:
        return dict(self._unallocated_vulnerable_population_by_zone)

    @property
    def excluded_roads(self) -> list[ExcludedRoad]:
        return [road.model_copy(deep=True) for road in self._excluded_roads]

    @property
    def destination_allocations(self) -> list[DestinationAllocation]:
        return [item.model_copy(deep=True) for item in self._destination_allocations]

    @property
    def unresolved_destination_demands(self) -> list[UnresolvedDestinationDemand]:
        return [item.model_copy(deep=True) for item in self._unresolved_destination_demands]

    def compute_routes(
        self,
        origin_nodes: list[str],
        zone_number: int,
        population: int,
        hazard_type: str = "bushfire",
        excluded_edge_ids: set[str] | None = None,
        allocate_population: bool = True,
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
        self._prepare_hazard_policy(hazard_type)
        hazard_excluded = set(self._hazard_exclusion_reasons)
        zero_capacity_edges = {
            edge.id for edge in self._network.get_all_edges() if edge.capacity_vehicles_per_hour <= 0
        }
        all_excluded = (excluded_edge_ids or set()) | hazard_excluded | zero_capacity_edges
        self._excluded_roads = self._collect_excluded_roads(all_excluded)
        eligible_assembly_areas = self._eligible_assembly_areas()
        if not origin_nodes:
            return []
        assembly_node_ids = self._network.get_assembly_area_node_ids()
        if not assembly_node_ids:
            logger.warning("No assembly areas found in road network")
            return []

        routes: list[EvacuationRoute] = []
        self._edge_penalties.clear()

        for origin in origin_nodes:
            # Try to find paths to each assembly area
            for aa in eligible_assembly_areas:
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
        routes.sort(
            key=lambda route: (
                route.hazard_risk_score,
                route.estimated_travel_minutes,
                route.distance_km,
                route.assembly_area_id,
                route.origin_node_id,
                tuple(route.waypoints),
            )
        )
        if allocate_population:
            self.allocate_plan_routes(
                routes,
                {zone_number: population},
            )
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
        self._edge_penalties.clear()
        routes: list[EvacuationRoute] = []

        # First path via standard Dijkstra's
        with tel.start_span(
            "evacuation.dijkstra_run",
            attributes={"origin": origin, "destination": destination},
        ):
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
        window_hours = self._config.route_allocation_window_minutes / 60
        if population > 0 and bottleneck_capacity > 0:
            estimated_throughput = bottleneck_capacity * self._config.average_persons_per_vehicle * window_hours
            if population > estimated_throughput:
                # Need additional paths — penalise first path edges
                for edge_id in path["edge_ids"]:
                    self._edge_penalties[edge_id] = self._edge_penalties.get(edge_id, 1.0) * MULTI_PATH_PENALTY

                for _ in range(MAX_ALTERNATIVE_PATHS - 1):
                    with tel.start_span(
                        "evacuation.dijkstra_run",
                        attributes={
                            "origin": origin,
                            "destination": destination,
                        },
                    ):
                        alt_path = self._dijkstra(
                            origin,
                            destination,
                            excluded_edges,
                        )
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

        return routes

    def _dijkstra(
        self,
        origin: str,
        destination: str,
        excluded_edges: set[str],
    ) -> dict[str, Any] | None:
        """Run Dijkstra's algorithm from origin to destination.

        Uses capacity-weighted edge costs with deterministic tie-breaking by
        projected utilisation, distance, and ordered edge identifiers (T045).

        Weight formula: ``distance / (capacity × utilisation_factor)``
        where utilisation_factor starts at 1.0 and is adjusted via penalty map.

        Returns dict with 'node_path', 'edge_ids', 'total_distance_km', 'bottleneck_capacity'.
        Returns None if no path exists (shelter-in-place detection).
        """
        # Labels compare cost, projected current-load utilisation, distance,
        # and the ordered edge path before the node identifier.
        origin_label: tuple[float, float, float, tuple[str, ...]] = (
            0.0,
            0.0,
            0.0,
            (),
        )
        pq: list[tuple[float, float, float, tuple[str, ...], str]] = [(*origin_label, origin)]
        best: dict[
            str,
            tuple[float, float, float, tuple[str, ...]],
        ] = {origin: origin_label}
        prev: dict[str, tuple[str, str]] = {}  # node -> (prev_node, edge_id)

        while pq:
            cost, projected_utilisation, distance_km, path_edges, current = heapq.heappop(pq)
            label = (
                cost,
                projected_utilisation,
                distance_km,
                path_edges,
            )
            if label != best.get(current):
                continue

            if current == destination:
                # Reconstruct path
                return self._reconstruct_path(origin, destination, prev)

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
                hazard_penalty = self._edge_hazard_penalty(
                    current,
                    neighbor,
                    edge,
                )
                weight = (edge.distance_km / capacity) * penalty * hazard_penalty

                new_cost = cost + weight
                edge_utilisation = (
                    edge.current_traffic_load_vehicles_per_hour / edge.capacity_vehicles_per_hour
                    if edge.capacity_vehicles_per_hour > 0
                    else float("inf")
                )
                new_label = (
                    new_cost,
                    max(projected_utilisation, edge_utilisation),
                    distance_km + edge.distance_km,
                    path_edges + (edge.id,),
                )
                if new_label < best.get(
                    neighbor,
                    (float("inf"), float("inf"), float("inf"), ()),
                ):
                    best[neighbor] = new_label
                    prev[neighbor] = (current, edge.id)
                    heapq.heappush(pq, (*new_label, neighbor))

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

        hazard_risk_score = 0.0
        preference_evidence: list[HazardPreferenceEvidence] = []
        for index, edge_id in enumerate(edge_ids):
            edge = self._network.get_edge(edge_id)
            if edge is not None:
                edge_evidence = self._edge_preference_evidence(
                    node_path[index],
                    node_path[index + 1],
                    edge,
                )
                preference_evidence.extend(edge_evidence)
                edge_penalty = math.prod(evidence.multiplier for evidence in edge_evidence) if edge_evidence else 1.0
                hazard_risk_score += max(0.0, edge_penalty - 1.0)

        if bottleneck_capacity == float("inf"):
            bottleneck_capacity = 0

        return {
            "node_path": node_path,
            "edge_ids": edge_ids,
            "total_distance_km": round(total_distance, 2),
            "bottleneck_capacity": int(bottleneck_capacity),
            "hazard_risk_score": hazard_risk_score,
            "hazard_preference_evidence": preference_evidence,
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
        excluded_roads = [road.model_copy(deep=True) for road in self._excluded_roads]

        route_id = self._stable_route_id(
            zone_number,
            path["node_path"][0],
            assembly_area.assembly_area_id,
            path["edge_ids"],
        )

        route_name = f"Deterministic path from Zone {zone_number} to {assembly_area.name}"
        hazard_risk_score = path["hazard_risk_score"] + (self._destination_risk_score(assembly_area))
        hazard_names = ", ".join(sorted(self._active_hazard_types))
        selection_rationale = (
            f"Selected by {self._routing_mode.value} policy for {hazard_names}; "
            "hard safety exclusions applied before capacity-weighted Dijkstra"
        )
        preference_types = []
        if "bushfire" in self._active_hazard_types:
            preference_types.append("wind direction")
        if self._active_hazard_types.intersection({"cyclone", "flood", "tsunami"}):
            preference_types.append("relative elevation")
        if "earthquake" in self._active_hazard_types:
            preference_types.append("damage status")
        if preference_types:
            selection_rationale += "; evaluated preferences: " + ", ".join(preference_types)
        if hazard_risk_score:
            selection_rationale += f"; residual relative preference score {hazard_risk_score:.3f}"
        if self._hazard_data_gaps:
            selection_rationale += "; data gaps: " + ", ".join(self._hazard_data_gaps)

        route = EvacuationRoute(
            route_id=route_id,
            zone_id=str(zone_number),
            origin_node_id=path["node_path"][0],
            assembly_area_id=assembly_area.assembly_area_id,
            route_name=route_name,
            congestion_risk_pct=0,
            excluded_roads=excluded_roads,
            waypoints=path["edge_ids"],
            path=path["edge_ids"],
            node_path=path["node_path"],
            selection_rationale=selection_rationale,
            routing_mode=self._routing_mode,
            hazard_data_gaps=self._hazard_data_gaps,
            hazard_risk_score=hazard_risk_score,
            hazard_preference_evidence=path["hazard_preference_evidence"],
        )
        return self.populate_route_static_evidence(route, path["node_path"])

    def _stable_route_id(
        self,
        zone_number: int,
        origin_node_id: str,
        assembly_area_id: str,
        edge_ids: list[str],
    ) -> str:
        identity = "|".join(
            [
                "route-v1",
                (self._hazard_context.incident_scope_key if self._hazard_context is not None else ""),
                str(zone_number),
                origin_node_id,
                assembly_area_id,
                ",".join(edge_ids),
            ]
        )
        return f"route-{hashlib.sha256(identity.encode()).hexdigest()[:16]}"

    def populate_route_static_evidence(
        self,
        route: EvacuationRoute,
        node_path: list[str],
    ) -> EvacuationRoute:
        """Derive connected-path metrics identically for all route sources."""
        edges = []
        for edge_id in route.waypoints:
            edge = self._network.get_edge(edge_id)
            if edge is None:
                raise ValueError(f"Route references unknown edge {edge_id}")
            edges.append(edge)
        if len(node_path) != len(edges) + 1:
            raise ValueError("Route node path must contain one more node than edges")
        for index, edge in enumerate(edges):
            if {node_path[index], node_path[index + 1]} != {
                edge.from_node,
                edge.to_node,
            }:
                raise ValueError("Route node path is not connected by its edges")

        distance = round(sum(edge.distance_km for edge in edges), 2)
        normal_minutes = distance / self._config.normal_route_speed_kmh * 60 if distance > 0 else 0.0
        loaded_minutes = distance / self._config.loaded_route_speed_kmh * 60 if distance > 0 else 0.0
        route.origin_node_id = node_path[0] if node_path else ""
        route.node_path = list(node_path)
        route.path = list(route.waypoints)
        route.origin_zone = int(route.zone_id) if route.zone_id.isdigit() else 0
        route.destination_assembly_area = route.assembly_area_id
        route.distance_km = distance
        route.total_distance_km = distance
        route.estimated_travel_time_normal_min = round(normal_minutes, 2)
        route.estimated_travel_time_loaded_min = round(loaded_minutes, 2)
        route.estimated_travel_minutes = round(loaded_minutes)
        route.capacity_vehicles_per_hour = min(
            (edge.capacity_vehicles_per_hour for edge in edges),
            default=0,
        )
        route.vehicle_suitability = VehicleSuitability.model_validate(self._assess_vehicle_suitability(route.waypoints))
        return route

    def allocate_plan_routes(
        self,
        routes: list[EvacuationRoute],
        population_by_zone: dict[int, int],
        vulnerable_population_by_zone: dict[int, int] | None = None,
    ) -> None:
        """Allocate each zone population once and build one shared-edge ledger."""
        self._corridor_loads = []
        ordered_routes = sorted(
            routes,
            key=lambda route: (
                int(route.zone_id),
                route.hazard_risk_score,
                route.estimated_travel_minutes,
                route.distance_km,
                route.assembly_area_id,
                route.origin_node_id,
                tuple(route.waypoints),
            ),
        )
        for route in ordered_routes:
            route.allocated_population = 0
        destination_result = DestinationAllocator(self._network).allocate(
            ordered_routes,
            population_by_zone,
            vulnerable_population_by_zone,
        )
        self._destination_allocations = destination_result.allocations
        self._unresolved_destination_demands = destination_result.unresolved
        self._unallocated_population_by_zone = destination_result.unallocated_population_by_zone
        self._unallocated_vulnerable_population_by_zone = destination_result.unallocated_vulnerable_population_by_zone

        window_hours = self._config.route_allocation_window_minutes / 60
        occupancy = self._config.average_persons_per_vehicle
        edge_evacuation_loads: dict[str, float] = {}
        edge_route_ids: dict[str, set[str]] = {}
        for route in ordered_routes:
            route.evacuation_load_vehicles_per_hour = route.allocated_population / occupancy / window_hours
            for edge_id in set(route.waypoints):
                edge_evacuation_loads[edge_id] = (
                    edge_evacuation_loads.get(edge_id, 0.0) + route.evacuation_load_vehicles_per_hour
                )
                edge_route_ids.setdefault(edge_id, set()).add(route.route_id)

        loads_by_edge: dict[str, CorridorLoad] = {}
        for edge_id in sorted(edge_evacuation_loads):
            edge = self._network.get_edge(edge_id)
            if edge is None:
                continue
            total_load = edge.current_traffic_load_vehicles_per_hour + edge_evacuation_loads[edge_id]
            utilisation = (
                total_load / edge.capacity_vehicles_per_hour * 100
                if edge.capacity_vehicles_per_hour > 0
                else float("inf")
            )
            load = CorridorLoad(
                edge_id=edge_id,
                capacity_vehicles_per_hour=edge.capacity_vehicles_per_hour,
                current_traffic_load_vehicles_per_hour=(edge.current_traffic_load_vehicles_per_hour),
                evacuation_load_vehicles_per_hour=edge_evacuation_loads[edge_id],
                total_load_vehicles_per_hour=total_load,
                uncapped_utilisation_pct=utilisation,
                capacity_overloaded=utilisation > 100,
                route_ids=sorted(edge_route_ids[edge_id]),
            )
            loads_by_edge[edge_id] = load
        self._corridor_loads = list(loads_by_edge.values())

        for route in ordered_routes:
            route_loads = [loads_by_edge[edge_id] for edge_id in route.waypoints if edge_id in loads_by_edge]
            route.uncapped_utilisation_pct = max(
                (load.uncapped_utilisation_pct for load in route_loads),
                default=0.0,
            )
            route.estimated_utilisation_pct = route.uncapped_utilisation_pct
            route.congestion_risk_pct = min(
                100,
                round(route.uncapped_utilisation_pct),
            )
            route.congestion_risk = route.uncapped_utilisation_pct > self._config.congestion_risk_threshold_pct
            route.capacity_overloaded = route.uncapped_utilisation_pct > 100
            route.bottleneck_edge_ids = sorted(
                load.edge_id
                for load in route_loads
                if math.isclose(
                    load.uncapped_utilisation_pct,
                    route.uncapped_utilisation_pct,
                )
            )
            route.selection_rationale = generate_route_rationale_template(
                route.model_dump(mode="json"),
                hazard_type=",".join(sorted(self._active_hazard_types)),
            )

        for zone_number in sorted(population_by_zone):
            zone_routes = [route for route in ordered_routes if int(route.zone_id) == zone_number]
            shared_capacity = self._max_flow_capacity(zone_routes)
            for route in zone_routes:
                route.zone_shared_capacity_vehicles_per_hour = shared_capacity
        routes.sort(
            key=lambda route: (
                route.hazard_risk_score,
                route.uncapped_utilisation_pct,
                route.estimated_travel_time_loaded_min,
                route.total_distance_km,
                route.assembly_area_id,
                route.origin_node_id,
                tuple(route.path),
            )
        )

    def _route_available_capacity(self, route: EvacuationRoute) -> float:
        capacities = []
        for edge_id in route.waypoints:
            edge = self._network.get_edge(edge_id)
            if edge is not None:
                capacities.append(
                    max(
                        0.0,
                        edge.capacity_vehicles_per_hour - edge.current_traffic_load_vehicles_per_hour,
                    )
                )
        return min(capacities, default=0.0)

    @staticmethod
    def _largest_remainder(total: int, weights: list[float]) -> list[int]:
        if total < 0:
            raise ValueError("Population allocation total cannot be negative")
        weight_total = sum(weights)
        if weight_total <= 0:
            return [0] * len(weights)
        raw = [total * weight / weight_total for weight in weights]
        allocations = [math.floor(value) for value in raw]
        remaining = total - sum(allocations)
        ranking = sorted(
            range(len(raw)),
            key=lambda index: (
                -(raw[index] - allocations[index]),
                index,
            ),
        )
        for index in ranking[:remaining]:
            allocations[index] += 1
        return allocations

    def _max_flow_capacity(self, routes: list[EvacuationRoute]) -> int:
        if not routes:
            return 0
        source = "__zone_source__"
        sink = "__zone_sink__"
        capacities: dict[tuple[str, str], float] = {}
        physical_arcs: dict[tuple[str, str], set[str]] = {}
        origins = {route.origin_node_id for route in routes}
        destinations = {route.node_path[-1] for route in routes if route.node_path}

        for route in routes:
            if len(route.node_path) != len(route.waypoints) + 1:
                continue
            for start, end, edge_id in zip(
                route.node_path[:-1],
                route.node_path[1:],
                route.waypoints,
                strict=True,
            ):
                physical_arcs.setdefault((start, end), set()).add(edge_id)
        for arc, edge_ids in physical_arcs.items():
            capacities[arc] = sum(self._available_edge_capacity(edge_id) for edge_id in edge_ids)
        infinite_capacity = sum(capacities.values()) or 1.0
        for origin in origins:
            capacities[(source, origin)] = infinite_capacity
        for destination in destinations:
            capacities[(destination, sink)] = infinite_capacity
        return math.floor(self._edmonds_karp(capacities, source, sink))

    def _available_edge_capacity(self, edge_id: str) -> float:
        edge = self._network.get_edge(edge_id)
        if edge is None:
            return 0.0
        return max(
            0.0,
            edge.capacity_vehicles_per_hour - edge.current_traffic_load_vehicles_per_hour,
        )

    @staticmethod
    def _edmonds_karp(
        capacities: dict[tuple[str, str], float],
        source: str,
        sink: str,
    ) -> float:
        residual = dict(capacities)
        adjacency: dict[str, set[str]] = {}
        for start, end in capacities:
            adjacency.setdefault(start, set()).add(end)
            adjacency.setdefault(end, set()).add(start)
            residual.setdefault((end, start), 0.0)
        total_flow = 0.0
        while True:
            parents: dict[str, str | None] = {source: None}
            queue = [source]
            for current in queue:
                for neighbor in sorted(adjacency.get(current, set())):
                    if neighbor in parents or residual.get((current, neighbor), 0) <= 0:
                        continue
                    parents[neighbor] = current
                    queue.append(neighbor)
                    if neighbor == sink:
                        break
                if sink in parents:
                    break
            if sink not in parents:
                return total_flow
            path_flow = float("inf")
            current = sink
            while parents[current] is not None:
                previous = parents[current]
                path_flow = min(
                    path_flow,
                    residual[(previous, current)],
                )
                current = previous
            current = sink
            while parents[current] is not None:
                previous = parents[current]
                residual[(previous, current)] -= path_flow
                residual[(current, previous)] += path_flow
                current = previous
            total_flow += path_flow

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
        for edge_id in sorted(excluded_edges):
            edge = self._network.get_edge(edge_id)
            if edge:
                hazard_reason = self._hazard_exclusion_reasons.get(edge_id)
                if hazard_reason is not None:
                    exclusion_reason, source_hazard_type = hazard_reason
                    closure_reason = _to_closure_reason(edge.closure_reason)
                elif edge.capacity_vehicles_per_hour <= 0:
                    exclusion_reason = "Road has zero effective capacity"
                    source_hazard_type = None
                    closure_reason = ClosureReason.capacity_exhausted
                elif edge.closure_reason:
                    exclusion_reason = edge.closure_reason
                    source_hazard_type = None
                    closure_reason = _to_closure_reason(edge.closure_reason)
                else:
                    exclusion_reason = "Excluded without a reported closure cause"
                    source_hazard_type = None
                    closure_reason = ClosureReason.unspecified
                excluded.append(
                    ExcludedRoad(
                        road_id=edge.id,
                        edge_id=edge.id,
                        road_name=edge.name,
                        closure_reason=closure_reason,
                        exclusion_reason=exclusion_reason,
                        source_hazard_type=source_hazard_type,
                    )
                )
        return excluded

    def _prepare_hazard_policy(self, primary_hazard_type: str) -> None:
        context = self._hazard_context or HazardRoutingContext(hazard_types=[primary_hazard_type])
        self._active_hazard_types = set(context.hazard_types or [primary_hazard_type])
        self._hazard_exclusion_reasons = {}
        self._destination_exclusions = []
        self._hazard_data_gaps = self._find_hazard_data_gaps(context)

        elevations = [float(edge.elevation_m) for edge in self._network.get_all_edges() if edge.elevation_m is not None]
        self._elevation_range = (min(elevations), max(elevations)) if elevations else None

        fire_areas = []
        for area in context.bushfire_exclusion_areas:
            try:
                from shapely.geometry import shape

                geometry = shape(area)
                if not geometry.is_empty and geometry.is_valid:
                    fire_areas.append(geometry)
            except (TypeError, ValueError):
                continue

        for edge in self._network.get_all_edges():
            geometry = self._network.get_edge_geometry(edge.id)
            reason = self._hard_exclusion_reason(edge, geometry, fire_areas)
            if reason is not None:
                self._hazard_exclusion_reasons[edge.id] = reason

        self._routing_mode = (
            RoutingMode.hazard_aware if not self._hazard_data_gaps else RoutingMode.hazard_constrained_degraded
        )

    def _find_hazard_data_gaps(
        self,
        context: HazardRoutingContext,
    ) -> list[str]:
        edges = self._network.get_all_edges()
        areas = self._network.get_assembly_areas()
        gaps: set[str] = set()

        if "bushfire" in self._active_hazard_types:
            if not context.bushfire_exclusion_areas:
                gaps.add("bushfire.fire_perimeter_buffer")
            if context.wind_from_degrees is None:
                gaps.add("bushfire.wind_from_degrees")
            if any(self._network.get_edge_geometry(edge.id) is None for edge in edges):
                gaps.add("bushfire.edge_geometry")
        if "cyclone" in self._active_hazard_types:
            if any(edge.coastal_exposure is None for edge in edges):
                gaps.add("cyclone.edge_coastal_exposure")
            if any(area.coastal_exposure is None or not area.shelter_types for area in areas):
                gaps.add("cyclone.destination_safety")
        if "flood" in self._active_hazard_types:
            if any(edge.flood_exposure is None or edge.elevation_m is None for edge in edges):
                gaps.add("flood.edge_exposure_elevation")
            if any(area.flood_exposure is None or area.elevation_m is None for area in areas):
                gaps.add("flood.destination_exposure_elevation")
        if "earthquake" in self._active_hazard_types:
            if any(edge.earthquake_damage_status is None for edge in edges):
                gaps.add("earthquake.edge_damage_status")
            if any(area.structural_status is None for area in areas):
                gaps.add("earthquake.destination_structural_status")
        if "tsunami" in self._active_hazard_types:
            if any(
                edge.coastal_exposure is None or edge.tsunami_inundation_exposure is None or edge.elevation_m is None
                for edge in edges
            ):
                gaps.add("tsunami.edge_coastal_inundation_elevation")
            if any(
                area.coastal_exposure is None or area.tsunami_inundation_exposure is None or area.elevation_m is None
                for area in areas
            ):
                gaps.add("tsunami.destination_coastal_inundation_elevation")
        return sorted(gaps)

    def _hard_exclusion_reason(
        self,
        edge: Any,
        geometry: Any,
        fire_areas: list[Any],
    ) -> tuple[str, str] | None:
        if "bushfire" in self._active_hazard_types and (
            edge.closure_reason == "fire_proximity"
            or (geometry is not None and any(area.intersects(geometry) for area in fire_areas))
        ):
            return "Road intersects the 2 km bushfire perimeter exclusion", "bushfire"
        if "cyclone" in self._active_hazard_types and (
            edge.coastal_exposure is True or edge.closure_reason in {"storm_surge", "coastal_closure"}
        ):
            return "Coastal or storm-surge road excluded for cyclone", "cyclone"
        if "flood" in self._active_hazard_types and (
            edge.flood_exposure is True or edge.closure_reason in {"flood_cut", "low_lying"}
        ):
            return "Flood-exposed or low-lying road excluded", "flood"
        if "earthquake" in self._active_hazard_types and (
            edge.earthquake_damage_status == "confirmed" or edge.closure_reason == "structural_damage"
        ):
            return "Confirmed structural damage exclusion", "earthquake"
        if "tsunami" in self._active_hazard_types and (
            edge.coastal_exposure is True
            or edge.tsunami_inundation_exposure is True
            or edge.closure_reason
            in {
                "coastal_closure",
                "low_elevation",
                "storm_surge",
            }
        ):
            return "Coastal or inundation-exposed road excluded for tsunami", "tsunami"
        return None

    def _eligible_assembly_areas(self) -> list[Any]:
        eligible = []
        for area in self._network.get_assembly_areas():
            exclusion = self._destination_exclusion(area)
            if exclusion is None:
                eligible.append(area)
            else:
                self._destination_exclusions.append(exclusion)
        return eligible

    def _destination_exclusion(self, area: Any) -> DestinationExclusion | None:
        point = None
        try:
            from shapely.geometry import Point, shape

            point = Point(
                area.coordinates.get("lng", 0),
                area.coordinates.get("lat", 0),
            )
            if "bushfire" in self._active_hazard_types:
                for geometry in self._hazard_context.bushfire_exclusion_areas if self._hazard_context else []:
                    if shape(geometry).covers(point):
                        return self._destination_rejection(
                            area,
                            "Assembly area intersects the 2 km bushfire perimeter exclusion",
                            "bushfire",
                        )
        except (TypeError, ValueError):
            point = None
        del point

        if "cyclone" in self._active_hazard_types:
            if area.coastal_exposure is True:
                return self._destination_rejection(
                    area,
                    "Coastal assembly area is unsuitable for cyclone shelter",
                    "cyclone",
                )
            if area.shelter_types and "cyclone_shelter" not in area.shelter_types:
                return self._destination_rejection(
                    area,
                    "Assembly area is not certified as a cyclone shelter",
                    "cyclone",
                )
        if "flood" in self._active_hazard_types and area.flood_exposure is True:
            return self._destination_rejection(
                area,
                "Flood-exposed assembly area is unsuitable",
                "flood",
            )
        if "earthquake" in self._active_hazard_types and area.structural_status == "unsafe":
            return self._destination_rejection(
                area,
                "Structurally unsafe assembly area is unsuitable",
                "earthquake",
            )
        if "tsunami" in self._active_hazard_types and (
            area.coastal_exposure is True or area.tsunami_inundation_exposure is True
        ):
            return self._destination_rejection(
                area,
                "Coastal or inundation-exposed assembly area is unsuitable for tsunami",
                "tsunami",
            )
        return None

    @staticmethod
    def _destination_rejection(
        area: Any,
        reason: str,
        hazard_type: str,
    ) -> DestinationExclusion:
        return DestinationExclusion(
            assembly_area_id=area.assembly_area_id,
            assembly_area_name=area.name,
            reason=reason,
            source_hazard_type=hazard_type,
        )

    def _edge_hazard_penalty(
        self,
        from_node_id: str,
        to_node_id: str,
        edge: Any,
    ) -> float:
        evidence = self._edge_preference_evidence(
            from_node_id,
            to_node_id,
            edge,
        )
        return math.prod(item.multiplier for item in evidence) if evidence else 1.0

    def _edge_preference_evidence(
        self,
        from_node_id: str,
        to_node_id: str,
        edge: Any,
    ) -> list[HazardPreferenceEvidence]:
        evidence: list[HazardPreferenceEvidence] = []
        context = self._hazard_context
        if "bushfire" in self._active_hazard_types and context is not None and context.wind_from_degrees is not None:
            bearing = self._travel_bearing(from_node_id, to_node_id)
            if bearing is not None:
                downwind = (context.wind_from_degrees + 180.0) % 360.0
                delta = math.radians(self._bearing_delta(bearing, downwind))
                multiplier = 1.0 + max(0.0, math.cos(delta))
                if multiplier > 1.0:
                    evidence.append(
                        HazardPreferenceEvidence(
                            edge_id=edge.id,
                            reason="Travel direction is downwind of the bushfire",
                            source_hazard_type="bushfire",
                            multiplier=multiplier,
                        )
                    )
        elevation_hazards = self._active_hazard_types.intersection({"cyclone", "flood", "tsunami"})
        if elevation_hazards:
            multiplier = self._relative_elevation_penalty(edge.elevation_m)
            if multiplier > 1.0:
                evidence.append(
                    HazardPreferenceEvidence(
                        edge_id=edge.id,
                        reason="Lower relative elevation than available alternatives",
                        source_hazard_type=",".join(sorted(elevation_hazards)),
                        multiplier=multiplier,
                    )
                )
        if "earthquake" in self._active_hazard_types and edge.earthquake_damage_status == "suspected":
            evidence.append(
                HazardPreferenceEvidence(
                    edge_id=edge.id,
                    reason="Suspected earthquake damage",
                    source_hazard_type="earthquake",
                    multiplier=2.0,
                )
            )
        return evidence

    def _relative_elevation_penalty(self, elevation_m: float | None) -> float:
        if elevation_m is None or self._elevation_range is None:
            return 1.0
        minimum, maximum = self._elevation_range
        if maximum <= minimum:
            return 1.0
        relative_risk = (maximum - elevation_m) / (maximum - minimum)
        return 1.0 + max(0.0, min(1.0, relative_risk))

    def _destination_risk_score(self, area: Any) -> float:
        score = 0.0
        if self._active_hazard_types.intersection({"cyclone", "flood", "tsunami"}):
            score += self._relative_elevation_penalty(area.elevation_m) - 1.0
        if "earthquake" in self._active_hazard_types and area.structural_status == "uninspected":
            score += 1.0
        return score

    def _travel_bearing(
        self,
        from_node_id: str,
        to_node_id: str,
    ) -> float | None:
        start = self._network.get_node(from_node_id)
        end = self._network.get_node(to_node_id)
        if start is None or end is None:
            return None
        longitude_delta = math.radians(end.coordinates.get("lng", 0) - start.coordinates.get("lng", 0))
        start_latitude = math.radians(start.coordinates.get("lat", 0))
        end_latitude = math.radians(end.coordinates.get("lat", 0))
        x = math.sin(longitude_delta) * math.cos(end_latitude)
        y = math.cos(start_latitude) * math.sin(end_latitude) - math.sin(start_latitude) * math.cos(
            end_latitude
        ) * math.cos(longitude_delta)
        if x == 0 and y == 0:
            return None
        return (math.degrees(math.atan2(x, y)) + 360.0) % 360.0

    @staticmethod
    def _bearing_delta(first: float, second: float) -> float:
        return abs((first - second + 180.0) % 360.0 - 180.0)
