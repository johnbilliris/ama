import logging
from datetime import UTC, datetime
from typing import Any

import httpx

from apps.api.app.services.ingestion.pipeline_base import IngestionPipelineBase

logger = logging.getLogger(__name__)

WEBEOC_API_URL = "https://webeoc.example.gov.au/api/boards/incidents"
ICON_API_URL = "https://icon.example.gov.au/api/incidents"


class ImsWebEocPipeline(IngestionPipelineBase):
    """Polls WebEOC REST API and ICON API for incident management system field reports."""

    def __init__(self, webeoc_url: str | None = None, icon_url: str | None = None, **kwargs: Any):
        self._webeoc_url = webeoc_url or WEBEOC_API_URL
        self._icon_url = icon_url or ICON_API_URL
        super().__init__(
            pipeline_id="webeoc-ims",
            data_source_ids=["webeoc-ims", "icon-ims"],
            poll_interval_seconds=120,
            trust_tier="tier_4_field_reports",
            expected_update_seconds=120,
            **kwargs,
        )

    async def poll_source(self) -> list[dict[str, Any]]:
        payloads: list[dict[str, Any]] = []

        # Poll WebEOC
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.get(self._webeoc_url)
                resp.raise_for_status()
                data = resp.json()
            records = data if isinstance(data, list) else data.get("incidents", [])
            for record in records[:50]:
                record["_ims_source"] = "webeoc"
                payloads.append(record)
        except Exception as exc:
            logger.warning("WebEOC poll failed: %s", exc)

        # Poll ICON
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.get(self._icon_url)
                resp.raise_for_status()
                data = resp.json()
            records = data if isinstance(data, list) else data.get("incidents", [])
            for record in records[:50]:
                record["_ims_source"] = "icon"
                payloads.append(record)
        except Exception as exc:
            logger.warning("ICON poll failed: %s", exc)

        return payloads

    def normalise(self, raw_payload: dict[str, Any]) -> dict[str, Any]:
        now = datetime.now(UTC).isoformat()
        ims_source = raw_payload.get("_ims_source", "webeoc")
        data_source_id = "webeoc-ims" if ims_source == "webeoc" else "icon-ims"

        incident_type = raw_payload.get("incident_type", raw_payload.get("type", "")).lower()
        category = "community_report"
        if any(k in incident_type for k in ("fire", "bushfire")):
            category = "fire"
        elif any(k in incident_type for k in ("flood", "storm_water")):
            category = "hydrology"
        elif any(k in incident_type for k in ("storm", "cyclone", "weather")):
            category = "weather"
        elif any(k in incident_type for k in ("earthquake", "landslide")):
            category = "geohazard"

        location_data = raw_payload.get("location", {})
        lat = location_data.get("latitude", raw_payload.get("latitude", -33.86))
        lon = location_data.get("longitude", raw_payload.get("longitude", 151.21))

        return {
            "source": {
                "dataSourceId": data_source_id,
                "name": "WebEOC IMS" if ims_source == "webeoc" else "ICON IMS",
                "kind": "field_report",
            },
            "category": category,
            "occurredAt": raw_payload.get("created_at", raw_payload.get("timestamp", now)),
            "receivedAt": now,
            "location": {
                "type": "Point",
                "coordinates": [float(lon), float(lat)],
                "precisionMeters": 100,
            },
            "payload": {
                "incidentId": raw_payload.get("incident_id", ""),
                "title": raw_payload.get("title", raw_payload.get("description", "")),
                "status": raw_payload.get("status", ""),
                "priority": raw_payload.get("priority", ""),
                "reporter": raw_payload.get("reporter", ""),
                "imsSource": ims_source,
            },
            "confidenceScore": 0.65,
            "freshnessScore": 0.85,
            "validationStatus": "validated",
            "provenance": {
                "collectionMethod": "api_pull",
                "sourceUri": self._webeoc_url if ims_source == "webeoc" else self._icon_url,
            },
        }

    def compute_canonical_key(self, raw_payload: dict[str, Any]) -> str:
        ims_source = raw_payload.get("_ims_source", "webeoc")
        incident_id = raw_payload.get("incident_id", raw_payload.get("id", ""))
        updated = raw_payload.get("updated_at", raw_payload.get("timestamp", ""))
        return f"{ims_source}:{incident_id}:{updated}"
