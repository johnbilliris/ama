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

import logging
from typing import Any

from evacuation.config import EvacuationConfig
from evacuation.models import TransportRequirement, VulnerabilityCategory

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
        """Generate transport requirements for facilities within evacuation zones.

        Args:
            zones: List of zone dicts with zone_number and boundary.
            facilities: List of facility dicts from population data.  Each should
                contain keys: ``vulnerability_category``, ``capacity``, ``name``,
                ``coordinates`` (``{lat, lng}``), and optionally
                ``special_considerations``.
            assembly_areas: List of assembly area dicts with ``assembly_area_id``,
                ``name``, and ``coordinates``.

        Returns:
            List of TransportRequirement records sorted by priority.
        """
        if not facilities:
            logger.info("No facility data available — skipping transport coordination")
            return []

        requirements: list[TransportRequirement] = []

        for facility in facilities:
            # Determine which zone the facility is in
            zone_number = self._determine_facility_zone(facility, zones)
            if zone_number is None:
                continue  # Facility outside evacuation zones

            # Find nearest assembly area
            nearest_aa = self._find_nearest_assembly_area(facility, assembly_areas)
            if nearest_aa is None:
                continue

            # Get vulnerability category
            vuln_category = facility.get("vulnerability_category", "")
            if vuln_category not in VEHICLE_TYPE_MAP:
                continue

            # Compute vehicle requirement
            capacity = facility.get("capacity", 0)
            if capacity <= 0:
                continue

            vehicle_type = VEHICLE_TYPE_MAP[vuln_category]
            priority = PRIORITY_MAP[vuln_category]
            vehicle_capacity = VEHICLE_CAPACITY.get(vehicle_type, 50)
            estimated_vehicles = max(1, -(-capacity // vehicle_capacity))  # Ceiling division

            # Gather special considerations
            special = list(SPECIAL_CONSIDERATIONS.get(vuln_category, []))
            facility_special = facility.get("special_considerations", [])
            for s in facility_special:
                if s not in special:
                    special.append(s)

            # Build notes field with all contextual info
            facility_name = facility.get("name", "Unknown facility")
            dest_name = nearest_aa.get("name", nearest_aa.get("assembly_area_id", ""))
            coords = facility.get("coordinates", {})
            coord_str = (
                f"({coords.get('lat', 0):.4f}, {coords.get('lng', 0):.4f})"
                if coords
                else ""
            )
            special_str = ", ".join(special) if special else "none"

            notes = (
                f"Priority: {priority} | "
                f"Pickup: {facility_name} {coord_str} | "
                f"Destination: {dest_name} | "
                f"Individuals: {capacity} | "
                f"Zone: {zone_number} | "
                f"Considerations: {special_str}"
            )

            requirement = TransportRequirement(
                category=VulnerabilityCategory(vuln_category),
                vehicle_type=vehicle_type,
                quantity_required=estimated_vehicles,
                estimated_trips=max(1, estimated_vehicles),
                notes=notes,
            )
            requirements.append(requirement)

        # Sort by priority: critical > immediate > high
        requirements.sort(
            key=lambda r: (
                _PRIORITY_ORDER.get(
                    PRIORITY_MAP.get(r.category.value, "high"), 3
                ),
                _zone_from_notes(r.notes),
            )
        )

        return requirements

    def _determine_facility_zone(
        self,
        facility: dict[str, Any],
        zones: list[dict[str, Any]],
    ) -> int | None:
        """Determine which evacuation zone a facility falls in.

        Uses simple coordinate-based containment check via Shapely when available.
        Falls back to nearest-zone assignment if geometric check fails.
        """
        # Try geometric containment via Shapely
        try:
            from shapely.geometry import Point, shape

            coords = facility.get("coordinates", {})
            if coords:
                point = Point(coords.get("lng", 0), coords.get("lat", 0))
                for zone in sorted(zones, key=lambda z: z.get("zone_number", 99)):
                    boundary = zone.get("boundary")
                    if boundary:
                        zone_poly = shape(boundary)
                        if zone_poly.contains(point) or zone_poly.intersects(
                            point.buffer(0.001)
                        ):
                            return zone.get("zone_number")
        except Exception:
            pass

        # Fallback: if zones are defined, assign to outermost zone
        if zones:
            return max(z.get("zone_number", 3) for z in zones)

        return None

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
            dist = (
                (facility_coords.get("lat", 0) - aa_coords.get("lat", 0)) ** 2
                + (facility_coords.get("lng", 0) - aa_coords.get("lng", 0)) ** 2
            )
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
