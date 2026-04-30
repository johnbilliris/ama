import math
from datetime import UTC, datetime
from typing import Any


class FireGenerator:
    """Generates bushfire signals using the McArthur Forest Fire Danger Index (FFDI)."""

    def generate_ffdi(
        self,
        temperature: float = 35.0,
        humidity: float = 15.0,
        wind_speed: float = 30.0,
        drought_factor: float = 8.0,
    ) -> float:
        """Calculate Forest Fire Danger Index (McArthur Mark 5).

        Simplified FFDI formula:
        FFDI = 2 * exp(-0.45 + 0.987 * ln(DF) - 0.0345 * RH + 0.0338 * T + 0.0234 * V)
        """
        if humidity <= 0:
            humidity = 1.0
        df = max(0.1, min(drought_factor, 10.0))
        ln_df = math.log(df)
        exponent = -0.45 + 0.987 * ln_df - 0.0345 * humidity + 0.0338 * temperature + 0.0234 * wind_speed
        ffdi = 2.0 * math.exp(exponent)
        return round(max(0.0, ffdi), 1)

    def generate_signal(
        self,
        ffdi: float = 50.0,
        location: list[float] | None = None,
        alert_level: str = "Watch and Act",
        **_kwargs: Any,
    ) -> dict[str, Any]:
        """Generate a SignalEnvelope dict for a fire danger signal."""
        now = datetime.now(UTC).isoformat()
        loc = location or [150.5, -33.5]

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

        return {
            "source": {
                "dataSourceId": "nsw-rfs-fires-near-me",
                "name": "Fire Danger Indicator",
                "kind": "authoritative",
            },
            "category": "fire",
            "occurredAt": now,
            "receivedAt": now,
            "location": {
                "type": "Point",
                "coordinates": loc,
                "precisionMeters": 1000,
            },
            "payload": {
                "ffdi": ffdi,
                "severity": severity,
                "alertLevel": alert_level,
            },
            "confidenceScore": 0.95,
            "freshnessScore": 0.90,
            "validationStatus": "validated",
            "provenance": {
                "collectionMethod": "simulation",
                "sourceUri": "sim://fire-generator",
            },
        }
