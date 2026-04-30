import random
from datetime import UTC, datetime
from typing import Any

SENSOR_RANGES: dict[str, tuple[float, float]] = {
    "temperature": (-20.0, 55.0),
    "humidity": (0.0, 100.0),
    "wind_speed": (0.0, 250.0),
    "wind_gust": (0.0, 300.0),
    "pressure": (900.0, 1100.0),
    "rainfall": (0.0, 500.0),
    "water_level": (-5.0, 30.0),
    "pm25": (0.0, 1000.0),
    "pm10": (0.0, 2000.0),
}


class SensorGenerator:
    """Generates plausible sensor observations within documented ranges."""

    def generate_observation(
        self,
        sensor_type: str = "temperature",
        base_value: float = 25.0,
        variation: float = 5.0,
        station_id: str = "sim-station-001",
        location: list[float] | None = None,
        **_kwargs: Any,
    ) -> dict[str, Any]:
        """Generate a sensor reading within plausible ranges."""
        now = datetime.now(UTC).isoformat()
        loc = location or [151.21, -33.86]

        min_val, max_val = SENSOR_RANGES.get(sensor_type, (-999, 999))
        value = base_value + random.uniform(-variation, variation)
        value = max(min_val, min(max_val, value))
        value = round(value, 2)

        category = "weather"
        if sensor_type in ("water_level",):
            category = "hydrology"

        return {
            "source": {
                "dataSourceId": "bom-aws-stations",
                "name": f"Sensor {station_id}",
                "kind": "sensor",
            },
            "category": category,
            "occurredAt": now,
            "receivedAt": now,
            "location": {
                "type": "Point",
                "coordinates": loc,
                "precisionMeters": 10,
            },
            "payload": {
                "stationId": station_id,
                "sensorType": sensor_type,
                "value": value,
                "unit": _get_unit(sensor_type),
            },
            "confidenceScore": 0.75,
            "freshnessScore": 0.90,
            "validationStatus": "validated",
            "provenance": {
                "collectionMethod": "simulation",
                "sourceUri": f"sim://sensor-generator/{station_id}",
            },
        }


def _get_unit(sensor_type: str) -> str:
    units: dict[str, str] = {
        "temperature": "°C",
        "humidity": "%",
        "wind_speed": "km/h",
        "wind_gust": "km/h",
        "pressure": "hPa",
        "rainfall": "mm",
        "water_level": "m",
        "pm25": "µg/m³",
        "pm10": "µg/m³",
    }
    return units.get(sensor_type, "")
