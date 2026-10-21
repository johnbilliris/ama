import logging
import os
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from app.services.ingestion.exceptions import SourceUnavailable
from app.services.ingestion.raw_artifact import RawArtifact, attach_raw_artifact

from apps.api.app.services.ingestion.pipeline_base import IngestionPipelineBase
from apps.ingestion.normalisers.timestamps import parse_iso_timestamp, to_utc_iso_z

logger = logging.getLogger(__name__)


class SnapSendSolvePipeline(IngestionPipelineBase):
    """Snap Send Solve partner API polling pipeline."""

    def __init__(self, endpoint_url: str | None = None, transport: Any = None, **kwargs: Any):
        super().__init__(
            pipeline_id="snap-send-solve",
            data_source_ids=["snap-send-solve"],
            poll_interval_seconds=300,
            trust_tier="tier_5_community_volunteer",
            expected_update_seconds=300,
            **kwargs,
        )
        self._endpoint_url = endpoint_url or "https://api.snapsendsolve.com/v1/reports"
        self._transport = transport

    async def poll_source(self) -> list[dict[str, Any]]:
        api_key = os.environ.get("SNAP_SEND_SOLVE_API_KEY", "").strip()
        if not api_key:
            raise SourceUnavailable("snap-send-solve", "snap send solve api key is not configured", blocked=True)
        if self._transport is None:
            raise SourceUnavailable("snap-send-solve", "snap transport is not configured", blocked=True)
        records = await self._transport.poll(endpoint_url=self._endpoint_url, api_key=api_key)
        if isinstance(records, tuple) and len(records) == 3:
            payloads, raw_bytes, content_type = records
            artifact = RawArtifact(
                raw_bytes=raw_bytes, content_type=content_type, source_uri=self._endpoint_url, file_format="json"
            )
            return [attach_raw_artifact(dict(item), artifact) for item in payloads]
        return records

    def normalise(self, raw_payload: dict[str, Any]) -> dict[str, Any]:
        now = datetime.now(UTC).isoformat()
        created_raw = raw_payload.get("created_at")
        occurred_at = to_utc_iso_z(parse_iso_timestamp(created_raw, provider="snap_send_solve", field="created_at"))
        location_data = raw_payload.get("location", {})
        coordinates = [
            location_data.get("longitude", 151.21),
            location_data.get("latitude", -33.86),
        ]

        category = "community_report"
        report_type = raw_payload.get("type", "").lower()
        if any(k in report_type for k in ("fire", "smoke")):
            category = "fire"
        elif any(k in report_type for k in ("flood", "water")):
            category = "hydrology"
        elif any(k in report_type for k in ("storm", "wind")):
            category = "weather"
        elif any(k in report_type for k in ("road closure", "road_closed", "road", "traffic")):
            category = "infrastructure"

        return {
            "source": {
                "dataSourceId": "snap-send-solve",
                "name": "Snap Send Solve",
                "kind": "community",
            },
            "category": category,
            "occurredAt": occurred_at,
            "receivedAt": now,
            "location": {
                "type": "Point",
                "coordinates": coordinates,
                "precisionMeters": 50,
            },
            "payload": {
                "reportId": raw_payload.get("id", str(uuid4().hex[:12])),
                "description": raw_payload.get("description", ""),
                "reportType": raw_payload.get("type", ""),
                "imageUrl": raw_payload.get("image_url", ""),
            },
            "confidenceScore": 0.45,
            "validationStatus": "pending",
            "provenance": {
                "collectionMethod": "api_pull",
                "sourceUri": "https://api.snapsendsolve.com/v2/reports",
                "sourceTimestamp": occurred_at,
            },
        }

    def compute_canonical_key(self, raw_payload: dict[str, Any]) -> str:
        report_id = raw_payload.get("id", "")
        return f"snap-send-solve:{report_id}"
