import logging
from datetime import UTC, datetime
from typing import Any

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

    occurred_at = props.get("pubDate", props.get("updated", props.get("created", "")))
    if not occurred_at:
        occurred_at = datetime.now(UTC).isoformat()

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
            "properties": props,
        },
        "confidenceScore": confidence,
        "freshnessScore": 0.85,
        "validationStatus": "validated",
        "provenance": {
            "collectionMethod": "api_pull",
            "sourceUri": collection_context.get("source_uri", ""),
            "sourceTimestamp": occurred_at,
        },
    }


def _geometry_to_location(geometry: dict[str, Any]) -> dict[str, Any]:
    geo_type = geometry.get("type", "Point")
    coordinates = geometry.get("coordinates", [])

    if geo_type == "Point" and coordinates:
        return {"type": "Point", "coordinates": coordinates, "precisionMeters": 100}
    elif geo_type == "Polygon" and coordinates:
        return {"type": "Polygon", "coordinates": coordinates, "precisionMeters": 50}
    elif geo_type == "MultiPolygon" and coordinates:
        flat = coordinates[0] if coordinates else [[]]
        return {"type": "Polygon", "coordinates": flat, "precisionMeters": 100}
    return {"type": "Point", "coordinates": [0, 0], "precisionMeters": 100000}
