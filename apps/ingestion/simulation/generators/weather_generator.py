from datetime import UTC, datetime
from typing import Any


class WeatherGenerator:
    """Generates simulated BoM-style weather warning signals."""

    def generate_warning(
        self,
        scenario_type: str = "severe_storm",
        severity: str = "warning",
        jurisdiction: str = "nsw",
        location: list[float] | None = None,
        **_kwargs: Any,
    ) -> dict[str, Any]:
        """Generate a SignalEnvelope dict mimicking a BoM weather warning."""
        now = datetime.now(UTC).isoformat()
        loc = location or [151.21, -33.86]

        title_map = {
            "severe_storm": f"Severe Thunderstorm Warning for {jurisdiction.upper()}",
            "bushfire": f"Fire Weather Warning for {jurisdiction.upper()}",
            "flood": f"Flood Warning for {jurisdiction.upper()}",
            "cyclone": f"Tropical Cyclone Warning for {jurisdiction.upper()}",
        }
        title = title_map.get(scenario_type, f"Weather Warning for {jurisdiction.upper()}")

        category = "weather"
        if scenario_type == "flood":
            category = "hydrology"
        elif scenario_type == "bushfire":
            category = "fire"

        alert_level_map = {
            "watch": "Advice",
            "warning": "Watch and Act",
            "severe": "Emergency Warning",
            "extreme": "Emergency Warning",
            "moderate": "Advice",
            "minor": "Advice",
        }
        alert_level = alert_level_map.get(severity, "Watch and Act")

        return {
            "source": {
                "dataSourceId": "bom-warnings",
                "name": "Bureau of Meteorology",
                "kind": "authoritative",
            },
            "category": category,
            "occurredAt": now,
            "receivedAt": now,
            "location": {
                "type": "Point",
                "coordinates": loc,
                "precisionMeters": 50000,
            },
            "payload": {
                "title": title,
                "scenarioType": scenario_type,
                "severity": severity,
                "alertLevel": alert_level,
                "jurisdiction": jurisdiction,
            },
            "confidenceScore": 0.95,
            "freshnessScore": 0.90,
            "validationStatus": "validated",
            "provenance": {
                "collectionMethod": "simulation",
                "sourceUri": "sim://weather-generator",
            },
        }
