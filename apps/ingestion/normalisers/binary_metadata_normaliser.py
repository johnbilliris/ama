import logging
from datetime import UTC, datetime
from typing import Any

from apps.ingestion.normalisers.timestamps import (
    TimestampParseError,
    parse_bom_filename_timestamp,
    parse_bom_local_timestamp,
    parse_iso_timestamp,
    to_utc_iso_z,
)

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
    source_uri = str(raw_payload.get("source_uri", "")).strip()
    if not source_uri:
        raise ValueError("Binary metadata payload missing required source_uri")

    source_timezone = str(raw_payload.get("source_timezone", "Australia/Sydney"))
    occurred_timestamp = _parse_binary_timestamp(raw_payload, source_timezone)
    provider_timestamp = _parse_provider_update_timestamp(raw_payload, source_timezone, fallback=occurred_timestamp)

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
        "occurredAt": occurred_timestamp,
        "receivedAt": datetime.now(UTC).isoformat(),
        "jurisdictionId": raw_payload.get("jurisdiction_id", "national"),
        "location": location,
        "payload": {
            "productType": product_type,
            "fileFormat": raw_payload.get("file_format", "png"),
            "binaryAssetUri": source_uri,
            "coverageBbox": coverage_bbox,
            "productCode": raw_payload.get("product_code", ""),
            "publicationTimestamp": provider_timestamp,
            "resolution": raw_payload.get("resolution"),
        },
        "confidenceScore": 0.75,
        "freshnessScore": 0.9,
        "validationStatus": "validated",
        "provenance": {
            "collectionMethod": raw_payload.get("collection_method", "satellite_downlink"),
            "sourceUri": source_uri,
            "sourceTimestamp": provider_timestamp,
        },
    }


def _parse_binary_timestamp(raw_payload: dict[str, Any], source_timezone: str) -> str:
    explicit = raw_payload.get("product_timestamp")
    if explicit is not None and str(explicit).strip() != "":
        text = str(explicit).strip()
        if len(text) == 14 and text.isdigit():
            return to_utc_iso_z(
                parse_bom_local_timestamp(
                    text,
                    source_timezone=source_timezone,
                    provider="binary_metadata",
                    field="product_timestamp",
                )
            )
        return to_utc_iso_z(parse_iso_timestamp(text, provider="binary_metadata", field="product_timestamp"))

    filename = raw_payload.get("timestamp") or raw_payload.get("product_code") or raw_payload.get("source_uri")
    return to_utc_iso_z(
        parse_bom_filename_timestamp(
            filename,
            source_timezone=source_timezone,
            provider="binary_metadata",
            field="filename_timestamp",
        )
    )


def _parse_provider_update_timestamp(raw_payload: dict[str, Any], source_timezone: str, *, fallback: str) -> str:
    provider_version = raw_payload.get("provider_version")
    if provider_version is None or str(provider_version).strip() == "":
        return fallback
    token = str(provider_version).strip().split()[-1]
    if token.isdigit() and len(token) == 14:
        return to_utc_iso_z(
            parse_bom_local_timestamp(
                token,
                source_timezone="UTC",
                provider="binary_metadata",
                field="provider_version",
            )
        )
    try:
        return to_utc_iso_z(parse_iso_timestamp(token, provider="binary_metadata", field="provider_version"))
    except TimestampParseError:
        return fallback
