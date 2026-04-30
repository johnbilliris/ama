"""Timeline estimation — phased evacuation timeline computation and shelter-in-place logic.

Computes 5-phase evacuation timelines, clearance times, shelter-in-place
recommendations, and time deficit detection.

Clearance time formula: ``(population / road_capacity) × distance_km × 60`` minutes.
Vulnerable population phases use a buffer multiplier (default 1.5×).
Phase transition: time-based primary, population-based secondary.
"""

from __future__ import annotations

import logging
from typing import Any

from evacuation.config import EvacuationConfig
from evacuation.models import EvacuationPhase

logger = logging.getLogger(__name__)


class ShelterInPlaceRecommendation:
    """Result of shelter-in-place decision logic."""

    def __init__(
        self,
        recommended: bool,
        zone_number: int,
        reason: str,
        is_emergency_escalation: bool = False,
    ) -> None:
        self.recommended = recommended
        self.zone_number = zone_number
        self.reason = reason
        self.is_emergency_escalation = is_emergency_escalation


class TimelineEstimator:
    """Computes phased evacuation timelines and shelter-in-place decisions."""

    def __init__(self, config: EvacuationConfig | None = None) -> None:
        self._config = config or EvacuationConfig()

    def estimate_timeline(
        self,
        zones: list[dict[str, Any]],
        routes: list[dict[str, Any]],
        transport_requirements: list[dict[str, Any]] | None = None,
        hazard_type: str = "bushfire",
        hazard_time_horizon_hours: float | None = None,
    ) -> tuple[list[EvacuationPhase], list[ShelterInPlaceRecommendation], list[str]]:
        """Compute 5-phase evacuation timeline.

        The five phases follow FR-015:
          1. Zone 1 vulnerable populations
          2. Zone 1 general population
          3. Zone 2 vulnerable populations
          4. Zone 2 general population
          5. Zone 3 advisory evacuation (all)

        Args:
            zones: Zone dicts with ``zone_number``, ``population_estimate``,
                ``vulnerable_population``.
            routes: Route dicts with ``origin_zone`` (or ``zone_id``),
                ``distance_km`` (or ``total_distance_km``),
                ``capacity_vehicles_per_hour``.
            transport_requirements: Optional transport requirement dicts.
            hazard_type: Hazard type for mobilisation time lookup.
            hazard_time_horizon_hours: Hours until hazard arrival (for time
                deficit detection).

        Returns:
            Tuple of (phases, shelter_recommendations, assumptions).
        """
        mobilisation_min = self._config.mobilisation_time_for(hazard_type)
        assumptions: list[str] = []
        shelter_recommendations: list[ShelterInPlaceRecommendation] = []

        # Sort zones by priority (Zone 1 first)
        sorted_zones = sorted(zones, key=lambda z: z.get("zone_number", 99))

        # Compute average route metrics per zone
        zone_metrics = self._compute_zone_route_metrics(sorted_zones, routes)

        phases: list[EvacuationPhase] = []
        # Running offset in minutes from plan start (includes mobilisation)
        current_offset_min = mobilisation_min
        phase_number = 0

        # 5-phase sequence per FR-015
        phase_definitions = [
            (1, "vulnerable", "Zone 1 vulnerable populations"),
            (1, "general", "Zone 1 general population"),
            (2, "vulnerable", "Zone 2 vulnerable populations"),
            (2, "general", "Zone 2 general population"),
            (3, "advisory", "Zone 3 advisory evacuation (all)"),
        ]

        for zone_num, pop_type, description in phase_definitions:
            phase_number += 1

            # Find zone data
            zone_data = next(
                (z for z in sorted_zones if z.get("zone_number") == zone_num),
                None,
            )

            if zone_data is None:
                # Zone not in scope — minimal phase
                phase = self._create_minimal_phase(
                    phase_number,
                    zone_num,
                    pop_type,
                    description,
                    current_offset_min,
                    mobilisation_min,
                )
                phases.append(phase)
                continue

            # Get population for this phase
            total_pop = zone_data.get("population_estimate", 0)
            vuln_pop = zone_data.get("vulnerable_population", 0)

            if pop_type == "vulnerable":
                phase_pop = vuln_pop
            elif pop_type == "advisory":
                phase_pop = total_pop
            else:
                phase_pop = max(0, total_pop - vuln_pop)

            # Get route metrics for this zone
            metrics = zone_metrics.get(zone_num, {})
            avg_distance: float = metrics.get("avg_distance_km", 10.0)
            total_capacity: int = metrics.get("total_capacity", 500)
            has_viable_routes: bool = metrics.get("has_routes", False)

            # Check if shelter-in-place is needed
            if not has_viable_routes and phase_pop > 0:
                sip = self._evaluate_shelter_in_place(
                    zone_num,
                    hazard_type,
                    hazard_time_horizon_hours,
                )
                shelter_recommendations.append(sip)
                if sip.is_emergency_escalation:
                    assumptions.append(
                        f"EMERGENCY: Zone {zone_num} has no viable evacuation routes "
                        f"and faces immediate threat. Emergency escalation recommended."
                    )

            # Compute clearance time
            buffer = self._config.vulnerable_population_buffer if pop_type == "vulnerable" else 1.0
            clearance_min = self._compute_clearance_time(
                population=phase_pop,
                road_capacity=total_capacity,
                distance_km=avg_distance,
                buffer_multiplier=buffer,
            )

            travel_min = (avg_distance / 30.0) * 60  # 30 km/h loaded speed

            phase_start_offset = current_offset_min
            duration = round(clearance_min)

            # Transition criteria
            time_threshold = clearance_min * self._config.phase_transition_time_factor
            pop_threshold = self._config.phase_transition_population_pct
            transition = f"Previous phase {pop_threshold}% complete OR elapsed time >= {time_threshold:.0f} min"

            # Enriched description with transition criteria and timing detail
            enriched_desc = (
                f"{description} | "
                f"Mobilisation: {mobilisation_min}min | "
                f"Travel: {travel_min:.0f}min | "
                f"Buffer: {buffer:.1f}x | "
                f"Transition: {transition}"
            )

            phase = EvacuationPhase(
                phase_number=phase_number,
                zone_ids=[str(zone_num)],
                start_offset_minutes=phase_start_offset,
                duration_minutes=duration,
                population_moved=phase_pop,
                description=enriched_desc,
            )
            phases.append(phase)

            # Time deficit detection
            if hazard_time_horizon_hours is not None:
                completion_offset_min = phase_start_offset + duration
                total_elapsed_hours = completion_offset_min / 60.0
                if total_elapsed_hours > hazard_time_horizon_hours:
                    assumptions.append(
                        f"TIME DEFICIT: Phase {phase_number} ({description}) "
                        f"completion at {total_elapsed_hours:.1f}h exceeds "
                        f"hazard arrival window of {hazard_time_horizon_hours:.1f}h. "
                        f"Shelter-in-place recommended for remaining population."
                    )

            current_offset_min = phase_start_offset + duration

        return phases, shelter_recommendations, assumptions

    def _compute_clearance_time(
        self,
        population: int,
        road_capacity: int,
        distance_km: float,
        buffer_multiplier: float = 1.0,
    ) -> float:
        """Compute clearance time using formula: (pop / capacity) × distance × 60 minutes.

        Args:
            population: Number of people to evacuate.
            road_capacity: Road capacity in vehicles per hour.
            distance_km: Average distance to assembly area.
            buffer_multiplier: Multiplier for vulnerable populations (default 1.5×).

        Returns:
            Clearance time in minutes.
        """
        if road_capacity <= 0 or population <= 0:
            return 0.0

        # Formula: (population / road_capacity) × distance_km × 60
        raw_time = (population / road_capacity) * distance_km * 60
        return raw_time * buffer_multiplier

    def _compute_zone_route_metrics(
        self,
        zones: list[dict[str, Any]],
        routes: list[dict[str, Any]],
    ) -> dict[int, dict[str, Any]]:
        """Compute average route metrics grouped by zone.

        Supports both ``origin_zone`` (int) and ``zone_id`` (str) keys in route
        dicts for compatibility with different callers.
        """
        metrics: dict[int, dict[str, Any]] = {}

        for zone in zones:
            zone_num = zone.get("zone_number", 0)
            zone_routes = [r for r in routes if _route_zone(r) == zone_num]

            if zone_routes:
                avg_dist = sum(_route_distance(r) for r in zone_routes) / len(zone_routes)
                total_cap = sum(r.get("capacity_vehicles_per_hour", 0) for r in zone_routes)
                metrics[zone_num] = {
                    "avg_distance_km": avg_dist,
                    "total_capacity": total_cap,
                    "has_routes": True,
                    "route_count": len(zone_routes),
                }
            else:
                metrics[zone_num] = {
                    "avg_distance_km": 10.0,
                    "total_capacity": 0,
                    "has_routes": False,
                    "route_count": 0,
                }

        return metrics

    def _evaluate_shelter_in_place(
        self,
        zone_number: int,
        hazard_type: str,
        hazard_time_horizon_hours: float | None,
    ) -> ShelterInPlaceRecommendation:
        """Evaluate whether shelter-in-place is appropriate.

        Decision tree:
        - No viable route + immediate threat → emergency escalation
        - No viable route + hazard timeline allows → shelter-in-place
        """
        # Immediate threat threshold: less than 2 hours for sudden-onset,
        # less than 4 hours for slower-onset
        immediate_threshold_hours = 2.0
        if hazard_type in ("flood", "cyclone"):
            immediate_threshold_hours = 4.0

        if hazard_time_horizon_hours is not None and hazard_time_horizon_hours < immediate_threshold_hours:
            return ShelterInPlaceRecommendation(
                recommended=False,
                zone_number=zone_number,
                reason=(
                    f"No viable evacuation routes for Zone {zone_number} "
                    f"and hazard arrival imminent ({hazard_time_horizon_hours:.1f}h). "
                    f"Emergency escalation required."
                ),
                is_emergency_escalation=True,
            )

        return ShelterInPlaceRecommendation(
            recommended=True,
            zone_number=zone_number,
            reason=(
                f"No viable evacuation routes for Zone {zone_number}. "
                f"Shelter-in-place recommended — hazard timeline allows "
                f"({hazard_time_horizon_hours or 'unknown'}h). "
                f"Seek strong building with interior rooms."
            ),
        )

    def _create_minimal_phase(
        self,
        phase_number: int,
        zone_number: int,
        population_type: str,
        description: str,
        start_offset_minutes: int,
        mobilisation_min: int,
    ) -> EvacuationPhase:
        """Create a minimal phase entry for zones with no data."""
        return EvacuationPhase(
            phase_number=phase_number,
            zone_ids=[str(zone_number)],
            start_offset_minutes=start_offset_minutes,
            duration_minutes=0,
            population_moved=0,
            description=(f"{description} | N/A — zone not in scope | Mobilisation: {mobilisation_min}min"),
        )

    def can_recover_from_shelter(
        self,
        zone_number: int,
        routes: list[dict[str, Any]],
    ) -> bool:
        """Check if shelter-in-place zone can be recovered to evacuation.

        Returns True if new viable routes exist for the zone.
        """
        zone_routes = [r for r in routes if _route_zone(r) == zone_number]
        return len(zone_routes) > 0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _route_zone(route: dict[str, Any]) -> int:
    """Extract zone number from a route dict, supporting both key conventions."""
    # Try origin_zone (int) first, then zone_id (str)
    oz = route.get("origin_zone")
    if oz is not None:
        return int(oz)
    zid = route.get("zone_id")
    if zid is not None:
        try:
            return int(zid)
        except (ValueError, TypeError):
            return 0
    return 0


def _route_distance(route: dict[str, Any]) -> float:
    """Extract distance from a route dict, supporting both key conventions."""
    return route.get("total_distance_km", route.get("distance_km", 0.0))
