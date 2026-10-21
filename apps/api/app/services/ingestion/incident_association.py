import logging
from collections.abc import Iterable
from typing import Any

from app.services.state_store import INCIDENTS

logger = logging.getLogger(__name__)


class IncidentAssociationService:
    """Associates signals with active incidents at ingestion time (FR-019a).

    Checks signal jurisdiction and geographic location against active incident
    boundaries. Creates one signal record per matching incident (multi-incident
    fan-out) with shared correlation ID.
    """

    def __init__(self, incident_reader: Any | None = None) -> None:
        self._incident_reader = incident_reader

    async def associate(self, envelope: dict[str, Any], *, scope: str = "live") -> dict[str, Any]:
        signal_jurisdiction = envelope.get("jurisdictionId")
        signal_location = envelope.get("location", {})
        matching_incidents = self._find_matching_incidents(signal_jurisdiction, signal_location, scope=scope)

        if not matching_incidents:
            envelope["incidentId"] = None
            return envelope

        incident_id, reason = matching_incidents[0]
        envelope["incidentId"] = incident_id
        self._append_validation_note(envelope, reason)
        return envelope

    async def associate_multi(self, envelope: dict[str, Any], *, scope: str = "live") -> list[dict[str, Any]]:
        """Returns multiple envelopes if signal matches multiple incidents."""
        signal_jurisdiction = envelope.get("jurisdictionId")
        signal_location = envelope.get("location", {})
        matching_incidents = self._find_matching_incidents(signal_jurisdiction, signal_location, scope=scope)

        if not matching_incidents:
            envelope["incidentId"] = None
            return [envelope]

        results = []
        for incident_id, reason in matching_incidents:
            copy = {**envelope, "incidentId": incident_id}
            self._append_validation_note(copy, reason)
            results.append(copy)
        return results

    def _find_matching_incidents(
        self,
        jurisdiction_id: str | None,
        location: dict[str, Any],
        *,
        scope: str,
    ) -> list[tuple[str, str]]:
        matching: list[tuple[str, str]] = []
        for incident_id, incident in self._iter_incidents(scope):
            if incident.status not in ("active", "monitoring"):
                continue
            if not self._jurisdiction_allows_signal(jurisdiction_id, incident):
                continue

            incident_location = getattr(incident, "location", None)
            if isinstance(incident_location, dict):
                if self._location_overlaps_incident(location, incident_location):
                    matching.append((incident_id, "association_precision=footprint"))
                continue

            # Fallback is allowed only when the incident has no footprint.
            matching.append((incident_id, "association_precision=jurisdiction_only_no_footprint"))
        return matching

    def _location_overlaps_incident(
        self,
        signal_location: dict[str, Any],
        incident_location: dict[str, Any],
    ) -> bool:
        try:
            if not isinstance(signal_location, dict) or not isinstance(incident_location, dict):
                return False

            if str(incident_location.get("type", "")).lower() == "national":
                return True

            signal_points = self._extract_points(signal_location)
            incident_polygons = self._extract_polygons(incident_location)
            if signal_points and incident_polygons:
                for point in signal_points:
                    if any(self._point_in_polygon(point, polygon) for polygon in incident_polygons):
                        return True

            incident_points = self._extract_points(incident_location)
            signal_polygons = self._extract_polygons(signal_location)
            if incident_points and signal_polygons:
                for point in incident_points:
                    if any(self._point_in_polygon(point, polygon) for polygon in signal_polygons):
                        return True

            if signal_polygons and incident_polygons:
                if self._bbox_overlaps(signal_polygons, incident_polygons):
                    return True
        except Exception:
            pass
        return False

    def _iter_incidents(self, scope: str) -> Iterable[tuple[str, Any]]:
        if self._incident_reader is not None:
            provided = self._incident_reader(scope)
            if isinstance(provided, dict):
                return provided.items()
            return provided
        return INCIDENTS.bucket_for(scope).items()

    def _jurisdiction_allows_signal(self, jurisdiction_id: str | None, incident: Any) -> bool:
        affected = {str(j).lower() for j in getattr(incident, "affected_jurisdiction_ids", [])}
        if "national" in affected:
            return True
        if not jurisdiction_id:
            return False
        return str(jurisdiction_id).lower() in affected

    def _extract_points(self, geometry: dict[str, Any]) -> list[tuple[float, float]]:
        kind = geometry.get("type")
        coords = geometry.get("coordinates")
        if kind == "Point" and isinstance(coords, list) and len(coords) >= 2:
            return [(float(coords[0]), float(coords[1]))]
        points: list[tuple[float, float]] = []
        if kind == "Polygon" and isinstance(coords, list):
            for ring in coords:
                if isinstance(ring, list):
                    for point in ring:
                        if isinstance(point, list) and len(point) >= 2:
                            points.append((float(point[0]), float(point[1])))
        if kind == "MultiPolygon" and isinstance(coords, list):
            for polygon in coords:
                if isinstance(polygon, list):
                    for ring in polygon:
                        if isinstance(ring, list):
                            for point in ring:
                                if isinstance(point, list) and len(point) >= 2:
                                    points.append((float(point[0]), float(point[1])))
        return points

    def _extract_polygons(self, geometry: dict[str, Any]) -> list[list[tuple[float, float]]]:
        kind = geometry.get("type")
        coords = geometry.get("coordinates")
        polygons: list[list[tuple[float, float]]] = []
        if kind == "Polygon" and isinstance(coords, list):
            for ring in coords:
                if not isinstance(ring, list):
                    continue
                points = [
                    (float(point[0]), float(point[1])) for point in ring if isinstance(point, list) and len(point) >= 2
                ]
                if points:
                    polygons.append(points)
        if kind == "MultiPolygon" and isinstance(coords, list):
            for polygon in coords:
                if not isinstance(polygon, list):
                    continue
                for ring in polygon:
                    if not isinstance(ring, list):
                        continue
                    points = [
                        (float(point[0]), float(point[1]))
                        for point in ring
                        if isinstance(point, list) and len(point) >= 2
                    ]
                    if points:
                        polygons.append(points)
        return polygons

    def _point_in_polygon(self, point: tuple[float, float], polygon: list[tuple[float, float]]) -> bool:
        x, y = point
        inside = False
        if len(polygon) < 3:
            return False
        j = len(polygon) - 1
        for i in range(len(polygon)):
            xi, yi = polygon[i]
            xj, yj = polygon[j]
            intersects = ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / ((yj - yi) or 1e-12) + xi)
            if intersects:
                inside = not inside
            j = i
        return inside

    def _bbox_overlaps(
        self,
        polygons_a: list[list[tuple[float, float]]],
        polygons_b: list[list[tuple[float, float]]],
    ) -> bool:
        def _bbox(polygons: list[list[tuple[float, float]]]) -> tuple[float, float, float, float] | None:
            points = [point for polygon in polygons for point in polygon]
            if not points:
                return None
            lons = [p[0] for p in points]
            lats = [p[1] for p in points]
            return min(lons), min(lats), max(lons), max(lats)

        bbox_a = _bbox(polygons_a)
        bbox_b = _bbox(polygons_b)
        if bbox_a is None or bbox_b is None:
            return False
        a_min_lon, a_min_lat, a_max_lon, a_max_lat = bbox_a
        b_min_lon, b_min_lat, b_max_lon, b_max_lat = bbox_b
        return not (a_max_lon < b_min_lon or b_max_lon < a_min_lon or a_max_lat < b_min_lat or b_max_lat < a_min_lat)

    def _append_validation_note(self, envelope: dict[str, Any], note: str) -> None:
        provenance = envelope.get("provenance")
        if not isinstance(provenance, dict):
            provenance = {}
            envelope["provenance"] = provenance
        existing = str(provenance.get("validationNotes", "")).strip()
        provenance["validationNotes"] = f"{existing}; {note}" if existing else note

    def _jurisdiction_contains_point(self, jurisdiction_id: str, lon: float, lat: float) -> bool:
        AU_BOUNDS: dict[str, tuple[float, float, float, float]] = {
            "nsw": (140.99, -37.51, 153.64, -28.16),
            "vic": (140.96, -39.16, 149.98, -33.98),
            "qld": (137.99, -29.18, 153.55, -10.68),
            "sa": (129.00, -38.06, 141.00, -26.00),
            "wa": (112.92, -35.13, 129.00, -13.69),
            "tas": (143.83, -43.64, 148.48, -39.57),
            "nt": (129.00, -26.00, 138.00, -10.97),
            "act": (148.76, -35.92, 149.40, -35.12),
            "national": (112.0, -44.0, 154.0, -10.0),
        }
        bounds = AU_BOUNDS.get(jurisdiction_id)
        if bounds:
            min_lon, min_lat, max_lon, max_lat = bounds
            return min_lon <= lon <= max_lon and min_lat <= lat <= max_lat
        return False
