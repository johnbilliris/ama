import logging
from typing import Any

from app.services.state_store import INCIDENTS

logger = logging.getLogger(__name__)


class IncidentAssociationService:
    """Associates signals with active incidents at ingestion time (FR-019a).

    Checks signal jurisdiction and geographic location against active incident
    boundaries. Creates one signal record per matching incident (multi-incident
    fan-out) with shared correlation ID.
    """

    async def associate(self, envelope: dict[str, Any]) -> dict[str, Any]:
        signal_jurisdiction = envelope.get("jurisdictionId")
        signal_location = envelope.get("location", {})
        matching_incidents = self._find_matching_incidents(signal_jurisdiction, signal_location)

        if not matching_incidents:
            envelope["incidentId"] = None
            return envelope

        envelope["incidentId"] = matching_incidents[0]
        return envelope

    async def associate_multi(self, envelope: dict[str, Any]) -> list[dict[str, Any]]:
        """Returns multiple envelopes if signal matches multiple incidents."""
        signal_jurisdiction = envelope.get("jurisdictionId")
        signal_location = envelope.get("location", {})
        matching_incidents = self._find_matching_incidents(signal_jurisdiction, signal_location)

        if not matching_incidents:
            envelope["incidentId"] = None
            return [envelope]

        results = []
        for incident_id in matching_incidents:
            copy = {**envelope, "incidentId": incident_id}
            results.append(copy)
        return results

    def _find_matching_incidents(
        self,
        jurisdiction_id: str | None,
        location: dict[str, Any],
    ) -> list[str]:
        matching = []
        for incident_id, incident in INCIDENTS.items():
            if incident.status not in ("active", "monitoring"):
                continue
            if jurisdiction_id and jurisdiction_id in incident.affected_jurisdiction_ids:
                matching.append(incident_id)
            elif self._location_overlaps_incident(location, incident):
                matching.append(incident_id)
        return matching

    def _location_overlaps_incident(
        self,
        signal_location: dict[str, Any],
        incident: Any,
    ) -> bool:
        try:
            if signal_location.get("type") == "Point":
                coords = signal_location.get("coordinates", [])
                if len(coords) >= 2:
                    for jid in incident.affected_jurisdiction_ids:
                        if self._jurisdiction_contains_point(jid, coords[0], coords[1]):
                            return True
        except Exception:
            pass
        return False

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
