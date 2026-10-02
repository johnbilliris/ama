"""Transport coordination — vulnerable population identification and vehicle estimation.

Identifies facilities within evacuation zones and generates TransportRequirement
records with vehicle types, quantities, pickup locations, and priority levels.

Four vulnerability categories are supported:
- mobility_impaired → wheelchair_accessible_vehicle (priority: immediate)
- medical_dependent → ambulance (priority: critical)
- elderly_aged_care → accessible_bus (priority: immediate)
- children_schools_childcare → bus (priority: high)
"""

from __future__ import annotations

import hashlib
import logging
from typing import Any

from evacuation.config import EvacuationConfig
from evacuation.models import (
    TransportCoordinationResult,
    TransportCoordinationStatus,
    TransportExclusionReason,
    TransportGroupExclusion,
    TransportPriority,
    TransportRequirement,
    VulnerabilityCategory,
)

logger = logging.getLogger(__name__)

# Vehicle type mapping per vulnerability category
VEHICLE_TYPE_MAP: dict[str, str] = {
    "mobility_impaired": "wheelchair_accessible_vehicle",
    "medical_dependent": "ambulance",
    "elderly_aged_care": "accessible_bus",
    "children_schools_childcare": "bus",
}

# Priority level mapping per vulnerability category
PRIORITY_MAP: dict[str, str] = {
    "mobility_impaired": "immediate",
    "medical_dependent": "critical",
    "elderly_aged_care": "immediate",
    "children_schools_childcare": "high",
}

# Vehicle capacity for estimation (persons per vehicle)
VEHICLE_CAPACITY: dict[str, int] = {
    "bus": 50,
    "wheelchair_accessible_vehicle": 4,
    "ambulance": 2,
    "medical_transport": 6,
    "accessible_bus": 50,
}

# Map vulnerability category to special considerations
SPECIAL_CONSIDERATIONS: dict[str, list[str]] = {
    "mobility_impaired": ["wheelchair_users", "mobility_equipment"],
    "medical_dependent": [
        "medical_equipment",
        "oxygen_supply",
        "continuous_monitoring",
    ],
    "elderly_aged_care": ["mobility_assistance", "medication_management"],
    "children_schools_childcare": [
        "child_supervision",
        "guardian_notification",
        "headcount_verification",
    ],
}

# Priority ordering for sort (lower = higher priority)
_PRIORITY_ORDER: dict[str, int] = {"critical": 0, "immediate": 1, "high": 2}


class TransportCoordinator:
    """Coordinates transport requirements for vulnerable populations."""

    def __init__(self, config: EvacuationConfig | None = None) -> None:
        self._config = config or EvacuationConfig()

    def compute_transport_requirements(
        self,
        zones: list[dict[str, Any]],
        facilities: list[dict[str, Any]],
        assembly_areas: list[dict[str, Any]],
    ) -> list[TransportRequirement]:
        """Return actionable requests for legacy list callers."""
        return self.coordinate_transport(
            zones,
            facilities,
            assembly_areas,
        ).requirements

    def coordinate_transport(
        self,
        zones: list[dict[str, Any]],
        facilities: list[dict[str, Any]] | None,
        assembly_areas: list[dict[str, Any]],
        incident_scope_key: str = "",
        destination_allocations: list[dict[str, Any]] | None = None,
        routes: list[dict[str, Any]] | None = None,
    ) -> TransportCoordinationResult:
        """Generate requests and reconcile identified vulnerable coverage.

        Args:
            zones: List of zone dicts with zone_number and boundary.
            facilities: List of facility dicts from population data.  Each should
                contain keys: ``vulnerability_category``, ``capacity``, ``name``,
                ``coordinates`` (``{lat, lng}``), and optionally
                ``special_considerations``.
            assembly_areas: List of assembly area dicts with ``assembly_area_id``,
                ``name``, and ``coordinates``.

        Zone 3 facilities remain advisory inventory and never generate a
        mandatory Resource Allocation request.
        """
        if facilities is None:
            return TransportCoordinationResult(
                status=TransportCoordinationStatus.unavailable,
                assumptions=["Facility registry unavailable; vulnerable transport needs are incomplete"],
                uncovered_vulnerable_population_by_zone={
                    int(zone.get("zone_number", 0)): int(zone.get("vulnerable_population", 0))
                    for zone in zones
                    if int(zone.get("zone_number", 0)) in {1, 2}
                },
            )
        if not facilities:
            return TransportCoordinationResult(
                status=TransportCoordinationStatus.complete,
                assumptions=["Facility registry contains no vulnerable facilities"],
                uncovered_vulnerable_population_by_zone={
                    int(zone.get("zone_number", 0)): int(zone.get("vulnerable_population", 0))
                    for zone in zones
                    if int(zone.get("zone_number", 0)) in {1, 2}
                },
            )

        requirements: list[TransportRequirement] = []
        exclusions: list[TransportGroupExclusion] = []
        identified_by_zone: dict[int, int] = {}
        assumptions: list[str] = []
        remaining_vulnerable_capacity = {
            (
                int(allocation.get("zone_number", 0)),
                str(allocation.get("assembly_area_id", "")),
            ): int(allocation.get("assigned_vulnerable_population", 0))
            for allocation in destination_allocations or []
        }

        for facility in sorted(facilities, key=self._facility_sort_key):
            facility_id = self._facility_id(facility)
            facility_name = str(facility.get("name") or "Unknown facility")
            population = self._facility_population(facility)
            if population is None:
                exclusions.append(
                    TransportGroupExclusion(
                        facility_id=facility_id,
                        facility_name=facility_name,
                        reason=TransportExclusionReason.invalid_population,
                        details="Facility capacity must be a positive integer",
                    )
                )
                continue
            zone_number, location_error = self._locate_facility_zone(
                facility,
                zones,
            )
            if location_error:
                exclusions.append(
                    TransportGroupExclusion(
                        facility_id=facility_id,
                        facility_name=facility_name,
                        estimated_individuals=population,
                        reason=TransportExclusionReason.invalid_location,
                        details=location_error,
                    )
                )
                continue
            if zone_number is None:
                exclusions.append(
                    TransportGroupExclusion(
                        facility_id=facility_id,
                        facility_name=facility_name,
                        estimated_individuals=population,
                        reason=TransportExclusionReason.outside_affected_area,
                        details="Facility is outside all exclusive zone memberships",
                    )
                )
                continue

            identified_by_zone[zone_number] = identified_by_zone.get(zone_number, 0) + population
            if zone_number == 3:
                exclusions.append(
                    TransportGroupExclusion(
                        facility_id=facility_id,
                        facility_name=facility_name,
                        estimated_individuals=population,
                        reason=TransportExclusionReason.advisory_only,
                        zone_number=3,
                        details="Zone 3 is advisory and creates no mandatory transport request",
                    )
                )
                continue

            vuln_category = facility.get("vulnerability_category", "")
            if vuln_category not in VEHICLE_TYPE_MAP:
                exclusions.append(
                    TransportGroupExclusion(
                        facility_id=facility_id,
                        facility_name=facility_name,
                        estimated_individuals=population,
                        reason=TransportExclusionReason.unknown_category,
                        zone_number=zone_number,
                        details=f"Unsupported vulnerability category: {vuln_category or 'missing'}",
                    )
                )
                continue

            vehicle_type = VEHICLE_TYPE_MAP[vuln_category]
            priority = PRIORITY_MAP[vuln_category]
            vehicle_capacity = VEHICLE_CAPACITY.get(vehicle_type, 50)
            estimated_vehicles = -(-population // vehicle_capacity)
            unresolved_destination_reason: str | None = None
            selected_route_id = ""
            if destination_allocations is None:
                nearest_aa = self._find_nearest_assembly_area(
                    facility,
                    assembly_areas,
                )
            else:
                nearest_aa, selected_route_id = self._find_allocated_destination(
                    zone_number=zone_number,
                    population=population,
                    vehicle_type=vehicle_type,
                    assembly_areas=assembly_areas,
                    routes=routes or [],
                    remaining_vulnerable_capacity=remaining_vulnerable_capacity,
                )
                if nearest_aa is None:
                    unresolved_destination_reason = (
                        "No route-backed compatible assembly area has sufficient verified allocated capacity"
                    )
            if nearest_aa is None:
                assumptions.append(
                    f"Transport request for {facility_id} has an unresolved "
                    "destination: "
                    + (unresolved_destination_reason or "No assembly area is available for transport coordination")
                )

            # Gather special considerations
            special = list(SPECIAL_CONSIDERATIONS.get(vuln_category, []))
            facility_special = facility.get("special_considerations", [])
            for s in facility_special:
                if s not in special:
                    special.append(s)

            dest_name = (
                nearest_aa.get("name", nearest_aa.get("assembly_area_id", ""))
                if nearest_aa is not None
                else "Unresolved"
            )
            coords = facility.get("coordinates", {})
            coord_str = f"({coords.get('lat', 0):.4f}, {coords.get('lng', 0):.4f})" if coords else ""
            special_str = ", ".join(special) if special else "none"

            notes = (
                f"Priority: {priority} | "
                f"Pickup: {facility_name} {coord_str} | "
                f"Destination: {dest_name} | "
                f"Individuals: {population} | "
                f"Zone: {zone_number} | "
                f"Considerations: {special_str}"
            )

            requirement = TransportRequirement(
                requirement_id=self._requirement_id(
                    incident_scope_key,
                    facility_id,
                    vuln_category,
                    vehicle_type,
                ),
                facility_id=facility_id,
                facility_name=facility_name,
                category=VulnerabilityCategory(vuln_category),
                vehicle_type=vehicle_type,
                estimated_individuals=population,
                quantity_required=estimated_vehicles,
                estimated_trips=1,
                pickup_location={
                    "lat": float(coords["lat"]),
                    "lng": float(coords["lng"]),
                },
                destination_assembly_area_id=str(
                    nearest_aa.get("assembly_area_id", "") if nearest_aa is not None else ""
                ),
                destination_assembly_area_name=str(dest_name),
                destination_route_id=selected_route_id,
                destination_resolved=nearest_aa is not None,
                unresolved_destination_reason=unresolved_destination_reason,
                priority_level=TransportPriority(priority),
                origin_zone=zone_number,
                phase_number=1 if zone_number == 1 else 3,
                special_considerations=special,
                notes=notes,
            )
            requirements.append(requirement)

        # Sort by priority: critical > immediate > high
        requirements.sort(
            key=lambda r: (
                _PRIORITY_ORDER.get(PRIORITY_MAP.get(r.category.value, "high"), 3),
                r.origin_zone,
                r.facility_id,
            )
        )

        uncovered_by_zone: dict[int, int] = {}
        for zone in zones:
            zone_number = int(zone.get("zone_number", 0))
            if zone_number not in {1, 2}:
                continue
            vulnerable_population = int(zone.get("vulnerable_population", 0))
            identified = identified_by_zone.get(zone_number, 0)
            uncovered_by_zone[zone_number] = max(
                0,
                vulnerable_population - identified,
            )
            if identified > vulnerable_population:
                assumptions.append(
                    f"Zone {zone_number} facility population {identified} exceeds "
                    f"the authoritative vulnerable estimate {vulnerable_population}"
                )
            elif uncovered_by_zone[zone_number]:
                assumptions.append(
                    f"Zone {zone_number} has {uncovered_by_zone[zone_number]} "
                    "vulnerable people without facility-specific transport records"
                )

        status = (
            TransportCoordinationStatus.complete
            if (
                not exclusions
                and not any(uncovered_by_zone.values())
                and not assumptions
                and all(requirement.destination_resolved for requirement in requirements)
            )
            else TransportCoordinationStatus.partial
        )
        return TransportCoordinationResult(
            status=status,
            requirements=requirements,
            exclusions=exclusions,
            identified_population_by_zone=identified_by_zone,
            uncovered_vulnerable_population_by_zone=uncovered_by_zone,
            assumptions=assumptions,
        )

    @staticmethod
    def _facility_sort_key(facility: dict[str, Any]) -> tuple:
        category = str(facility.get("vulnerability_category", ""))
        return (
            _PRIORITY_ORDER.get(PRIORITY_MAP.get(category, "high"), 3),
            str(facility.get("facility_id") or facility.get("name") or ""),
        )

    def _find_allocated_destination(
        self,
        *,
        zone_number: int,
        population: int,
        vehicle_type: str,
        assembly_areas: list[dict[str, Any]],
        routes: list[dict[str, Any]],
        remaining_vulnerable_capacity: dict[tuple[int, str], int],
    ) -> tuple[dict[str, Any] | None, str]:
        area_by_id = {str(area.get("assembly_area_id", "")): area for area in assembly_areas}
        route_metrics: dict[str, tuple[tuple[float, float, str], str]] = {}
        for route in routes:
            if int(route.get("origin_zone", route.get("zone_id", 0))) != zone_number:
                continue
            if not self._vehicle_route_compatible(vehicle_type, route):
                continue
            area_id = str(
                route.get(
                    "destination_assembly_area",
                    route.get("assembly_area_id", ""),
                )
            )
            metric = (
                float(route.get("estimated_travel_time_loaded_min", 0)),
                float(route.get("total_distance_km", route.get("distance_km", 0))),
                str(route.get("route_id", "")),
            )
            candidate = (metric, str(route.get("route_id", "")))
            route_metrics[area_id] = min(
                route_metrics.get(area_id, candidate),
                candidate,
            )

        candidates = []
        for (allocation_zone, area_id), remaining in remaining_vulnerable_capacity.items():
            if allocation_zone != zone_number or remaining < population:
                continue
            area = area_by_id.get(area_id)
            if area is None or area_id not in route_metrics:
                continue
            if not self._vehicle_destination_compatible(vehicle_type, area):
                continue
            candidates.append(
                (
                    route_metrics[area_id][0],
                    area_id,
                    route_metrics[area_id][1],
                    area,
                )
            )
        if not candidates:
            return None, ""
        _, area_id, route_id, selected = min(candidates)
        remaining_vulnerable_capacity[(zone_number, area_id)] -= population
        return selected, route_id

    @staticmethod
    def _vehicle_destination_compatible(
        vehicle_type: str,
        assembly_area: dict[str, Any],
    ) -> bool:
        features = set(assembly_area.get("accessibility_features", []))
        if vehicle_type in {"wheelchair_accessible_vehicle", "accessible_bus"}:
            return "wheelchair_accessible" in features
        if vehicle_type == "ambulance":
            return "medical_facilities" in features
        return True

    @staticmethod
    def _vehicle_route_compatible(
        vehicle_type: str,
        route: dict[str, Any],
    ) -> bool:
        suitability = route.get("vehicle_suitability", {})
        if vehicle_type in {"wheelchair_accessible_vehicle", "accessible_bus"}:
            return bool(suitability.get("accessible", False))
        if vehicle_type in {"bus", "ambulance", "medical_transport"}:
            return bool(suitability.get("standard", True))
        return False

    @staticmethod
    def _facility_population(facility: dict[str, Any]) -> int | None:
        value = facility.get("capacity")
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            return None
        return value

    @staticmethod
    def _facility_id(facility: dict[str, Any]) -> str:
        identifier = str(facility.get("facility_id") or "").strip()
        if identifier:
            return identifier
        identity = "|".join(
            [
                str(facility.get("name") or "unknown"),
                str((facility.get("coordinates") or {}).get("lat", "")),
                str((facility.get("coordinates") or {}).get("lng", "")),
            ]
        )
        return f"facility-{hashlib.sha256(identity.encode()).hexdigest()[:12]}"

    @staticmethod
    def _requirement_id(
        incident_scope_key: str,
        facility_id: str,
        category: str,
        vehicle_type: str,
    ) -> str:
        identity = "|".join([incident_scope_key, facility_id, category, vehicle_type])
        return f"tr-{hashlib.sha256(identity.encode()).hexdigest()[:16]}"

    def _determine_facility_zone(
        self,
        facility: dict[str, Any],
        zones: list[dict[str, Any]],
    ) -> int | None:
        """Determine which evacuation zone a facility falls in.

        Uses exclusive membership geometry and highest-priority boundary ownership.
        """
        zone_number, _ = self._locate_facility_zone(facility, zones)
        return zone_number

    def _locate_facility_zone(
        self,
        facility: dict[str, Any],
        zones: list[dict[str, Any]],
    ) -> tuple[int | None, str | None]:
        coordinates = facility.get("coordinates")
        if not isinstance(coordinates, dict):
            return None, "Facility coordinates are missing"
        latitude = coordinates.get("lat")
        longitude = coordinates.get("lng")
        if not isinstance(latitude, (int, float)) or not isinstance(
            longitude,
            (int, float),
        ):
            return None, "Facility coordinates must contain numeric lat/lng"
        if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
            return None, "Facility coordinates are outside WGS84 bounds"
        try:
            from shapely.geometry import Point, shape

            point = Point(longitude, latitude)
            for zone in sorted(zones, key=lambda z: z.get("zone_number", 99)):
                boundary = zone.get("membership_boundary") or zone.get("boundary")
                if not boundary:
                    continue
                zone_poly = shape(boundary)
                if zone_poly.is_empty or not zone_poly.is_valid:
                    return None, "Zone membership geometry is invalid"
                if zone_poly.covers(point):
                    return int(zone.get("zone_number", 0)), None
        except (TypeError, ValueError):
            return None, "Zone membership geometry is malformed"

        return None, None

    def _find_nearest_assembly_area(
        self,
        facility: dict[str, Any],
        assembly_areas: list[dict[str, Any]],
    ) -> dict[str, Any] | None:
        """Find the nearest assembly area to a facility using Euclidean distance."""
        if not assembly_areas:
            return None

        facility_coords = facility.get("coordinates", {})
        if not facility_coords:
            return assembly_areas[0]

        best: dict[str, Any] | None = None
        best_dist = float("inf")

        for aa in assembly_areas:
            aa_coords = aa.get("coordinates", {})
            if not aa_coords:
                continue
            dist = (facility_coords.get("lat", 0) - aa_coords.get("lat", 0)) ** 2 + (
                facility_coords.get("lng", 0) - aa_coords.get("lng", 0)
            ) ** 2
            if dist < best_dist:
                best_dist = dist
                best = aa

        return best


def _zone_from_notes(notes: str) -> int:
    """Extract zone number from notes string for sorting. Returns 99 on failure."""
    try:
        idx = notes.index("Zone: ")
        rest = notes[idx + 6 :]
        num_str = rest.split(" ")[0].rstrip("|")
        return int(num_str)
    except (ValueError, IndexError):
        return 99
