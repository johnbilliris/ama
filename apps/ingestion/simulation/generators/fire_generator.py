import math
import random
from datetime import UTC, datetime
from typing import Any

from apps.ingestion.simulation.region_sampling import sample_point_in_target_region

MODEL_VERSION = "fire-v1"
MODEL_CONFIG_VERSION = "2026-09-16"


class FireGenerator:
    """Generates bushfire signals using the McArthur Forest Fire Danger Index (FFDI)."""

    def generate_ffdi(
        self,
        temperature: float = 35.0,
        humidity: float = 15.0,
        wind_speed: float = 30.0,
        drought_factor: float = 8.0,
        fuel_load_t_ha: float = 12.0,
    ) -> float:
        """Calculate Forest Fire Danger Index (McArthur Mark 5).

        Simplified FFDI formula:
        FFDI = 2 * exp(-0.45 + 0.987 * ln(DF) - 0.0345 * RH + 0.0338 * T + 0.0234 * V)
        """
        if not (0.0 <= humidity <= 100.0):
            raise ValueError("humidity must be between 0 and 100")
        if wind_speed < 0:
            raise ValueError("wind_speed must be non-negative")
        if not (0.0 < fuel_load_t_ha <= 80.0):
            raise ValueError("fuel_load_t_ha must be in (0, 80]")
        if humidity <= 0:
            humidity = 1.0
        df = max(0.1, min(drought_factor, 10.0))
        ln_df = math.log(df)
        fuel_factor = 1.0 + (fuel_load_t_ha / 100.0)
        exponent = -0.45 + 0.987 * ln_df - 0.0345 * humidity + 0.0338 * temperature + 0.0234 * wind_speed
        ffdi = 2.0 * math.exp(exponent)
        return round(max(0.0, ffdi * fuel_factor), 1)

    def generate_signal(
        self,
        ffdi: float = 50.0,
        wind_bearing_degrees: float = 225.0,
        perimeter_km2: float = 3.5,
        fuel_load_t_ha: float = 12.0,
        target_region: dict[str, Any] | None = None,
        jurisdiction_id: str = "NSW",
        random_seed: int | None = None,
        location: list[float] | None = None,
        alert_level: str = "Watch and Act",
        **_kwargs: Any,
    ) -> dict[str, Any]:
        """Generate a SignalEnvelope dict for a fire danger signal."""
        now = datetime.now(UTC).isoformat()
        if not (0.0 <= wind_bearing_degrees < 360.0):
            raise ValueError("wind_bearing_degrees must be in [0, 360)")
        if not (0.01 <= perimeter_km2 <= 50000.0):
            raise ValueError("perimeter_km2 must be in [0.01, 50000]")
        if not (0.0 < fuel_load_t_ha <= 80.0):
            raise ValueError("fuel_load_t_ha must be in (0, 80]")

        rng = random.Random(random_seed)
        loc = location or sample_point_in_target_region(target_region, fallback=[150.5, -33.5], rng=rng)

        if ffdi >= 100:
            severity = "catastrophic"
        elif ffdi >= 75:
            severity = "extreme"
        elif ffdi >= 50:
            severity = "severe"
        elif ffdi >= 25:
            severity = "very_high"
        elif ffdi >= 12:
            severity = "high"
        else:
            severity = "moderate"

        wind_rad = math.radians(wind_bearing_degrees)
        spread_vector = {
            "dx": round(math.sin(wind_rad) * perimeter_km2, 4),
            "dy": round(math.cos(wind_rad) * perimeter_km2, 4),
        }

        return {
            "source": {
                "dataSourceId": "nsw-rfs-fires-near-me",
                "name": "Fire Danger Indicator",
                "kind": "authoritative",
            },
            "category": "fire",
            "occurredAt": now,
            "receivedAt": now,
            "jurisdictionId": jurisdiction_id,
            "location": {
                "type": "Point",
                "coordinates": loc,
                "precisionMeters": 1000,
            },
            "payload": {
                "ffdi": ffdi,
                "severity": severity,
                "alertLevel": alert_level,
                "windBearingDegrees": wind_bearing_degrees,
                "perimeterKm2": perimeter_km2,
                "fuelLoadTonsPerHa": fuel_load_t_ha,
                "spreadVector": spread_vector,
                "modelVersion": MODEL_VERSION,
                "modelConfigVersion": MODEL_CONFIG_VERSION,
                "calibrationProvenance": {
                    "status": "UNVERIFIED",
                    "detail": "External fire calibration constants unavailable in repository; placeholder model only.",
                },
            },
            "confidenceScore": 0.95,
            "freshnessScore": 0.90,
            "validationStatus": "validated",
            "provenance": {
                "collectionMethod": "simulation",
                "sourceUri": "sim://fire-generator",
            },
        }
