import logging
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger(__name__)

SENSOR_RANGES: dict[str, tuple[float, float]] = {
    "temperature": (-20.0, 55.0),
    "air_temp": (-20.0, 55.0),
    "dew_point": (-40.0, 40.0),
    "dewpt": (-40.0, 40.0),
    "relative_humidity": (0.0, 100.0),
    "rel_hum": (0.0, 100.0),
    "wind_speed": (0.0, 250.0),
    "wind_spd_kmh": (0.0, 250.0),
    "wind_gust": (0.0, 300.0),
    "gust_kmh": (0.0, 300.0),
    "pressure": (900.0, 1100.0),
    "press_msl": (900.0, 1100.0),
    "rainfall": (0.0, 500.0),
    "rain_trace": (0.0, 500.0),
    "water_level": (-5.0, 30.0),
    "flow_rate": (0.0, 1000000.0),
    "pm25": (0.0, 1000.0),
    "pm10": (0.0, 2000.0),
    "ozone": (0.0, 500.0),
}


def normalise_json_observation(raw_payload: dict[str, Any]) -> dict[str, Any]:
    """Parse BoM JSON station observations or sensor data into a SignalEnvelope dict."""
    observations = raw_payload.get("observations", raw_payload)
    if isinstance(observations, dict):
        data = observations.get("data", [observations])
    elif isinstance(observations, list):
        data = observations
    else:
        data = [raw_payload]

    record = data[0] if data else raw_payload
    station_id = str(record.get("wmo", record.get("station_id", record.get("gauge_id", ""))))
    station_name = record.get("name", record.get("station_name", record.get("gauge_name", "")))

    validation_issues: list[str] = []
    validated_values: dict[str, Any] = {}
    all_valid = True

    for field, (min_val, max_val) in SENSOR_RANGES.items():
        value = record.get(field)
        if value is not None:
            try:
                numeric = float(value)
                if numeric < min_val or numeric > max_val:
                    validation_issues.append(
                        f"{field}={numeric} outside range [{min_val}, {max_val}]"
                    )
                    all_valid = False
                else:
                    validated_values[field] = numeric
            except (ValueError, TypeError):
                validation_issues.append(f"{field}={value} is not numeric")
                all_valid = False

    observation_time = record.get("local_date_time_full", record.get("timestamp", ""))
    if not observation_time:
        observation_time = datetime.now(UTC).isoformat()

    category = "weather"
    data_source_id = raw_payload.get("data_source_id", "bom-observations")
    source_kind = raw_payload.get("source_kind", "sensor")

    if any(k in record for k in ("water_level", "flow_rate", "gauge_id")):
        category = "hydrology"
    elif any(k in record for k in ("pm25", "pm10", "ozone", "aqi")):
        category = "weather"

    confidence = 0.75 if all_valid else 0.2
    validation_status = "validated" if all_valid else "rejected"

    location_lat = record.get("lat", record.get("latitude", -33.86))
    location_lon = record.get("lon", record.get("longitude", 151.21))

    provenance: dict[str, Any] = {
        "collectionMethod": raw_payload.get("collection_method", "sensor_network"),
        "sourceUri": raw_payload.get("source_uri", ""),
        "sourceTimestamp": observation_time,
    }
    if validation_issues:
        provenance["validationNotes"] = "; ".join(validation_issues)

    return {
        "source": {
            "dataSourceId": data_source_id,
            "name": station_name or f"Station {station_id}",
            "kind": source_kind,
        },
        "category": category,
        "occurredAt": observation_time,
        "receivedAt": datetime.now(UTC).isoformat(),
        "jurisdictionId": raw_payload.get("jurisdiction_id"),
        "location": {
            "type": "Point",
            "coordinates": [float(location_lon), float(location_lat)],
            "precisionMeters": 10,
        },
        "payload": {
            "stationId": station_id,
            "stationName": station_name,
            "observations": validated_values,
            "rawRecord": record,
        },
        "confidenceScore": confidence,
        "freshnessScore": 0.85,
        "validationStatus": validation_status,
        "provenance": provenance,
    }
