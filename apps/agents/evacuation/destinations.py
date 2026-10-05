"""Deterministic shared assembly-area capacity allocation."""

from __future__ import annotations

import math
from dataclasses import dataclass

from evacuation.models import (
    DestinationAllocation,
    EvacuationRoute,
    UnresolvedDestinationDemand,
)
from evacuation.road_network import AssemblyAreaConfig, RoadNetworkLoader


@dataclass(frozen=True)
class DestinationAllocationResult:
    allocations: list[DestinationAllocation]
    unresolved: list[UnresolvedDestinationDemand]
    unallocated_population_by_zone: dict[int, int]
    unallocated_vulnerable_population_by_zone: dict[int, int]


class DestinationAllocator:
    """Allocate zone populations over route-backed assembly areas once."""

    def __init__(self, road_network: RoadNetworkLoader) -> None:
        self._network = road_network

    def allocate(
        self,
        routes: list[EvacuationRoute],
        population_by_zone: dict[int, int],
        vulnerable_population_by_zone: dict[int, int] | None = None,
    ) -> DestinationAllocationResult:
        vulnerable_by_zone = vulnerable_population_by_zone or {}
        areas = {area.assembly_area_id: area for area in self._network.get_assembly_areas()}
        residual = {
            area_id: (
                None
                if area.current_occupancy_persons is None
                else area.capacity_persons - area.current_occupancy_persons
            )
            for area_id, area in areas.items()
        }
        ordered_routes = sorted(routes, key=self._route_key)
        allocations: list[DestinationAllocation] = []
        unresolved: list[UnresolvedDestinationDemand] = []
        unallocated_by_zone: dict[int, int] = {}
        unallocated_vulnerable_by_zone: dict[int, int] = {}

        for route in ordered_routes:
            route.allocated_population = 0

        for zone_number, population in sorted(population_by_zone.items()):
            zone_routes = [
                route
                for route in ordered_routes
                if int(route.zone_id) == zone_number
                and route.assembly_area_id in areas
                and self._area_accepts_zone(areas[route.assembly_area_id], zone_number)
            ]
            by_area = self._routes_by_area(zone_routes)
            known_capacity_areas = [
                area_id
                for area_id in sorted(by_area)
                if (remaining_capacity := residual.get(area_id)) is not None and remaining_capacity > 0
            ]
            unknown_capacity_areas = [area_id for area_id in sorted(by_area) if residual.get(area_id) is None]
            vulnerable_population = min(
                population,
                max(0, vulnerable_by_zone.get(zone_number, 0)),
            )
            accessible_areas = [
                area_id
                for area_id in known_capacity_areas
                if "wheelchair_accessible" in areas[area_id].accessibility_features
                and any(route.vehicle_suitability.accessible for route in by_area[area_id])
            ]
            vulnerable_allocations = self._allocate_to_areas(
                vulnerable_population,
                accessible_areas,
                by_area,
                residual,
            )
            assigned_vulnerable = sum(vulnerable_allocations.values())
            remaining_general = population - vulnerable_population
            general_allocations = self._allocate_to_areas(
                remaining_general,
                known_capacity_areas,
                by_area,
                residual,
            )

            assigned_by_area = {
                area_id: vulnerable_allocations.get(area_id, 0) + general_allocations.get(area_id, 0)
                for area_id in known_capacity_areas
            }
            for area_id in sorted(assigned_by_area):
                assigned = assigned_by_area[area_id]
                if assigned <= 0:
                    continue
                area = areas[area_id]
                remaining_capacity = residual[area_id]
                if remaining_capacity is None:
                    raise RuntimeError(f"Known-capacity area {area_id} lost its verified capacity")
                before = remaining_capacity + assigned
                area_routes = by_area[area_id]
                route_allocations = self._largest_remainder(
                    assigned,
                    [self._route_weight(route) for route in area_routes],
                )
                for route, route_population in zip(
                    area_routes,
                    route_allocations,
                    strict=True,
                ):
                    route.allocated_population += route_population
                allocations.append(
                    DestinationAllocation(
                        assembly_area_id=area_id,
                        assembly_area_name=area.name,
                        zone_number=zone_number,
                        assigned_population=assigned,
                        assigned_vulnerable_population=(vulnerable_allocations.get(area_id, 0)),
                        residual_capacity_before=before,
                        residual_capacity_after=residual[area_id],
                        route_ids=[route.route_id for route in area_routes],
                        accessibility_features=area.accessibility_features,
                    )
                )

            vulnerable_shortfall = vulnerable_population - assigned_vulnerable
            general_shortfall = remaining_general - sum(general_allocations.values())
            if vulnerable_shortfall:
                unresolved.append(
                    UnresolvedDestinationDemand(
                        zone_number=zone_number,
                        population=vulnerable_shortfall,
                        vulnerable_population=vulnerable_shortfall,
                        reason=(
                            "no_reachable_destination"
                            if not by_area
                            else (
                                "capacity_unverified"
                                if unknown_capacity_areas and not accessible_areas
                                else "no_accessible_capacity"
                            )
                        ),
                        details=(
                            "Vulnerable population has no reachable accessible "
                            "assembly area with verified residual capacity"
                        ),
                    )
                )
            if general_shortfall:
                unresolved.append(
                    UnresolvedDestinationDemand(
                        zone_number=zone_number,
                        population=general_shortfall,
                        reason=(
                            "capacity_unverified"
                            if unknown_capacity_areas and not known_capacity_areas
                            else ("no_reachable_destination" if not by_area else "capacity_exhausted")
                        ),
                        details=("General population has no reachable assembly area with verified residual capacity"),
                    )
                )
            unallocated_by_zone[zone_number] = vulnerable_shortfall + general_shortfall
            unallocated_vulnerable_by_zone[zone_number] = vulnerable_shortfall

        return DestinationAllocationResult(
            allocations=allocations,
            unresolved=unresolved,
            unallocated_population_by_zone=unallocated_by_zone,
            unallocated_vulnerable_population_by_zone=(unallocated_vulnerable_by_zone),
        )

    def _allocate_to_areas(
        self,
        population: int,
        area_ids: list[str],
        routes_by_area: dict[str, list[EvacuationRoute]],
        residual: dict[str, int | None],
    ) -> dict[str, int]:
        allocations = {area_id: 0 for area_id in area_ids}
        remaining = population
        active = list(area_ids)
        while remaining > 0 and active:
            weights = [sum(self._route_weight(route) for route in routes_by_area[area_id]) for area_id in active]
            proposed = self._largest_remainder(remaining, weights)
            progressed = 0
            for area_id, amount in zip(active, proposed, strict=True):
                capacity = int(residual[area_id] or 0)
                assigned = min(amount, capacity)
                allocations[area_id] += assigned
                residual[area_id] = capacity - assigned
                remaining -= assigned
                progressed += assigned
            active = [area_id for area_id in active if int(residual[area_id] or 0) > 0]
            if progressed == 0:
                break
        return allocations

    @staticmethod
    def _area_accepts_zone(area: AssemblyAreaConfig, zone_number: int) -> bool:
        return bool(area.assigned_zones) and zone_number in area.assigned_zones

    @staticmethod
    def _routes_by_area(
        routes: list[EvacuationRoute],
    ) -> dict[str, list[EvacuationRoute]]:
        grouped: dict[str, list[EvacuationRoute]] = {}
        for route in routes:
            grouped.setdefault(route.assembly_area_id, []).append(route)
        return grouped

    @staticmethod
    def _route_key(
        route: EvacuationRoute,
    ) -> tuple[int, float, float, float, str, str, tuple[str, ...]]:
        return (
            int(route.zone_id),
            route.hazard_risk_score,
            route.estimated_travel_time_loaded_min,
            route.total_distance_km,
            route.assembly_area_id,
            route.origin_node_id,
            tuple(route.path),
        )

    @staticmethod
    def _route_weight(route: EvacuationRoute) -> float:
        return max(1.0, float(route.capacity_vehicles_per_hour))

    @staticmethod
    def _largest_remainder(total: int, weights: list[float]) -> list[int]:
        if not weights:
            return []
        weight_total = sum(weights)
        if weight_total <= 0:
            weights = [1.0] * len(weights)
            weight_total = float(len(weights))
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
