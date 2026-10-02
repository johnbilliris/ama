import logging
from datetime import UTC, datetime
from typing import Any

from apps.ingestion.normalisers.timestamps import (
    TimestampParseError,
    parse_epoch_milliseconds,
    parse_iso_timestamp,
    parse_local_timestamp,
    parse_rfc822_timestamp,
    to_utc_iso_z,
)

logger = logging.getLogger(__name__)

ALERT_LEVEL_CONFIDENCE: dict[str, float] = {
    "Emergency Warning": 0.95,
    "Watch and Act": 0.85,
    "Advice": 0.70,
    "Not Applicable": 0.60,
}

CATEGORY_KEYWORDS: dict[str, str] = {
    "bush fire": "fire",
    "grass fire": "fire",
    "fire": "fire",
    "flood": "hydrology",
    "storm": "weather",
    "cyclone": "weather",
    "earthquake": "geohazard",
    "tsunami": "geohazard",
}

STATE_PROPERTY_MAPS: dict[str, dict[str, str]] = {
    "nsw-rfs": {"title": "title", "category": "category", "status": "status", "alert_level": "alertLevel"},
    "vic-cfa": {"title": "name", "category": "type", "status": "status", "alert_level": "alertLevel"},
    "qld-qfes": {"title": "title", "category": "type", "status": "status", "alert_level": "alertLevel"},
    "default": {"title": "title", "category": "category", "status": "status", "alert_level": "alertLevel"},
}


def normalise_geojson(raw_payload: dict[str, Any]) -> dict[str, Any]:
    """Parse a GeoJSON Feature into a SignalEnvelope dict."""
    if raw_payload.get("type") == "FeatureCollection":
        features = raw_payload.get("features", [])
        if features:
            return normalise_geojson_feature(features[0], raw_payload)
        raise ValueError("Empty FeatureCollection")

    if raw_payload.get("type") == "Feature":
        return normalise_geojson_feature(raw_payload, {})

    if "features" in raw_payload:
        return normalise_geojson({"type": "FeatureCollection", **raw_payload})

    return normalise_geojson_feature(raw_payload, {})


def normalise_geojson_collection(raw_payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Parse a GeoJSON FeatureCollection into multiple SignalEnvelope dicts."""
    features = raw_payload.get("features", [])
    return [normalise_geojson_feature(f, raw_payload) for f in features]


def normalise_geojson_feature(
    feature: dict[str, Any],
    collection_context: dict[str, Any],
) -> dict[str, Any]:
    """Normalise a single GeoJSON Feature to a SignalEnvelope."""
    props = feature.get("properties", {})
    geometry = feature.get("geometry", {})

    data_source_id = collection_context.get("data_source_id", feature.get("data_source_id", "unknown"))
    source_name = collection_context.get("source_name", feature.get("source_name", "Unknown"))
    source_kind = collection_context.get("source_kind", "authoritative")
    jurisdiction_id = collection_context.get("jurisdiction_id", feature.get("jurisdiction_id"))
    state_key = collection_context.get("state_key", "default")
    source_timezone = str(collection_context.get("source_timezone", "Australia/Sydney"))

    prop_map = STATE_PROPERTY_MAPS.get(state_key, STATE_PROPERTY_MAPS["default"])
    title = props.get(prop_map["title"], props.get("title", ""))
    raw_category = props.get(prop_map["category"], props.get("category", "")).lower()
    status = props.get(prop_map["status"], props.get("status", ""))
    alert_level = props.get(prop_map["alert_level"], props.get("alertLevel", ""))

    category = "fire"
    for keyword, cat in CATEGORY_KEYWORDS.items():
        if keyword in raw_category:
            category = cat
            break

    confidence = ALERT_LEVEL_CONFIDENCE.get(alert_level, 0.70)

    location = _geometry_to_location(geometry)

    source_uri = str(collection_context.get("source_uri", "")).strip()
    if not source_uri:
        raise ValueError("GeoJSON payload missing required source_uri")

    occurred_at, publication_or_update = _parse_geojson_timestamps(props, source_timezone=source_timezone)

    return {
        "source": {
            "dataSourceId": data_source_id,
            "name": source_name,
            "kind": source_kind,
        },
        "category": category,
        "occurredAt": occurred_at,
        "receivedAt": datetime.now(UTC).isoformat(),
        "jurisdictionId": jurisdiction_id,
        "location": location,
        "payload": {
            "title": title,
            "status": status,
            "alertLevel": alert_level,
            "rawCategory": raw_category,
            "featureId": feature.get("id", props.get("id", "")),
            "publicationTimestamp": publication_or_update,
            "updateTimestamp": publication_or_update,
            "properties": props,
        },
        "confidenceScore": confidence,
        "validationStatus": "validated",
        "provenance": {
            "collectionMethod": "api_pull",
            "sourceUri": source_uri,
            "sourceTimestamp": publication_or_update,
        },
    }


def _parse_geojson_timestamps(properties: dict[str, Any], *, source_timezone: str) -> tuple[str, str]:
    publication_or_update = _parse_one(
        [
            ("updated", properties.get("updated")),
            ("pubDate", properties.get("pubDate")),
            ("created", properties.get("created")),
            ("load_dt", properties.get("load_dt")),
            ("process_dt", properties.get("process_dt")),
        ],
        provider="geojson",
        source_timezone=source_timezone,
    )

    occurred = _parse_one(
        [
            ("time", properties.get("time")),
            ("occurredAt", properties.get("occurredAt")),
            ("eventTime", properties.get("eventTime")),
            ("datetime", properties.get("datetime")),
            ("start_dt", properties.get("start_dt")),
            ("created", properties.get("created")),
            ("pubDate", properties.get("pubDate")),
        ],
        provider="geojson",
        fallback_iso=publication_or_update,
        source_timezone=source_timezone,
    )
    return occurred, publication_or_update


def _parse_one(
    candidates: list[tuple[str, Any]],
    *,
    provider: str,
    fallback_iso: str | None = None,
    source_timezone: str,
) -> str:
    for field, value in candidates:
        if value is None or str(value).strip() == "":
            continue
        text = str(value).strip()
        try:
            if field == "pubDate":
                try:
                    return to_utc_iso_z(parse_rfc822_timestamp(text, provider=provider, field=field))
                except TimestampParseError:
                    try:
                        return to_utc_iso_z(parse_iso_timestamp(text, provider=provider, field=field))
                    except TimestampParseError:
                        return to_utc_iso_z(
                            parse_local_timestamp(
                                text,
                                formats=("%d/%m/%Y %I:%M:%S %p",),
                                source_timezone=source_timezone,
                                provider=provider,
                                field=field,
                            )
                        )
            if field == "time" and text.isdigit():
                return to_utc_iso_z(parse_epoch_milliseconds(text, provider=provider, field=field))
            if text.isdigit() and len(text) >= 12:
                return to_utc_iso_z(parse_epoch_milliseconds(text, provider=provider, field=field))
            return to_utc_iso_z(parse_iso_timestamp(text, provider=provider, field=field))
        except TimestampParseError:
            continue
    if fallback_iso is not None:
        return fallback_iso
    raise TimestampParseError(
        provider=provider, field="timestamp", value=None, reason="missing supported timestamp field"
    )


def _supported_geometries(geometry: dict[str, Any]) -> list[dict[str, Any]]:
    if geometry.get("type") != "GeometryCollection":
        return [geometry]

    supported: list[dict[str, Any]] = []
    for member in geometry.get("geometries", []):
        if isinstance(member, dict):
            supported.extend(_supported_geometries(member))
    return supported


def _geometry_to_location(geometry: dict[str, Any]) -> dict[str, Any]:
    if geometry.get("type") == "GeometryCollection":
        candidates = _supported_geometries(geometry)
        for preferred_type in ("Point", "Polygon", "MultiPolygon"):
            for candidate in candidates:
                if candidate.get("type") == preferred_type and candidate.get("coordinates"):
                    return _geometry_to_location(candidate)
        raise ValueError("Unsupported or empty GeoJSON geometry: GeometryCollection")
    geo_type = geometry.get("type", "Point")
    coordinates = geometry.get("coordinates", [])

    if geo_type == "Point" and coordinates:
        return {"type": "Point", "coordinates": coordinates, "precisionMeters": 100}
    if geo_type == "Polygon" and coordinates:
        return {"type": "Polygon", "coordinates": coordinates, "precisionMeters": 50}
    if geo_type == "MultiPolygon" and coordinates:
        return {"type": "MultiPolygon", "coordinates": coordinates, "precisionMeters": 100}
    raise ValueError(f"Unsupported or empty GeoJSON geometry: {geo_type}")
