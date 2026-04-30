import logging
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger(__name__)


def normalise_binary_metadata(raw_payload: dict[str, Any]) -> dict[str, Any]:
    """Create a metadata-only SignalEnvelope for radar/satellite imagery (FR-009a).

    By default, no binary is downloaded — only metadata is stored. Full binary
    download is triggered by the pipeline when an active incident overlaps
    the imagery coverage area.
    """
    data_source_id = raw_payload.get("data_source_id", "unknown")
    source_name = raw_payload.get("source_name", "Satellite/Radar")
    product_type = raw_payload.get("product_type", "radar")
    source_uri = raw_payload.get("source_uri", "")
    timestamp = raw_payload.get("timestamp", datetime.now(UTC).isoformat())

    coverage_bbox = raw_payload.get("coverage_bbox", [112.0, -44.0, 154.0, -10.0])
    coverage_polygon = raw_payload.get("coverage_polygon")

    if coverage_polygon:
        location = {
            "type": "Polygon",
            "coordinates": coverage_polygon,
            "precisionMeters": 1000,
        }
    elif coverage_bbox and len(coverage_bbox) == 4:
        min_lon, min_lat, max_lon, max_lat = coverage_bbox
        location = {
            "type": "Polygon",
            "coordinates": [
                [
                    [min_lon, min_lat],
                    [max_lon, min_lat],
                    [max_lon, max_lat],
                    [min_lon, max_lat],
                    [min_lon, min_lat],
                ]
            ],
            "precisionMeters": 5000,
        }
    else:
        location = {"type": "Point", "coordinates": [133.0, -27.0], "precisionMeters": 500000}

    category = "fire" if product_type in ("hotspot", "thermal") else "weather"

    return {
        "source": {
            "dataSourceId": data_source_id,
            "name": source_name,
            "kind": raw_payload.get("source_kind", "sensor"),
        },
        "category": category,
        "occurredAt": timestamp,
        "receivedAt": datetime.now(UTC).isoformat(),
        "jurisdictionId": raw_payload.get("jurisdiction_id", "national"),
        "location": location,
        "payload": {
            "productType": product_type,
            "fileFormat": raw_payload.get("file_format", "png"),
            "binaryAssetUri": source_uri,
            "coverageBbox": coverage_bbox,
            "productCode": raw_payload.get("product_code", ""),
            "resolution": raw_payload.get("resolution"),
        },
        "confidenceScore": 0.75,
        "freshnessScore": 0.9,
        "validationStatus": "validated",
        "provenance": {
            "collectionMethod": raw_payload.get("collection_method", "satellite_downlink"),
            "sourceUri": source_uri,
            "sourceTimestamp": timestamp,
        },
    }
