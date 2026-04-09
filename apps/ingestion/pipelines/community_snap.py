import logging
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from apps.api.app.services.ingestion.pipeline_base import IngestionPipelineBase

logger = logging.getLogger(__name__)


class SnapSendSolvePipeline(IngestionPipelineBase):
    """Snap Send Solve partner API polling pipeline."""

    def __init__(self, **kwargs: Any):
        super().__init__(
            pipeline_id="snap-send-solve",
            data_source_ids=["snap-send-solve"],
            poll_interval_seconds=300,
            trust_tier="tier_5_community_volunteer",
            expected_update_seconds=300,
            **kwargs,
        )

    async def poll_source(self) -> list[dict[str, Any]]:
        # Production: Snap Send Solve partner API.
        return []

    def normalise(self, raw_payload: dict[str, Any]) -> dict[str, Any]:
        now = datetime.now(UTC).isoformat()
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

        return {
            "source": {
                "dataSourceId": "snap-send-solve",
                "name": "Snap Send Solve",
                "kind": "community",
            },
            "category": category,
            "occurredAt": raw_payload.get("created_at", now),
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
            "freshnessScore": 0.85,
            "validationStatus": "pending",
            "provenance": {
                "collectionMethod": "api_pull",
                "sourceUri": "https://api.snapsendsolve.com/v2/reports",
            },
        }

    def compute_canonical_key(self, raw_payload: dict[str, Any]) -> str:
        report_id = raw_payload.get("id", "")
        return f"snap-send-solve:{report_id}"
