import logging
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from apps.api.app.services.ingestion.pipeline_base import IngestionPipelineBase

logger = logging.getLogger(__name__)


class FacebookPipeline(IngestionPipelineBase):
    """Meta Graph API polling for disaster-related community posts."""

    def __init__(self, **kwargs: Any):
        super().__init__(
            pipeline_id="facebook-community",
            data_source_ids=["facebook-community"],
            poll_interval_seconds=300,
            trust_tier="tier_6_social_unverified",
            expected_update_seconds=300,
            **kwargs,
        )

    async def poll_source(self) -> list[dict[str, Any]]:
        # Production: Meta Graph API /search or page feed endpoints.
        return []

    def normalise(self, raw_payload: dict[str, Any]) -> dict[str, Any]:
        now = datetime.now(UTC).isoformat()
        message = raw_payload.get("message", "")
        place = raw_payload.get("place", {})
        location = place.get("location", {})
        coordinates = [
            location.get("longitude", 151.21),
            location.get("latitude", -33.86),
        ]

        category = "community_report"
        msg_lower = message.lower()
        if any(k in msg_lower for k in ("bushfire", "fire")):
            category = "fire"
        elif any(k in msg_lower for k in ("flood",)):
            category = "hydrology"
        elif any(k in msg_lower for k in ("cyclone", "storm")):
            category = "weather"

        return {
            "source": {
                "dataSourceId": "facebook-community",
                "name": "Facebook Community Reports",
                "kind": "social",
            },
            "category": category,
            "occurredAt": raw_payload.get("created_time", now),
            "receivedAt": now,
            "location": {
                "type": "Point",
                "coordinates": coordinates,
                "precisionMeters": 10000,
            },
            "payload": {
                "text": message,
                "postId": raw_payload.get("id", str(uuid4().hex[:12])),
                "pageName": raw_payload.get("from", {}).get("name", ""),
            },
            "confidenceScore": 0.30,
            "freshnessScore": 0.80,
            "validationStatus": "pending",
            "provenance": {
                "collectionMethod": "api_pull",
                "sourceUri": "https://graph.facebook.com/v18.0/search",
            },
        }

    def compute_canonical_key(self, raw_payload: dict[str, Any]) -> str:
        post_id = raw_payload.get("id", "")
        return f"facebook:{post_id}"
