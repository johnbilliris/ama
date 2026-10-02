import math
import random
from datetime import UTC, datetime
from typing import Any

from apps.ingestion.simulation.region_sampling import sample_point_in_target_region

MODEL_VERSION = "cyclone-v1"
MODEL_CONFIG_VERSION = "2026-09-16"


class CycloneGenerator:
    """Generates tropical cyclone track and signal data."""

    def generate_track(
        self,
        start_lat: float = -15.0,
        start_lon: float = 155.0,
        bearing: float = 225.0,
        speed_kmh: float = 20.0,
        duration_hours: float = 72.0,
        min_pressure_hpa: float = 910.0,
        max_pressure_hpa: float = 1005.0,
        intensity_factor: float = 1.0,
    ) -> list[tuple[float, float, int]]:
        """Generate (lat, lon, category) tuples along a cyclone track."""
        if duration_hours <= 0:
            raise ValueError("duration_hours must be > 0")
        if not (850.0 <= min_pressure_hpa < max_pressure_hpa <= 1035.0):
            raise ValueError("pressure bounds must satisfy 850 <= min < max <= 1035")
        if intensity_factor <= 0:
            raise ValueError("intensity_factor must be > 0")
        points: list[tuple[float, float, int]] = []
        steps = max(int(duration_hours), 10)
        bearing_rad = math.radians(bearing)

        lat = start_lat
        lon = start_lon

        for i in range(steps):
            fraction = i / steps
            # Category intensifies then weakens
            pressure = max_pressure_hpa - (max_pressure_hpa - min_pressure_hpa) * math.sin(fraction * math.pi)
            category = self._category_from_pressure(pressure, intensity_factor)

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
        central_pressure_hpa: float = 980.0,
        radius_max_wind_km: float = 40.0,
        pressure_wind_slope: float = 2.0,
        intensity_factor: float = 1.0,
        target_region: dict[str, Any] | None = None,
        jurisdiction_id: str = "QLD",
        random_seed: int | None = None,
        **_kwargs: Any,
    ) -> dict[str, Any]:
        """Generate a SignalEnvelope dict for a cyclone position."""
        now = datetime.now(UTC).isoformat()
        if not (850.0 <= central_pressure_hpa <= 1035.0):
            raise ValueError("central_pressure_hpa must be between 850 and 1035")
        if not (5.0 <= radius_max_wind_km <= 250.0):
            raise ValueError("radius_max_wind_km must be between 5 and 250")
        if pressure_wind_slope <= 0:
            raise ValueError("pressure_wind_slope must be > 0")
        if intensity_factor <= 0:
            raise ValueError("intensity_factor must be > 0")

        rng = random.Random(random_seed)
        sampled = sample_point_in_target_region(target_region, fallback=[155.0, -15.0], rng=rng)
        pos = position or (sampled[1], sampled[0])
        derived_wind = max(0.0, (1035.0 - central_pressure_hpa) * pressure_wind_slope * intensity_factor)
        effective_wind = round(max(wind_speed, derived_wind), 1)
        if category <= 0:
            category = self._category_from_pressure(central_pressure_hpa, intensity_factor)

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
            "jurisdictionId": jurisdiction_id,
            "location": {
                "type": "Point",
                "coordinates": [pos[1], pos[0]],
                "precisionMeters": 50000,
            },
            "payload": {
                "cycloneCategory": category,
                "windSpeedKmh": effective_wind,
                "severity": severity,
                "trackLat": pos[0],
                "trackLon": pos[1],
                "centralPressureHpa": central_pressure_hpa,
                "radiusMaxWindKm": radius_max_wind_km,
                "pressureWindSlope": pressure_wind_slope,
                "intensityFactor": intensity_factor,
                "modelVersion": MODEL_VERSION,
                "modelConfigVersion": MODEL_CONFIG_VERSION,
                "calibrationProvenance": {
                    "status": "UNVERIFIED",
                    "detail": "External pressure/intensity calibration constants unavailable in repository; placeholder model only.",  # noqa: E501
                },
            },
            "confidenceScore": 0.95,
            "freshnessScore": 0.90,
            "validationStatus": "validated",
            "provenance": {
                "collectionMethod": "simulation",
                "sourceUri": "sim://cyclone-generator",
            },
        }

    def _category_from_pressure(self, pressure_hpa: float, intensity_factor: float) -> int:
        normalized = (1035.0 - pressure_hpa) * intensity_factor
        if normalized >= 130:
            return 5
        if normalized >= 105:
            return 4
        if normalized >= 85:
            return 3
        if normalized >= 65:
            return 2
        return 1
