import math
from datetime import UTC, datetime
from typing import Any


class CycloneGenerator:
    """Generates tropical cyclone track and signal data."""

    def generate_track(
        self,
        start_lat: float = -15.0,
        start_lon: float = 155.0,
        bearing: float = 225.0,
        speed_kmh: float = 20.0,
        duration_hours: float = 72.0,
    ) -> list[tuple[float, float, int]]:
        """Generate (lat, lon, category) tuples along a cyclone track."""
        points: list[tuple[float, float, int]] = []
        steps = max(int(duration_hours), 10)
        bearing_rad = math.radians(bearing)

        lat = start_lat
        lon = start_lon

        for i in range(steps):
            fraction = i / steps
            # Category intensifies then weakens
            if fraction < 0.4:
                category = min(5, 1 + int(fraction * 10))
            elif fraction < 0.7:
                category = max(1, 5 - int((fraction - 0.4) * 10))
            else:
                category = max(1, 3 - int((fraction - 0.7) * 10))

            points.append((round(lat, 4), round(lon, 4), category))

            km_per_step = speed_kmh
            delta_lat = km_per_step / 111.0 * math.cos(bearing_rad)
            delta_lon = km_per_step / (111.0 * math.cos(math.radians(lat))) * math.sin(bearing_rad)
            lat += delta_lat
            lon += delta_lon

        return points

    def generate_signal(
        self,
        position: tuple[float, float] | None = None,
        category: int = 2,
        wind_speed: float = 130.0,
        **_kwargs: Any,
    ) -> dict[str, Any]:
        """Generate a SignalEnvelope dict for a cyclone position."""
        now = datetime.now(UTC).isoformat()
        pos = position or (-15.0, 155.0)

        severity = "watch"
        if category >= 4:
            severity = "extreme"
        elif category >= 3:
            severity = "severe"
        elif category >= 2:
            severity = "warning"

        return {
            "source": {
                "dataSourceId": "bom-warnings",
                "name": "Tropical Cyclone Track",
                "kind": "authoritative",
            },
            "category": "weather",
            "occurredAt": now,
            "receivedAt": now,
            "location": {
                "type": "Point",
                "coordinates": [pos[1], pos[0]],
                "precisionMeters": 50000,
            },
            "payload": {
                "cycloneCategory": category,
                "windSpeedKmh": wind_speed,
                "severity": severity,
                "trackLat": pos[0],
                "trackLon": pos[1],
            },
            "confidenceScore": 0.95,
            "freshnessScore": 0.90,
            "validationStatus": "validated",
            "provenance": {
                "collectionMethod": "simulation",
                "sourceUri": "sim://cyclone-generator",
            },
        }
