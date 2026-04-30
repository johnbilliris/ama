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
from typing import Any

from evacuation.models import EvacuationZone
from shapely.geometry import LineString, Polygon, shape
from shapely.ops import unary_union

logger = logging.getLogger(__name__)

# Default buffer distances in degrees (~km at tropical latitudes)
# 1 degree ≈ 111km, so 0.01 ≈ 1.1km
DEFAULT_ZONE_2_BUFFER = 0.05  # ~5.5km buffer from Zone 1
DEFAULT_ZONE_3_BUFFER = 0.05  # ~5.5km additional buffer from Zone 2

# Capacity reduction factors by zone
ZONE_CAPACITY_FACTORS = {
    1: 0.0,  # Zone 1: closed (0% capacity)
    2: 0.50,  # Zone 2: 50% capacity
    3: 0.75,  # Zone 3: 75% capacity
}


class ZoneComputer:
    """Computes evacuation zones from hazard GeoJSON and classifies road segments."""

    def __init__(
        self,
        zone_2_buffer: float = DEFAULT_ZONE_2_BUFFER,
        zone_3_buffer: float = DEFAULT_ZONE_3_BUFFER,
    ) -> None:
        self._zone_2_buffer = zone_2_buffer
        self._zone_3_buffer = zone_3_buffer

    def compute_zones(
        self,
        hazard_geojson: dict[str, Any],
        population_data: list[dict[str, Any]] | None = None,
    ) -> list[EvacuationZone]:
        """Compute 3 concentric evacuation zones from a hazard polygon.

        Args:
            hazard_geojson: GeoJSON Polygon or MultiPolygon of the affected area.
            population_data: Optional population density data for estimation.

        Returns:
            List of 3 EvacuationZone objects (Zone 1, 2, 3).
        """
        hazard_poly = shape(hazard_geojson)
        if not hazard_poly.is_valid:
            hazard_poly = hazard_poly.buffer(0)  # Fix invalid geometry

        # Zone 1: the hazard area itself
        zone_1_poly = hazard_poly

        # Zone 2: buffer around Zone 1
        zone_2_poly = zone_1_poly.buffer(self._zone_2_buffer)

        # Zone 3: buffer around Zone 2
        zone_3_poly = zone_2_poly.buffer(self._zone_3_buffer)

        zones = []
        for zone_num, poly, priority in [
            (1, zone_1_poly, "mandatory"),
            (2, zone_2_poly, "recommended"),
            (3, zone_3_poly, "advisory"),
        ]:
            pop_est = self._estimate_population(poly, population_data)
            vuln_est = int(pop_est * 0.15)  # ~15% vulnerable population estimate

            zones.append(
                EvacuationZone(
                    zone_number=zone_num,
                    boundary=self._polygon_to_geojson(poly),
                    population_estimate=pop_est,
                    vulnerable_population=vuln_est,
                    evacuation_priority=priority,
                    status="pending",
                )
            )

        return zones

    def compute_zones_multi_hazard(
        self,
        hazard_geojsons: list[dict[str, Any]],
        population_data: list[dict[str, Any]] | None = None,
    ) -> list[EvacuationZone]:
        """Compute zones from multiple hazard polygons via geometric union.

        Uses shapely.ops.unary_union() to merge overlapping hazard areas
        before computing concentric zones.
        """
        if not hazard_geojsons:
            return []

        polys = []
        for geojson in hazard_geojsons:
            poly = shape(geojson)
            if not poly.is_valid:
                poly = poly.buffer(0)
            polys.append(poly)

        merged = unary_union(polys)
        merged_geojson = self._polygon_to_geojson(merged)
        return self.compute_zones(merged_geojson, population_data)

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

    def _estimate_population(
        self,
        polygon: Polygon,
        population_data: list[dict[str, Any]] | None,
    ) -> int:
        """Estimate population within a polygon from density data.

        If no population data available, uses a rough estimate based on area.
        """
        if not population_data:
            # Rough fallback: ~100 people per sq degree unit area
            area = polygon.area
            return max(100, int(area * 100_000))

        total = 0
        for area_data in population_data:
            boundary = area_data.get("boundary")
            if boundary is None:
                continue
            area_poly = shape(boundary)
            if not area_poly.is_valid:
                area_poly = area_poly.buffer(0)

            if polygon.intersects(area_poly):
                intersection = polygon.intersection(area_poly)
                if area_poly.area > 0:
                    fraction = intersection.area / area_poly.area
                else:
                    fraction = 0.0
                pop = area_data.get("population_estimate", 0)
                total += int(pop * fraction)

        return max(total, 0)

    @staticmethod
    def _polygon_to_geojson(polygon: Polygon | Any) -> dict[str, Any]:
        """Convert a Shapely polygon to GeoJSON dict."""
        if hasattr(polygon, "__geo_interface__"):
            return dict(polygon.__geo_interface__)
        return {"type": "Polygon", "coordinates": []}
