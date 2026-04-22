"""GeoJSON hazard polygon generation (FR-004, FR-005, R2).

Generates GeoJSON Polygon/MultiPolygon from signal locations and severity,
using severity-indexed radius lookup. Merges overlapping polygons.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from risk_assessment.hazard_radius import HazardRadiusRepository
from shapely.geometry import Point, mapping
from shapely.ops import unary_union

logger = logging.getLogger(__name__)

# Approximate degree conversion at equator: 1 degree ≈ 111,320 metres
_METRES_PER_DEGREE = 111_320


class HazardMapGenerator:
    """Generates GeoJSON hazard map polygons from point signals and radius lookup."""

    def __init__(self, radius_repo: HazardRadiusRepository | None = None) -> None:
        self._radius_repo = radius_repo or HazardRadiusRepository()

    def generate(
        self,
        signals: list[dict[str, Any]],
        hazard_type: str,
        severity_level: int | str,
    ) -> dict[str, Any]:
        """Generate a GeoJSON hazard map from signal locations.

        Args:
            signals: List of signal dicts with 'longitude' and 'latitude' keys.
            hazard_type: Type of hazard (e.g., "bushfire", "flood").
            severity_level: Severity level 1-5.

        Returns:
            GeoJSON-compatible dict with Polygon or MultiPolygon geometry.
        """
        radius_m = self._radius_repo.get_radius(hazard_type, severity_level)
        radius_deg = radius_m / _METRES_PER_DEGREE

        polygons = []
        for signal in signals:
            lon = signal.get("longitude", signal.get("lon", 0.0))
            lat = signal.get("latitude", signal.get("lat", 0.0))
            point = Point(lon, lat)
            # Buffer to create circular polygon (approximate at equator)
            poly = point.buffer(radius_deg)
            polygons.append(poly)

        if not polygons:
            return self._empty_geojson(hazard_type, severity_level)

        # Merge overlapping polygons (R2)
        merged = unary_union(polygons)
        geojson_geometry = mapping(merged)

        return {
            "type": "Feature",
            "geometry": geojson_geometry,
            "properties": {
                "hazard_type": hazard_type,
                "severity_level": int(severity_level),
                "radius_metres": radius_m,
                "signal_count": len(signals),
                "generated_at": datetime.now(UTC).isoformat(),
            },
        }

    @staticmethod
    def _empty_geojson(hazard_type: str, severity_level: int | str) -> dict[str, Any]:
        """Return an empty GeoJSON feature for zero-signal case."""
        return {
            "type": "Feature",
            "geometry": {"type": "Polygon", "coordinates": []},
            "properties": {
                "hazard_type": hazard_type,
                "severity_level": int(severity_level),
                "signal_count": 0,
                "generated_at": datetime.now(UTC).isoformat(),
            },
        }
