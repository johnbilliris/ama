from __future__ import annotations

import random
from typing import Any


def _point_in_ring(lon: float, lat: float, ring: list[list[float]]) -> bool:
    inside = False
    j = len(ring) - 1
    for i in range(len(ring)):
        xi, yi = ring[i]
        xj, yj = ring[j]
        intersects = ((yi > lat) != (yj > lat)) and (lon < (xj - xi) * (lat - yi) / ((yj - yi) or 1e-12) + xi)
        if intersects:
            inside = not inside
        j = i
    return inside


def point_in_polygon(lon: float, lat: float, polygon: list[list[list[float]]]) -> bool:
    if not polygon or not polygon[0]:
        return False
    if not _point_in_ring(lon, lat, polygon[0]):
        return False
    for hole in polygon[1:]:
        if hole and _point_in_ring(lon, lat, hole):
            return False
    return True


def sample_point_in_target_region(
    target_region: dict[str, Any] | None,
    *,
    fallback: list[float],
    rng: random.Random,
) -> list[float]:
    if not isinstance(target_region, dict):
        return fallback
    if target_region.get("type") != "Polygon":
        raise ValueError("target_region must be a GeoJSON Polygon")
    coords = target_region.get("coordinates")
    if not isinstance(coords, list) or not coords or not isinstance(coords[0], list):
        raise ValueError("target_region Polygon coordinates are required")

    ring = coords[0]
    lons = [float(point[0]) for point in ring]
    lats = [float(point[1]) for point in ring]
    min_lon, max_lon = min(lons), max(lons)
    min_lat, max_lat = min(lats), max(lats)

    for _ in range(64):
        lon = rng.uniform(min_lon, max_lon)
        lat = rng.uniform(min_lat, max_lat)
        if point_in_polygon(lon, lat, coords):
            return [round(lon, 6), round(lat, 6)]
    raise ValueError("could not sample a coordinate inside target_region")
