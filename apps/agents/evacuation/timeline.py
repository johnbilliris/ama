"""Phased evacuation timelines and per-zone operational dispositions."""

from __future__ import annotations

import math
from datetime import datetime, timedelta
from typing import Any

from evacuation.config import EvacuationConfig
from evacuation.models import (
    EvacuationPhase,
    OriginCoverageStatus,
    PhasePopulationType,
    PhaseTransitionTrigger,
    ShelterRequirements,
    TransportRequirement,
    ZoneDisposition,
    ZoneDispositionType,
)


class TimelineEstimator:
    """Compute five-phase timelines and one reconciled disposition per zone."""

    def __init__(self, config: EvacuationConfig | None = None) -> None:
        self._config = config or EvacuationConfig()

    def estimate_timeline(
        self,
        zones: list[dict[str, Any]],
        routes: list[dict[str, Any]],
        transport_requirements: list[dict[str, Any]] | None = None,
        hazard_type: str = "bushfire",
        hazard_time_horizon_hours: float | None = None,
        corridor_loads: list[dict[str, Any]] | None = None,
        timeline_anchor: datetime | None = None,
    ) -> tuple[list[EvacuationPhase], list[ZoneDisposition], list[str]]:
        """Return phased movement, zone dispositions, and safety assumptions."""
        transport_by_phase: dict[int, list[TransportRequirement]] = {}
        for document in transport_requirements or []:
            requirement = TransportRequirement.model_validate(document)
            if requirement.phase_number is not None:
                transport_by_phase.setdefault(
                    requirement.phase_number,
                    [],
                ).append(requirement)
        mobilisation_min = self._config.mobilisation_time_for(hazard_type)
        assumptions: list[str] = []
        sorted_zones = sorted(zones, key=lambda zone: zone.get("zone_number", 99))
        zone_metrics = self._compute_zone_route_metrics(sorted_zones, routes)
        disposition_by_zone: dict[int, ZoneDisposition] = {}
        clearance_deficit_by_zone: dict[int, float] = {}

        for zone in sorted_zones:
            zone_number = int(zone.get("zone_number", 0))
            population = int(zone.get("population_estimate", 0))
            origin_coverage_status = OriginCoverageStatus(
                zone.get(
                    "origin_coverage_status",
                    OriginCoverageStatus.unassigned,
                )
            )
            if population > 0 and not zone_metrics[zone_number]["has_routes"]:
                disposition = self._evaluate_shelter_in_place(
                    zone_number=zone_number,
                    zone_id=str(zone.get("zone_id") or zone_number),
                    population=population,
                    hazard_type=hazard_type,
                    hazard_time_horizon_hours=hazard_time_horizon_hours,
                    origin_coverage_status=origin_coverage_status,
                )
                disposition_by_zone[zone_number] = disposition
                assumptions.append(disposition.rationale)

        phases: list[EvacuationPhase] = []
        current_offset_min = float(mobilisation_min)
        phase_edge_loads_by_number: dict[int, dict[str, float]] = {}
        corridor_limits = self._corridor_limits(routes, corridor_loads or [])
        phase_definitions = [
            (1, "vulnerable", "Zone 1 vulnerable populations"),
            (1, "general", "Zone 1 general population"),
            (2, "vulnerable", "Zone 2 vulnerable populations"),
            (2, "general", "Zone 2 general population"),
            (3, "advisory", "Zone 3 advisory evacuation (all)"),
        ]

        for phase_number, (zone_number, population_type, description) in enumerate(
            phase_definitions,
            start=1,
        ):
            matching_zones = [candidate for candidate in sorted_zones if candidate.get("zone_number") == zone_number]
            phase_zone = matching_zones[0] if matching_zones else None
            if phase_zone is None:
                phase = self._create_minimal_phase(
                    phase_number,
                    zone_number,
                    population_type,
                    description,
                    current_offset_min,
                    mobilisation_min,
                    timeline_anchor,
                )
                phases.append(phase)
                current_offset_min = phase.selected_transition_offset_minutes or current_offset_min
                continue

            total_population = int(phase_zone.get("population_estimate", 0))
            vulnerable_population = int(phase_zone.get("vulnerable_population", 0))
            unallocated_population = int(phase_zone.get("unallocated_route_population", 0))
            unallocated_vulnerable = int(phase_zone.get("unallocated_vulnerable_population", 0))
            if population_type == "vulnerable":
                phase_population = vulnerable_population
                phase_unallocated = unallocated_vulnerable
            elif population_type == "advisory":
                phase_population = total_population
                phase_unallocated = unallocated_population
            else:
                phase_population = max(0, total_population - vulnerable_population)
                phase_unallocated = max(
                    0,
                    unallocated_population - unallocated_vulnerable,
                )
            routable_population = max(0, phase_population - phase_unallocated)

            metrics = zone_metrics[zone_number]
            has_viable_routes = bool(metrics["has_routes"])
            phase_routes = [route for route in routes if _route_zone(route) == zone_number]
            route_allocation_snapshot = {
                str(route.get("route_id")): int(route.get("allocated_population", 0))
                for route in sorted(
                    phase_routes,
                    key=lambda item: str(item.get("route_id", "")),
                )
                if route.get("route_id")
            }
            phase_edge_loads = self._phase_edge_loads(
                phase_routes,
                routable_population,
            )
            phase_start_offset = self._capacity_safe_start(
                current_offset_min,
                phase_edge_loads,
                phases,
                phase_edge_loads_by_number,
                corridor_limits,
            )
            transition_delay = phase_start_offset - current_offset_min
            linked_transport = transport_by_phase.get(phase_number, [])
            buffered_transport_population = min(
                routable_population,
                sum(
                    requirement.estimated_individuals
                    for requirement in linked_transport
                    if requirement.destination_resolved
                ),
            )
            buffer = (
                1.0
                + (self._config.vulnerable_population_buffer - 1.0)
                * buffered_transport_population
                / routable_population
                if routable_population > 0
                else 1.0
            )
            travel_minutes = (
                float(metrics["avg_distance_km"]) / self._config.loaded_route_speed_kmh * 60
                if has_viable_routes
                else 0.0
            )
            clearance_minutes: float | None = None
            departure_rate = 0.0
            population_threshold = (
                math.ceil(phase_population * self._config.phase_transition_population_pct / 100)
                if phase_population > 0
                else 0
            )
            population_transition_offset: float | None = None
            time_transition_offset: float | None = None
            selected_transition_offset: float | None = None
            selected_trigger = PhaseTransitionTrigger.blocked

            if phase_population <= 0:
                duration: float | None = 0.0
                population_moved = 0
                population_remaining = 0
                clearance_blocked = False
                clearance_minutes = 0.0
                population_transition_offset = phase_start_offset
                time_transition_offset = phase_start_offset
                selected_transition_offset = phase_start_offset
                selected_trigger = PhaseTransitionTrigger.zero_population
                phase_description = f"{description} | No population assigned"
            elif not has_viable_routes:
                duration = None
                population_moved = 0
                population_remaining = phase_population
                clearance_blocked = True
                phase_description = (
                    f"{description} | Clearance blocked: no viable road capacity | See Zone {zone_number} disposition"
                )
            elif routable_population <= 0:
                duration = None
                population_moved = 0
                population_remaining = phase_population
                clearance_blocked = True
                phase_description = (
                    f"{description} | Clearance blocked: no verified destination capacity | "
                    f"See Zone {zone_number} disposition"
                )
            else:
                clearance_minutes = self._compute_clearance_time(
                    population=routable_population,
                    road_capacity=int(metrics["total_capacity"]),
                    distance_km=float(metrics["avg_distance_km"]),
                    buffer_multiplier=buffer,
                )
                available_minutes = clearance_minutes
                if hazard_time_horizon_hours is not None:
                    available_minutes = max(
                        0.0,
                        hazard_time_horizon_hours * 60 - phase_start_offset,
                    )
                effective_minutes = min(clearance_minutes, available_minutes)
                if effective_minutes >= clearance_minutes:
                    population_moved = routable_population
                else:
                    population_moved = int(routable_population * effective_minutes / clearance_minutes)
                population_remaining = phase_population - population_moved
                clearance_deficit_by_zone[zone_number] = clearance_deficit_by_zone.get(zone_number, 0.0) + max(
                    0.0, clearance_minutes - available_minutes
                )
                duration = math.ceil(effective_minutes) if effective_minutes > 0 else 0
                clearance_blocked = False
                departure_rate = routable_population / clearance_minutes if clearance_minutes > 0 else 0.0
                if departure_rate > 0 and population_threshold <= population_moved:
                    population_transition_offset = phase_start_offset + population_threshold / departure_rate
                time_transition_offset = (
                    phase_start_offset + clearance_minutes * self._config.phase_transition_time_factor
                )
                candidate_completion_offset = phase_start_offset + duration
                candidates = [
                    (
                        population_transition_offset,
                        PhaseTransitionTrigger.population_threshold,
                    ),
                    (
                        time_transition_offset,
                        PhaseTransitionTrigger.time_threshold,
                    ),
                    (
                        candidate_completion_offset,
                        PhaseTransitionTrigger.phase_completion,
                    ),
                ]
                selected_transition_offset, selected_trigger = min(
                    ((offset, trigger) for offset, trigger in candidates if offset is not None),
                    key=lambda item: (
                        item[0],
                        list(PhaseTransitionTrigger).index(item[1]),
                    ),
                )
                phase_description = (
                    f"{description} | Mobilisation: {mobilisation_min}min | "
                    f"Travel: {travel_minutes:.0f}min | Buffer: {buffer:.1f}x | "
                    f"Transition: {selected_trigger.value} at "
                    f"+{selected_transition_offset:.2f}min"
                )

            completion_offset = None if duration is None else phase_start_offset + duration
            starts_at = self._offset_timestamp(timeline_anchor, phase_start_offset)
            completes_at = self._offset_timestamp(timeline_anchor, completion_offset)
            transition_at = self._offset_timestamp(
                timeline_anchor,
                selected_transition_offset,
            )

            phase = EvacuationPhase(
                phase_number=phase_number,
                zone_ids=[str(zone_number)],
                zone_number=zone_number,
                population_type=PhasePopulationType(population_type),
                estimated_population=phase_population,
                routable_population=routable_population,
                start_offset_minutes=phase_start_offset,
                duration_minutes=duration,
                completion_offset_minutes=completion_offset,
                mobilisation_minutes=mobilisation_min,
                travel_minutes=travel_minutes,
                clearance_minutes=clearance_minutes,
                effective_capacity_vehicles_per_hour=int(metrics["total_capacity"]),
                estimated_departure_rate_people_per_minute=departure_rate,
                population_transition_threshold=population_threshold,
                population_transition_offset_minutes=(population_transition_offset),
                time_transition_offset_minutes=time_transition_offset,
                selected_transition_offset_minutes=(selected_transition_offset),
                selected_transition_trigger=selected_trigger,
                transition_delay_minutes=transition_delay,
                is_empty=phase_population == 0,
                buffer_multiplier=buffer,
                buffered_transport_population=(buffered_transport_population),
                route_edge_ids=sorted(phase_edge_loads),
                route_allocation_snapshot=route_allocation_snapshot,
                zone_shared_capacity_vehicles_per_hour=int(metrics["total_capacity"]),
                starts_at=starts_at,
                completes_at=completes_at,
                transition_at=transition_at,
                population_moved=population_moved,
                population_remaining=population_remaining,
                clearance_blocked=clearance_blocked,
                transport_requirements=linked_transport,
                description=phase_description,
            )
            phases.append(phase)
            phase_edge_loads_by_number[phase_number] = phase_edge_loads if duration not in (None, 0) else {}
            if population_remaining > 0 and has_viable_routes:
                assumptions.append(
                    f"TIME DEFICIT: Phase {phase_number} has a time or "
                    f"DESTINATION CAPACITY GAP; "
                    f"({description}) leaves {population_remaining} people unable "
                    "to clear using verified route and destination capacity."
                )
            current_offset_min = (
                selected_transition_offset if selected_transition_offset is not None else phase_start_offset
            )

        for zone in sorted_zones:
            zone_number = int(zone.get("zone_number", 0))
            if zone_number in disposition_by_zone:
                continue
            population = int(zone.get("population_estimate", 0))
            origin_coverage_status = OriginCoverageStatus(
                zone.get(
                    "origin_coverage_status",
                    OriginCoverageStatus.unassigned,
                )
            )
            zone_phases = [phase for phase in phases if str(zone_number) in phase.zone_ids]
            evacuating_population = min(
                population,
                sum(phase.population_moved for phase in zone_phases),
            )
            remaining_population = population - evacuating_population
            if remaining_population:
                disposition_type = ZoneDispositionType.partial_evacuation
                urgency = "critical"
                prerequisites = [
                    "Keep assigned evacuation routes open",
                    "Move the highest-risk cohorts before hazard arrival",
                    "Confirm shelter for the remaining population",
                ]
                requirements = self._shelter_requirements(hazard_type)
                rationale = (
                    f"Zone {zone_number} can evacuate {evacuating_population} of "
                    f"{population} people before hazard arrival; "
                    f"{remaining_population} require shelter."
                )
            else:
                disposition_type = ZoneDispositionType.evacuation
                urgency = "planned"
                prerequisites = ["Keep assigned evacuation routes open"]
                requirements = ShelterRequirements()
                rationale = f"Zone {zone_number} population can clear using viable routes."
            disposition_by_zone[zone_number] = ZoneDisposition(
                zone_id=str(zone.get("zone_id") or zone_number),
                zone_number=zone_number,
                disposition=disposition_type,
                urgency=urgency,
                affected_population=population,
                evacuating_population=evacuating_population,
                remaining_population=remaining_population,
                origin_coverage_status=origin_coverage_status,
                clearance_deficit_minutes=math.ceil(clearance_deficit_by_zone.get(zone_number, 0.0)),
                prerequisites=prerequisites,
                shelter_requirements=requirements,
                rationale=rationale,
            )

        dispositions = [disposition_by_zone[int(zone.get("zone_number", 0))] for zone in sorted_zones]
        return phases, dispositions, assumptions

    @staticmethod
    def plan_completion_minutes(
        phases: list[EvacuationPhase],
    ) -> int | None:
        if any(phase.estimated_population > 0 and phase.completion_offset_minutes is None for phase in phases):
            return None
        return math.ceil(
            max(
                (phase.completion_offset_minutes or 0.0 for phase in phases),
                default=0.0,
            )
        )

    def _phase_edge_loads(
        self,
        routes: list[dict[str, Any]],
        phase_population: int,
    ) -> dict[str, float]:
        if phase_population <= 0 or not routes:
            return {}
        allocations = [max(0, int(route.get("allocated_population", 0))) for route in routes]
        if sum(allocations) <= 0:
            allocations = [max(1, int(route.get("capacity_vehicles_per_hour", 0))) for route in routes]
        route_populations = self._largest_remainder(
            phase_population,
            allocations,
        )
        window_hours = self._config.route_allocation_window_minutes / 60
        edge_loads: dict[str, float] = {}
        for route, assigned_population in zip(
            routes,
            route_populations,
            strict=True,
        ):
            load = assigned_population / self._config.average_persons_per_vehicle / window_hours
            for edge_id in set(route.get("path", route.get("waypoints", []))):
                edge_loads[str(edge_id)] = edge_loads.get(str(edge_id), 0.0) + load
        return edge_loads

    @staticmethod
    def _largest_remainder(total: int, weights: list[int]) -> list[int]:
        if not weights:
            return []
        weight_total = sum(weights)
        if weight_total <= 0:
            return [0] * len(weights)
        raw = [total * weight / weight_total for weight in weights]
        values = [math.floor(item) for item in raw]
        remaining = total - sum(values)
        ranking = sorted(
            range(len(raw)),
            key=lambda index: (
                -(raw[index] - values[index]),
                index,
            ),
        )
        for index in ranking[:remaining]:
            values[index] += 1
        return values

    @staticmethod
    def _corridor_limits(
        routes: list[dict[str, Any]],
        corridor_loads: list[dict[str, Any]],
    ) -> dict[str, tuple[float, float]]:
        limits = {
            str(load.get("edge_id")): (
                float(load.get("capacity_vehicles_per_hour", 0)),
                float(load.get("current_traffic_load_vehicles_per_hour", 0)),
            )
            for load in corridor_loads
            if load.get("edge_id")
        }
        for route in routes:
            route_capacity = float(route.get("capacity_vehicles_per_hour", 0))
            for edge_id in route.get("path", route.get("waypoints", [])):
                key = str(edge_id)
                if key not in limits:
                    limits[key] = (route_capacity, 0.0)
                else:
                    capacity, background = limits[key]
                    if capacity <= 0 or (route_capacity > 0 and route_capacity < capacity):
                        limits[key] = (route_capacity, background)
        return limits

    @staticmethod
    def _capacity_safe_start(
        candidate_start: float,
        current_loads: dict[str, float],
        prior_phases: list[EvacuationPhase],
        phase_loads_by_number: dict[int, dict[str, float]],
        corridor_limits: dict[str, tuple[float, float]],
    ) -> float:
        start = candidate_start
        while True:
            conflicting_completion_offsets: list[float] = []
            for edge_id, current_load in current_loads.items():
                capacity, background = corridor_limits.get(
                    edge_id,
                    (float("inf"), 0.0),
                )
                if capacity <= 0 or background + current_load > capacity:
                    continue
                overlapping = [
                    phase
                    for phase in prior_phases
                    if phase.completion_offset_minutes is not None
                    and phase.start_offset_minutes <= start < phase.completion_offset_minutes
                    and phase_loads_by_number.get(phase.phase_number, {}).get(
                        edge_id,
                        0.0,
                    )
                    > 0
                ]
                prior_load = sum(phase_loads_by_number[phase.phase_number][edge_id] for phase in overlapping)
                if background + current_load + prior_load > capacity:
                    conflicting_completion_offsets.extend(
                        float(phase.completion_offset_minutes) for phase in overlapping
                    )
            if not conflicting_completion_offsets:
                return start
            next_start = min(offset for offset in conflicting_completion_offsets if offset > start)
            if next_start <= start:
                return start
            start = next_start

    @staticmethod
    def _offset_timestamp(
        anchor: datetime | None,
        offset_minutes: float | None,
    ) -> datetime | None:
        if anchor is None or offset_minutes is None:
            return None
        if anchor.tzinfo is None:
            raise ValueError("Timeline anchor must be timezone-aware")
        return anchor + timedelta(minutes=offset_minutes)

    def _compute_clearance_time(
        self,
        population: int,
        road_capacity: int,
        distance_km: float,
        buffer_multiplier: float = 1.0,
    ) -> float:
        """Compute clearance minutes, returning infinity for blocked movement."""
        if population <= 0:
            return 0.0
        if road_capacity <= 0:
            return float("inf")
        return population / road_capacity * distance_km * 60 * buffer_multiplier

    def _compute_zone_route_metrics(
        self,
        zones: list[dict[str, Any]],
        routes: list[dict[str, Any]],
    ) -> dict[int, dict[str, Any]]:
        metrics: dict[int, dict[str, Any]] = {}
        for zone in zones:
            zone_number = int(zone.get("zone_number", 0))
            viable_routes = [
                route
                for route in routes
                if _route_zone(route) == zone_number
                and int(route.get("capacity_vehicles_per_hour", 0)) > 0
                and ("allocated_population" not in route or int(route.get("allocated_population", 0)) > 0)
            ]
            if viable_routes:
                shared_capacities = [
                    int(route.get("zone_shared_capacity_vehicles_per_hour", 0))
                    for route in viable_routes
                    if int(route.get("zone_shared_capacity_vehicles_per_hour", 0)) > 0
                ]
                allocated_population = sum(int(route.get("allocated_population", 0)) for route in viable_routes)
                if allocated_population > 0:
                    average_distance = (
                        sum(
                            _route_distance(route) * int(route.get("allocated_population", 0))
                            for route in viable_routes
                        )
                        / allocated_population
                    )
                else:
                    average_distance = sum(_route_distance(route) for route in viable_routes) / len(viable_routes)
                metrics[zone_number] = {
                    "avg_distance_km": average_distance,
                    "total_capacity": (
                        max(shared_capacities)
                        if shared_capacities
                        else sum(int(route.get("capacity_vehicles_per_hour", 0)) for route in viable_routes)
                    ),
                    "has_routes": True,
                    "route_count": len(viable_routes),
                }
            else:
                metrics[zone_number] = {
                    "avg_distance_km": 10.0,
                    "total_capacity": 0,
                    "has_routes": False,
                    "route_count": 0,
                }
        return metrics

    def _evaluate_shelter_in_place(
        self,
        *,
        zone_number: int,
        zone_id: str,
        population: int,
        hazard_type: str,
        hazard_time_horizon_hours: float | None,
        origin_coverage_status: OriginCoverageStatus,
    ) -> ZoneDisposition:
        immediate_threshold_hours = 4.0 if hazard_type in {"flood", "cyclone"} else 2.0
        requirements = self._shelter_requirements(hazard_type)
        if hazard_time_horizon_hours is None or hazard_time_horizon_hours < immediate_threshold_hours:
            horizon = "unknown" if hazard_time_horizon_hours is None else f"{hazard_time_horizon_hours:.1f}h"
            return ZoneDisposition(
                zone_id=zone_id,
                zone_number=zone_number,
                disposition=ZoneDispositionType.emergency_escalation,
                urgency="maximum",
                affected_population=population,
                evacuating_population=0,
                remaining_population=population,
                origin_coverage_status=origin_coverage_status,
                prerequisites=[
                    "Authorized emergency-services operator intervention required",
                    "Do not issue a public evacuation order without incident commander approval",
                ],
                shelter_requirements=requirements,
                rationale=(
                    f"EMERGENCY: Zone {zone_number} "
                    f"{self._route_gap_description(origin_coverage_status)} "
                    f"and hazard arrival is {horizon}. Maximum-urgency escalation required."
                ),
            )
        return ZoneDisposition(
            zone_id=zone_id,
            zone_number=zone_number,
            disposition=ZoneDispositionType.shelter_in_place,
            urgency="urgent",
            affected_population=population,
            evacuating_population=0,
            remaining_population=population,
            origin_coverage_status=origin_coverage_status,
            prerequisites=[
                "Confirm each nominated building is outside immediate structural danger",
                "Maintain emergency-services monitoring for route recovery",
            ],
            shelter_requirements=requirements,
            rationale=(
                f"Zone {zone_number} {self._route_gap_description(origin_coverage_status)}. "
                f"Shelter-in-place recommended because the "
                f"{hazard_time_horizon_hours:.1f}h hazard window allows it."
            ),
        )

    @staticmethod
    def _route_gap_description(
        origin_coverage_status: OriginCoverageStatus,
    ) -> str:
        if origin_coverage_status == OriginCoverageStatus.no_network_origin:
            return "has no road-network origin within its exclusive membership"
        return "has no viable evacuation routes"

    @staticmethod
    def _shelter_requirements(hazard_type: str) -> ShelterRequirements:
        building = [
            "Use a structurally sound building with a protected interior area",
        ]
        if hazard_type == "flood":
            building.append("Move above forecast flood level without entering roof spaces")
        elif hazard_type in {"bushfire", "cyclone"}:
            building.append("Close openings and shelter away from windows")
        return ShelterRequirements(
            building=building,
            supplies=[
                "Maintain drinking water, essential medication, first aid, and battery lighting",
            ],
            communication=[
                "Keep a charged radio or phone for verified emergency-services instructions",
                "Report building failure or medical emergencies to emergency services",
            ],
        )

    @staticmethod
    def _create_minimal_phase(
        phase_number: int,
        zone_number: int,
        population_type: str,
        description: str,
        start_offset_minutes: float,
        mobilisation_min: int,
        timeline_anchor: datetime | None,
    ) -> EvacuationPhase:
        return EvacuationPhase(
            phase_number=phase_number,
            zone_ids=[str(zone_number)],
            zone_number=zone_number,
            population_type=PhasePopulationType(population_type),
            start_offset_minutes=start_offset_minutes,
            duration_minutes=0.0,
            completion_offset_minutes=start_offset_minutes,
            mobilisation_minutes=mobilisation_min,
            selected_transition_offset_minutes=start_offset_minutes,
            selected_transition_trigger=PhaseTransitionTrigger.zero_population,
            is_empty=True,
            starts_at=TimelineEstimator._offset_timestamp(
                timeline_anchor,
                start_offset_minutes,
            ),
            completes_at=TimelineEstimator._offset_timestamp(
                timeline_anchor,
                start_offset_minutes,
            ),
            transition_at=TimelineEstimator._offset_timestamp(
                timeline_anchor,
                start_offset_minutes,
            ),
            population_moved=0,
            population_remaining=0,
            description=(f"{description} | N/A - zone not in scope | Mobilisation: {mobilisation_min}min"),
        )

    def can_recover_from_shelter(
        self,
        zone_number: int,
        routes: list[dict[str, Any]],
    ) -> bool:
        return any(
            _route_zone(route) == zone_number and int(route.get("capacity_vehicles_per_hour", 0)) > 0
            for route in routes
        )


def _route_zone(route: dict[str, Any]) -> int:
    origin_zone = route.get("origin_zone")
    if origin_zone is not None:
        return int(origin_zone)
    zone_id = route.get("zone_id")
    if zone_id is not None:
        try:
            return int(zone_id)
        except (ValueError, TypeError):
            return 0
    return 0


def _route_distance(route: dict[str, Any]) -> float:
    return float(route.get("total_distance_km", route.get("distance_km", 0.0)))
