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

DISASTER_KEYWORDS = ["bushfire", "flood", "cyclone", "evacuation", "emergency", "SES"]


class TwitterPipeline(IngestionPipelineBase):
    """Simulates X (Twitter) API v2 filtered stream for disaster-related posts."""

    def __init__(self, endpoint_url: str | None = None, transport: Any = None, **kwargs: Any):
        super().__init__(
            pipeline_id="twitter-disaster",
            data_source_ids=["twitter-disaster"],
            poll_interval_seconds=60,
            trust_tier="tier_6_social_unverified",
            expected_update_seconds=60,
            **kwargs,
        )
        self._keywords = DISASTER_KEYWORDS
        self._endpoint_url = endpoint_url or "https://api.twitter.com/2/tweets/search/stream"
        self._transport = transport

    async def poll_source(self) -> list[dict[str, Any]]:
        bearer_token = os.environ.get("TWITTER_BEARER_TOKEN", "").strip()
        if not bearer_token:
            raise SourceUnavailable(
                "twitter-disaster",
                "twitter bearer token is not configured",
                blocked=True,
            )
        if self._transport is None:
            raise SourceUnavailable(
                "twitter-disaster",
                "twitter transport is not configured",
                blocked=True,
            )
        records = await self._transport.poll(
            endpoint_url=self._endpoint_url,
            bearer_token=bearer_token,
            keywords=list(self._keywords),
        )
        if isinstance(records, tuple) and len(records) == 3:
            payloads, raw_bytes, content_type = records
            artifact = RawArtifact(
                raw_bytes=raw_bytes, content_type=content_type, source_uri=self._endpoint_url, file_format="json"
            )
            return [attach_raw_artifact(dict(item), artifact) for item in payloads]
        return records

    def normalise(self, raw_payload: dict[str, Any]) -> dict[str, Any]:
        now = datetime.now(UTC).isoformat()
        created_at_raw = raw_payload.get("created_at")
        occurred_at = to_utc_iso_z(parse_iso_timestamp(created_at_raw, provider="twitter", field="created_at"))
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
            "occurredAt": occurred_at,
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
                "sourceTimestamp": occurred_at,
            },
        }

    def compute_canonical_key(self, raw_payload: dict[str, Any]) -> str:
        tweet_id = raw_payload.get("id", "")
        return f"twitter:{tweet_id}"
