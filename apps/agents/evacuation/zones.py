"""Zone computation — Shapely-based evacuation zone boundaries and road classification.

Computes concentric zones from hazard GeoJSON polygons:
- Zone 1: Affected area (hazard polygon itself)
- Zone 2: Buffered Zone 1 (likely impact)
- Zone 3: Buffered Zone 2 (possible impact)

Road segments are classified by zone membership using polygon intersection.
Capacity reduction: Zone 1 = 0%, Zone 2 = 50%, Zone 3 = 75% of original.
"""

from __future__ import annotations

import logging
import math
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from evacuation.models import EvacuationZone
from pyproj import CRS, Transformer
from risk_assessment.hazard_radius import HazardRadiusRepository
from shapely.geometry import LineString, Polygon, shape
from shapely.ops import transform, unary_union

logger = logging.getLogger(__name__)

SEVERITY_RADIUS_LEVEL = {
    "low": 1,
    "moderate": 2,
    "high": 3,
    "critical": 4,
}

# Capacity reduction factors by zone
ZONE_CAPACITY_FACTORS = {
    1: 0.0,  # Zone 1: closed (0% capacity)
    2: 0.50,  # Zone 2: 50% capacity
    3: 0.75,  # Zone 3: 75% capacity
}


@dataclass(frozen=True)
class HazardZoneInput:
    """One validated hazard geometry and its radius lookup characteristics."""

    affected_area: dict[str, Any]
    hazard_type: str
    severity_level: str
    assessment_id: str = ""


class ZoneComputer:
    """Computes evacuation zones from hazard GeoJSON and classifies road segments."""

    def __init__(
        self,
        radius_lookup: Callable[[str, int], float] | None = None,
    ) -> None:
        radius_repository = HazardRadiusRepository()
        self._radius_lookup = radius_lookup or radius_repository.get_radius

    def compute_zones(
        self,
        hazard_geojson: dict[str, Any],
        population_data: list[dict[str, Any]] | None = None,
        hazard_type: str = "bushfire",
        severity_level: str = "high",
    ) -> list[EvacuationZone]:
        """Compute 3 concentric evacuation zones from a hazard polygon.

        Args:
            hazard_geojson: GeoJSON Polygon or MultiPolygon of the affected area.
            population_data: Optional population density data for estimation.

        Returns:
            List of 3 EvacuationZone objects (Zone 1, 2, 3).
        """
        return self.compute_zones_multi_hazard(
            [
                HazardZoneInput(
                    affected_area=hazard_geojson,
                    hazard_type=hazard_type,
                    severity_level=severity_level,
                )
            ],
            population_data,
        )

    def compute_zones_multi_hazard(
        self,
        hazards: list[HazardZoneInput | dict[str, Any]],
        population_data: list[dict[str, Any]] | None = None,
    ) -> list[EvacuationZone]:
        """Derive metric zones per hazard, then union matching severity levels."""
        if not hazards:
            return []

        normalized = [self._normalize_hazard_input(hazard) for hazard in hazards]
        hazard_zone_levels = [self._metric_zone_levels(hazard) for hazard in normalized]
        cumulative_polygons = [unary_union([levels[index] for levels in hazard_zone_levels]) for index in range(3)]
        membership_polygons = [
            cumulative_polygons[0],
            cumulative_polygons[1].difference(cumulative_polygons[0]),
            cumulative_polygons[2].difference(cumulative_polygons[1]),
        ]
        population_allocations = self._allocate_population(
            membership_polygons,
            population_data,
        )

        zones = []
        priorities = ["mandatory", "recommended", "advisory"]
        for index, (poly, membership_poly, priority) in enumerate(
            zip(cumulative_polygons, membership_polygons, priorities, strict=True),
        ):
            pop_est, vuln_est = population_allocations[index]
            zones.append(
                EvacuationZone(
                    zone_id=f"zone-{index + 1}",
                    zone_name=f"Zone {index + 1}",
                    priority=index + 1,
                    zone_number=index + 1,
                    boundary=self._polygon_to_geojson(poly),
                    membership_boundary=self._polygon_to_geojson(membership_poly),
                    population_estimate=pop_est,
                    vulnerable_population=vuln_est,
                    evacuation_priority=priority,
                    status="pending",
                )
            )

        return zones

    def merge_affected_areas(
        self,
        hazards: list[HazardZoneInput | dict[str, Any]],
    ) -> dict[str, Any]:
        """Return the validated union of raw active-hazard areas."""
        if not hazards:
            raise ValueError("At least one active hazard is required")
        geometries = [self._validate_geometry(self._normalize_hazard_input(hazard).affected_area) for hazard in hazards]
        return self._polygon_to_geojson(unary_union(geometries))

    def buffer_radius_metres(
        self,
        hazard_type: str,
        severity_level: str,
    ) -> float:
        radius_level = SEVERITY_RADIUS_LEVEL.get(severity_level)
        if radius_level is None:
            raise ValueError(f"Unsupported hazard severity: {severity_level}")
        radius = float(self._radius_lookup(hazard_type, radius_level))
        if not math.isfinite(radius) or radius <= 0:
            raise ValueError("Hazard buffer radius must be a positive number of metres")
        return radius

    def buffer_geometry_metres(
        self,
        geojson: dict[str, Any],
        distance_metres: float,
    ) -> dict[str, Any]:
        """Buffer WGS84 geometry by a metric distance in its local AEQD CRS."""
        if not math.isfinite(distance_metres) or distance_metres <= 0:
            raise ValueError("Buffer distance must be a positive number of metres")
        geometry = self._validate_geometry(geojson)
        forward, inverse = self._local_transformers(geometry)
        buffered = transform(forward, geometry).buffer(distance_metres)
        return self._polygon_to_geojson(transform(inverse, buffered))

    def _metric_zone_levels(self, hazard: HazardZoneInput) -> list[Any]:
        geometry = self._validate_geometry(hazard.affected_area)
        forward, inverse = self._local_transformers(geometry)
        metric_geometry = transform(forward, geometry)
        buffer_metres = self.buffer_radius_metres(
            hazard.hazard_type,
            hazard.severity_level,
        )
        zone_2 = metric_geometry.buffer(buffer_metres)
        zone_3 = zone_2.buffer(buffer_metres)
        return [
            geometry,
            transform(inverse, zone_2),
            transform(inverse, zone_3),
        ]

    @staticmethod
    def _local_transformers(geometry: Any) -> tuple[Callable, Callable]:
        centroid = geometry.centroid
        local_crs = CRS.from_proj4(
            f"+proj=aeqd +lat_0={centroid.y:.12f} +lon_0={centroid.x:.12f} +datum=WGS84 +units=m +no_defs"
        )
        forward = Transformer.from_crs(
            "EPSG:4326",
            local_crs,
            always_xy=True,
        ).transform
        inverse = Transformer.from_crs(
            local_crs,
            "EPSG:4326",
            always_xy=True,
        ).transform
        return forward, inverse

    @staticmethod
    def _normalize_hazard_input(
        hazard: HazardZoneInput | dict[str, Any],
    ) -> HazardZoneInput:
        if isinstance(hazard, HazardZoneInput):
            return hazard
        if "affected_area" in hazard:
            return HazardZoneInput(
                affected_area=hazard["affected_area"],
                hazard_type=str(hazard.get("hazard_type", "bushfire")),
                severity_level=str(hazard.get("severity_level", "high")),
                assessment_id=str(hazard.get("assessment_id", "")),
            )
        return HazardZoneInput(
            affected_area=hazard,
            hazard_type="bushfire",
            severity_level="high",
        )

    @staticmethod
    def _validate_geometry(geojson: dict[str, Any]) -> Any:
        try:
            geometry = shape(geojson)
        except (TypeError, ValueError) as exc:
            raise ValueError("Hazard geometry is malformed") from exc
        if geometry.geom_type not in {"Polygon", "MultiPolygon"}:
            raise ValueError("Hazard geometry must be a Polygon or MultiPolygon")
        if geometry.is_empty or not geometry.is_valid or geometry.area <= 0:
            raise ValueError("Hazard geometry must be valid and non-empty")
        return geometry

    def classify_edge_zone(
        self,
        edge_geometry: LineString,
        zone_polygons: list[tuple[int, Polygon]],
    ) -> int | None:
        """Determine which zone a road segment belongs to.

        Uses conservative partial-overlap rule: if a road intersects
        multiple zones, the highest-severity (lowest number) zone applies.

        Args:
            edge_geometry: Shapely LineString of the road segment.
            zone_polygons: List of (zone_number, polygon) sorted by severity.

        Returns:
            Zone number (1, 2, or 3) or None if outside all zones.
        """
        # Check from highest severity (Zone 1) to lowest (Zone 3)
        for zone_num, polygon in sorted(zone_polygons, key=lambda x: x[0]):
            if polygon.contains(edge_geometry):
                return zone_num
            if polygon.intersects(edge_geometry):
                # Conservative: partial overlap → highest severity zone
                return zone_num
        return None

    def get_capacity_factor(self, zone_number: int) -> float:
        """Return capacity reduction factor for a zone.

        Zone 1: 0.0 (closed), Zone 2: 0.50, Zone 3: 0.75
        Outside zones: 1.0 (full capacity)
        """
        return ZONE_CAPACITY_FACTORS.get(zone_number, 1.0)

    def apply_zone_capacity_reduction(
        self,
        edges: list[dict[str, Any]],
        zone_polygons: list[tuple[int, Any]],
    ) -> list[dict[str, Any]]:
        """Apply zone-based capacity reduction to road edges.

        Modifies edge capacity_vehicles_per_hour based on zone membership.
        Zone 1 edges are effectively closed.

        Returns edges with updated capacities and zone classifications.
        """
        results = []
        for edge in edges:
            edge_geom = edge.get("_geometry")
            if edge_geom is None:
                results.append(edge)
                continue

            zone = self.classify_edge_zone(edge_geom, zone_polygons)
            edge_copy = dict(edge)
            edge_copy["zone_membership"] = zone

            if zone is not None:
                factor = self.get_capacity_factor(zone)
                original_capacity = edge_copy.get("capacity_vehicles_per_hour", 0)
                edge_copy["original_capacity"] = original_capacity
                edge_copy["capacity_vehicles_per_hour"] = int(original_capacity * factor)

                if zone == 1:
                    edge_copy["closure_status"] = "closed"
                    edge_copy["closure_reason"] = "zone_1_closure"

            results.append(edge_copy)
        return results

    def get_zone_polygons(self, zones: list[EvacuationZone]) -> list[tuple[int, Polygon]]:
        """Convert zone boundaries to Shapely polygons for spatial operations."""
        result = []
        for zone in zones:
            poly = shape(zone.boundary)
            if not poly.is_valid:
                poly = poly.buffer(0)
            result.append((zone.zone_number, poly))
        return result

    def _allocate_population(
        self,
        membership_polygons: list[Any],
        population_data: list[dict[str, Any]] | None,
    ) -> list[tuple[int, int]]:
        """Allocate each source cohort once across exclusive memberships.

        Authoritative counts are apportioned by intersected area with deterministic
        largest-remainder rounding, preserving exact affected totals.
        """
        if not population_data:
            populations = [
                max(100, int(polygon.area * 100_000)) if not polygon.is_empty else 0 for polygon in membership_polygons
            ]
            return [(population, int(population * 0.15)) for population in populations]

        population_totals = [0] * len(membership_polygons)
        vulnerable_totals = [0] * len(membership_polygons)
        for area_data in population_data:
            boundary = area_data.get("boundary")
            if boundary is None:
                continue
            area_poly = shape(boundary)
            if not area_poly.is_valid:
                area_poly = area_poly.buffer(0)
            if area_poly.is_empty or area_poly.area <= 0:
                continue

            population = self._nonnegative_count(
                area_data.get("population_estimate", 0),
                "population_estimate",
            )
            vulnerable_value = area_data.get("vulnerable_population_estimate")
            vulnerable_population = (
                int(population * 0.15)
                if vulnerable_value is None
                else self._nonnegative_count(
                    vulnerable_value,
                    "vulnerable_population_estimate",
                )
            )
            if vulnerable_population > population:
                raise ValueError("vulnerable_population_estimate cannot exceed population_estimate")

            fractions = [
                membership.intersection(area_poly).area / area_poly.area if membership.intersects(area_poly) else 0.0
                for membership in membership_polygons
            ]
            population_by_zone = self._allocate_count(population, fractions)
            vulnerable_by_zone = self._allocate_count(
                vulnerable_population,
                fractions,
                capacities=population_by_zone,
            )
            for index in range(len(membership_polygons)):
                population_totals[index] += population_by_zone[index]
                vulnerable_totals[index] += vulnerable_by_zone[index]

        return list(zip(population_totals, vulnerable_totals, strict=True))

    @staticmethod
    def _allocate_count(
        count: int,
        fractions: list[float],
        capacities: list[int] | None = None,
    ) -> list[int]:
        covered_fraction = min(1.0, max(0.0, sum(fractions)))
        target = min(count, math.floor(count * covered_fraction + 0.5))
        if capacities is not None:
            target = min(target, sum(capacities))

        raw = [count * max(0.0, fraction) for fraction in fractions]
        allocations = [math.floor(value) for value in raw]
        if capacities is not None:
            allocations = [min(allocation, capacities[index]) for index, allocation in enumerate(allocations)]

        while sum(allocations) > target:
            candidates = [index for index, value in enumerate(allocations) if value]
            index = min(
                candidates,
                key=lambda candidate: (
                    raw[candidate] - math.floor(raw[candidate]),
                    -candidate,
                ),
            )
            allocations[index] -= 1

        ranking = sorted(
            range(len(raw)),
            key=lambda index: (
                -(raw[index] - math.floor(raw[index])),
                index,
            ),
        )
        remaining = target - sum(allocations)
        while remaining:
            progressed = False
            for index in ranking:
                if capacities is not None and allocations[index] >= capacities[index]:
                    continue
                allocations[index] += 1
                remaining -= 1
                progressed = True
                if not remaining:
                    break
            if not progressed:
                raise ValueError("Population allocation cannot satisfy zone capacities")

        return allocations

    @staticmethod
    def _nonnegative_count(value: Any, field_name: str) -> int:
        if isinstance(value, bool):
            raise ValueError(f"{field_name} must be a non-negative integer")
        parsed = int(value)
        if parsed != value or parsed < 0:
            raise ValueError(f"{field_name} must be a non-negative integer")
        return parsed

    @staticmethod
    def _polygon_to_geojson(polygon: Polygon | Any) -> dict[str, Any]:
        """Convert a Shapely polygon to GeoJSON dict."""
        if hasattr(polygon, "__geo_interface__"):
            return dict(polygon.__geo_interface__)
        return {"type": "Polygon", "coordinates": []}
