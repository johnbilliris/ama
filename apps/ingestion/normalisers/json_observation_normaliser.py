import logging
import math
from datetime import UTC, datetime
from typing import Any

from apps.ingestion.normalisers.timestamps import (
    TimestampParseError,
    parse_bom_local_timestamp,
    parse_epoch_milliseconds,
    parse_iso_timestamp,
    to_utc_iso_z,
)

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

MEASUREMENT_FIELD_MAP: dict[str, tuple[str, ...]] = {
    "temperature": ("temperature", "air_temp", "airTemperature", "temp"),
    "dew_point": ("dew_point", "dewpt", "dewPoint"),
    "relative_humidity": ("relative_humidity", "rel_hum", "humidity"),
    "wind_speed": ("wind_speed", "wind_spd_kmh", "windSpeed"),
    "wind_gust": ("wind_gust", "gust_kmh", "windGust"),
    "pressure": ("pressure", "press_msl", "qnh"),
    "rainfall": ("rainfall", "rain_trace", "rain_1h"),
    "water_level": ("water_level", "waterLevel", "level"),
    "flow_rate": ("flow_rate", "flow", "streamflow"),
    "pm25": ("pm25", "pm2_5", "pm2.5", "PM2.5"),
    "pm10": ("pm10", "PM10"),
    "ozone": ("ozone", "o3", "O3"),
}

RIVER_VALUE_TYPE_MAP: dict[str, str] = {
    "water course level": "water_level",
    "river level": "water_level",
    "gauge height": "water_level",
    "flow": "flow_rate",
    "streamflow": "flow_rate",
    "discharge": "flow_rate",
}

QUALITY_CODE_MAP: dict[str, str] = {
    "": "unknown",
    "0": "good",
    "1": "good",
    "2": "suspect",
    "3": "suspect",
    "9": "bad",
    "255": "bad",
    "good": "good",
    "ok": "good",
    "suspect": "suspect",
    "bad": "bad",
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
    validated_values: dict[str, float] = {}
    extracted_measurements = _collect_measurements(record)
    if not extracted_measurements:
        validation_issues.append("no recognized finite measurement field")

    for field, value in extracted_measurements.items():
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            validation_issues.append(f"{field}={value} is not numeric")
            continue

        if not math.isfinite(numeric):
            validation_issues.append(f"{field}={value} is not finite")
            continue

        range_bounds = SENSOR_RANGES.get(field)
        if range_bounds is not None:
            min_val, max_val = range_bounds
            if numeric < min_val or numeric > max_val:
                validation_issues.append(f"{field}={numeric} outside range [{min_val}, {max_val}]")
                continue
        validated_values[field] = numeric

    source_timezone = str(raw_payload.get("source_timezone", "Australia/Sydney"))
    observation_time = _parse_observation_timestamp(record, source_timezone)
    publication_time = _parse_publication_timestamp(record, source_timezone, fallback=observation_time)

    category = "weather"
    data_source_id = raw_payload.get("data_source_id", "bom-observations")
    source_kind = raw_payload.get("source_kind", "sensor")
    source_uri = str(raw_payload.get("source_uri", "")).strip()
    if not source_uri:
        raise ValueError("JSON observation payload missing required source_uri")

    if any(k in validated_values for k in ("water_level", "flow_rate")):
        category = "hydrology"
    elif any(k in validated_values for k in ("pm25", "pm10", "ozone")):
        category = "weather"

    threshold_crossing = _resolve_threshold_crossing(validated_values, raw_payload.get("flood_thresholds"))

    confidence = 0.75
    if threshold_crossing == "minor":
        confidence = 0.82
    elif threshold_crossing == "moderate":
        confidence = 0.90
    elif threshold_crossing == "major":
        confidence = 0.97

    if validation_issues or not validated_values:
        confidence = 0.2
        validation_status = "rejected"
    else:
        validation_status = "validated"

    location_lon, location_lat = _extract_coordinates(record, raw_payload)

    provenance: dict[str, Any] = {
        "collectionMethod": raw_payload.get("collection_method", "sensor_network"),
        "sourceUri": source_uri,
        "sourceTimestamp": publication_time,
    }
    if validation_issues:
        provenance["validationNotes"] = "; ".join(validation_issues)

    payload: dict[str, Any] = {
        "stationId": station_id,
        "stationName": station_name,
        "observationTimestamp": observation_time,
        "publicationTimestamp": publication_time,
        "observations": validated_values,
        "qualityCode": _map_quality_code(record),
        "rawRecord": record,
    }
    if threshold_crossing and "water_level" in validated_values:
        payload["thresholdCrossing"] = {
            "level": threshold_crossing,
            "value": validated_values["water_level"],
            "threshold": float(raw_payload.get("flood_thresholds", {}).get(threshold_crossing)),
        }

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
            **payload,
        },
        "confidenceScore": confidence,
        "validationStatus": validation_status,
        "provenance": provenance,
    }


def _collect_measurements(record: dict[str, Any]) -> dict[str, Any]:
    measurements: dict[str, Any] = {}
    for canonical_name, aliases in MEASUREMENT_FIELD_MAP.items():
        for alias in aliases:
            if alias in record and record[alias] not in (None, ""):
                measurements[canonical_name] = record[alias]
                break

    value = record.get("value")
    parameter_type = str(record.get("parametertype", record.get("parameter_type", ""))).strip().lower()
    if value not in (None, "") and parameter_type:
        for keyword, canonical_name in RIVER_VALUE_TYPE_MAP.items():
            if keyword in parameter_type:
                measurements[canonical_name] = value
                break
    return measurements


def _extract_coordinates(record: dict[str, Any], raw_payload: dict[str, Any]) -> tuple[float, float]:
    station_metadata = (
        raw_payload.get("station_metadata") if isinstance(raw_payload.get("station_metadata"), dict) else {}
    )
    raw_lon = record.get("lon", record.get("longitude", station_metadata.get("longitude")))
    raw_lat = record.get("lat", record.get("latitude", station_metadata.get("latitude")))
    if raw_lon in (None, "") or raw_lat in (None, ""):
        raise ValueError("station coordinates are required for JSON observations")
    return float(raw_lon), float(raw_lat)


def _resolve_threshold_crossing(measurements: dict[str, float], thresholds: Any) -> str | None:
    if "water_level" not in measurements or not isinstance(thresholds, dict):
        return None
    level_value = float(measurements["water_level"])
    ordered = ("major", "moderate", "minor")
    for level in ordered:
        threshold = thresholds.get(level)
        if threshold is None:
            continue
        try:
            threshold_value = float(threshold)
        except (TypeError, ValueError):
            continue
        if level_value >= threshold_value:
            return level
    return None


def _map_quality_code(record: dict[str, Any]) -> str:
    raw = record.get("quality", record.get("quality_code", record.get("qualityCode", "")))
    key = str(raw).strip().lower()
    return QUALITY_CODE_MAP.get(key, "unknown")


def _parse_observation_timestamp(record: dict[str, Any], source_timezone: str) -> str:
    local_stamp = record.get("local_date_time_full")
    if local_stamp is not None and str(local_stamp).strip() != "":
        return to_utc_iso_z(
            parse_bom_local_timestamp(
                local_stamp,
                source_timezone=source_timezone,
                provider="json_observation",
                field="local_date_time_full",
            )
        )

    timestamp = record.get("timestamp")
    if timestamp is None or str(timestamp).strip() == "":
        raise TimestampParseError(
            provider="json_observation",
            field="timestamp",
            value=timestamp,
            reason="missing observation timestamp",
        )

    text = str(timestamp).strip()
    if text.isdigit() and len(text) >= 12:
        return to_utc_iso_z(parse_epoch_milliseconds(text, provider="json_observation", field="timestamp"))
    return to_utc_iso_z(parse_iso_timestamp(text, provider="json_observation", field="timestamp"))


def _parse_publication_timestamp(record: dict[str, Any], source_timezone: str, *, fallback: str) -> str:
    for field in ("aifstime_utc", "sort_order", "updated", "pubDate"):
        value = record.get(field)
        if value is None or str(value).strip() == "":
            continue
        text = str(value).strip()
        if field == "aifstime_utc" and text.isdigit() and len(text) == 14:
            return to_utc_iso_z(
                parse_bom_local_timestamp(
                    text,
                    source_timezone="UTC",
                    provider="json_observation",
                    field=field,
                )
            )
        if field == "sort_order" and text.isdigit() and len(text) == 14:
            return to_utc_iso_z(
                parse_bom_local_timestamp(
                    text,
                    source_timezone=source_timezone,
                    provider="json_observation",
                    field=field,
                )
            )
        if text.isdigit() and len(text) >= 12:
            return to_utc_iso_z(parse_epoch_milliseconds(text, provider="json_observation", field=field))
        return to_utc_iso_z(parse_iso_timestamp(text, provider="json_observation", field=field))
    return fallback
