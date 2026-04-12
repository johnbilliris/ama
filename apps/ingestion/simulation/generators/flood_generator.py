import math
from datetime import UTC, datetime
from typing import Any


class FloodGenerator:
    """Generates realistic flood hydrograph signals."""

    def generate_hydrograph(
        self,
        duration_hours: float = 48.0,
        peak_level: float = 9.5,
        minor_threshold: float = 3.0,
        moderate_threshold: float = 5.0,
        major_threshold: float = 7.0,
    ) -> list[tuple[float, float]]:
        """Generate (time_offset_hours, water_level) tuples following a realistic flood curve."""
        points: list[tuple[float, float]] = []
        steps = max(int(duration_hours * 2), 10)
        rise_fraction = 0.35
        peak_fraction = 0.15

        rise_steps = int(steps * rise_fraction)
        peak_steps = int(steps * peak_fraction)
        recession_steps = steps - rise_steps - peak_steps

        base_level = minor_threshold * 0.3

        # Rising limb
        for i in range(rise_steps):
            t = (i / rise_steps)
            level = base_level + (peak_level - base_level) * (1 - math.cos(t * math.pi / 2))
            time_offset = (i / steps) * duration_hours
            points.append((round(time_offset, 2), round(level, 2)))

        # Peak plateau
        for i in range(peak_steps):
            variation = math.sin(i / max(peak_steps - 1, 1) * math.pi) * 0.3
            level = peak_level - abs(variation)
            time_offset = ((rise_steps + i) / steps) * duration_hours
            points.append((round(time_offset, 2), round(level, 2)))

        # Recession limb
        for i in range(recession_steps):
            t = i / max(recession_steps - 1, 1)
            level = peak_level * math.exp(-2.5 * t) + base_level * (1 - math.exp(-2.5 * t))
            time_offset = ((rise_steps + peak_steps + i) / steps) * duration_hours
            points.append((round(time_offset, 2), round(level, 2)))

        return points

    def generate_signal(
        self,
        time_offset: float = 0.0,
        water_level: float = 5.0,
        gauge_id: str = "gauge-001",
        location: list[float] | None = None,
        **_kwargs: Any,
    ) -> dict[str, Any]:
        """Generate a SignalEnvelope dict for a river gauge reading."""
        now = datetime.now(UTC).isoformat()
        loc = location or [151.21, -33.86]

        severity = "below_minor"
        if water_level >= 7.0:
            severity = "major"
        elif water_level >= 5.0:
            severity = "moderate"
        elif water_level >= 3.0:
            severity = "minor"

        return {
            "source": {
                "dataSourceId": "bom-river-gauges",
                "name": f"River Gauge {gauge_id}",
                "kind": "sensor",
            },
            "category": "hydrology",
            "occurredAt": now,
            "receivedAt": now,
            "location": {
                "type": "Point",
                "coordinates": loc,
                "precisionMeters": 10,
            },
            "payload": {
                "gaugeId": gauge_id,
                "waterLevel": water_level,
                "timeOffset": time_offset,
                "severity": severity,
            },
            "confidenceScore": 0.75,
            "freshnessScore": 0.90,
            "validationStatus": "validated",
            "provenance": {
                "collectionMethod": "simulation",
                "sourceUri": f"sim://flood-generator/{gauge_id}",
            },
        }
