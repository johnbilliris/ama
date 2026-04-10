import logging
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from apps.api.app.services.ingestion.pipeline_base import IngestionPipelineBase

logger = logging.getLogger(__name__)

DISASTER_KEYWORDS = ["bushfire", "flood", "cyclone", "evacuation", "emergency", "SES"]


class TwitterPipeline(IngestionPipelineBase):
    """Simulates X (Twitter) API v2 filtered stream for disaster-related posts."""

    def __init__(self, **kwargs: Any):
        super().__init__(
            pipeline_id="twitter-disaster",
            data_source_ids=["twitter-disaster"],
            poll_interval_seconds=60,
            trust_tier="tier_6_social_unverified",
            expected_update_seconds=60,
            **kwargs,
        )
        self._keywords = DISASTER_KEYWORDS

    async def poll_source(self) -> list[dict[str, Any]]:
        # In production, this would connect to X API v2 filtered stream.
        # Here we return an empty list; simulation generators provide test data.
        return []

    def normalise(self, raw_payload: dict[str, Any]) -> dict[str, Any]:
        now = datetime.now(UTC).isoformat()
        text = raw_payload.get("text", "")
        user = raw_payload.get("user", {})
        geo = raw_payload.get("geo", {})
        coordinates = geo.get("coordinates", [151.21, -33.86])

        category = "community_report"
        text_lower = text.lower()
        if any(k in text_lower for k in ("bushfire", "fire")):
            category = "fire"
        elif any(k in text_lower for k in ("flood", "ses")):
            category = "hydrology"
        elif any(k in text_lower for k in ("cyclone", "storm")):
            category = "weather"

        return {
            "source": {
                "dataSourceId": "twitter-disaster",
                "name": "X (Twitter) Disaster Stream",
                "kind": "social",
            },
            "category": category,
            "occurredAt": raw_payload.get("created_at", now),
            "receivedAt": now,
            "location": {
                "type": "Point",
                "coordinates": coordinates,
                "precisionMeters": 5000,
            },
            "payload": {
                "text": text,
                "userId": user.get("id", ""),
                "username": user.get("username", ""),
                "tweetId": raw_payload.get("id", str(uuid4().hex[:12])),
                "matchedKeywords": [k for k in self._keywords if k.lower() in text_lower],
            },
            "confidenceScore": 0.30,
            "freshnessScore": 0.85,
            "validationStatus": "pending",
            "provenance": {
                "collectionMethod": "streaming_api",
                "sourceUri": "https://api.twitter.com/2/tweets/search/stream",
            },
        }

    def compute_canonical_key(self, raw_payload: dict[str, Any]) -> str:
        tweet_id = raw_payload.get("id", "")
        return f"twitter:{tweet_id}"
