import logging
import os
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from app.services.ingestion.exceptions import SourceUnavailable
from app.services.ingestion.raw_artifact import RawArtifact, attach_raw_artifact

from apps.api.app.services.ingestion.pipeline_base import IngestionPipelineBase
from apps.ingestion.normalisers.timestamps import parse_epoch_milliseconds, to_utc_iso_z

logger = logging.getLogger(__name__)

AUSTRALIAN_SUBREDDITS = [
    "australia",
    "sydney",
    "melbourne",
    "brisbane",
    "perth",
    "adelaide",
    "canberra",
    "hobart",
    "darwin",
    "bushfire",
    "AustralianEmergency",
]


class RedditPipeline(IngestionPipelineBase):
    """Reddit JSON API polling for Australian disaster-related subreddits."""

    def __init__(self, endpoint_url: str | None = None, transport: Any = None, **kwargs: Any):
        super().__init__(
            pipeline_id="reddit-australia",
            data_source_ids=["reddit-australia"],
            poll_interval_seconds=120,
            trust_tier="tier_6_social_unverified",
            expected_update_seconds=120,
            **kwargs,
        )
        self._subreddits = AUSTRALIAN_SUBREDDITS
        self._endpoint_url = endpoint_url or "https://www.reddit.com"
        self._transport = transport
        self._active_poll_interval_seconds = 120
        self._idle_poll_interval_seconds = 900

    async def poll_source(self) -> list[dict[str, Any]]:
        client_id = os.environ.get("REDDIT_CLIENT_ID", "").strip()
        if not client_id:
            raise SourceUnavailable("reddit-australia", "reddit client id is not configured", blocked=True)
        if self._transport is None:
            raise SourceUnavailable("reddit-australia", "reddit transport is not configured", blocked=True)

        posts = await self._transport.poll(
            endpoint_url=self._endpoint_url,
            subreddits=list(self._subreddits),
            requests_per_minute=60,
        )
        if isinstance(posts, tuple) and len(posts) == 3:
            payloads, raw_bytes, content_type = posts
            self.poll_interval_seconds = (
                self._active_poll_interval_seconds if payloads else self._idle_poll_interval_seconds
            )
            artifact = RawArtifact(
                raw_bytes=raw_bytes, content_type=content_type, source_uri=self._endpoint_url, file_format="json"
            )
            return [attach_raw_artifact(dict(item), artifact) for item in payloads]
        self.poll_interval_seconds = self._active_poll_interval_seconds if posts else self._idle_poll_interval_seconds
        return posts

    def normalise(self, raw_payload: dict[str, Any]) -> dict[str, Any]:
        now = datetime.now(UTC).isoformat()
        data = raw_payload.get("data", raw_payload)
        title = data.get("title", "")
        selftext = data.get("selftext", "")
        subreddit = data.get("subreddit", "")

        category = "community_report"
        combined = f"{title} {selftext}".lower()
        if any(k in combined for k in ("bushfire", "fire")):
            category = "fire"
        elif any(k in combined for k in ("flood",)):
            category = "hydrology"
        elif any(k in combined for k in ("cyclone", "storm")):
            category = "weather"

        created_utc = data.get("created_utc")
        if created_utc is None:
            raise ValueError("Reddit payload missing required created_utc")
        occurred_at = to_utc_iso_z(
            parse_epoch_milliseconds(
                int(float(created_utc) * 1000),
                provider="reddit",
                field="created_utc",
            )
        )

        return {
            "source": {
                "dataSourceId": "reddit-australia",
                "name": f"Reddit r/{subreddit}",
                "kind": "social",
            },
            "category": category,
            "occurredAt": occurred_at,
            "receivedAt": now,
            "location": {
                "type": "Point",
                "coordinates": [133.77, -25.27],
                "precisionMeters": 500000,
            },
            "payload": {
                "text": f"{title}\n{selftext}".strip(),
                "postId": data.get("id", str(uuid4().hex[:12])),
                "subreddit": subreddit,
                "author": data.get("author", ""),
                "score": data.get("score", 0),
            },
            "confidenceScore": 0.30,
            "freshnessScore": 0.75,
            "validationStatus": "pending",
            "provenance": {
                "collectionMethod": "api_pull",
                "sourceUri": f"https://www.reddit.com/r/{subreddit}/new.json",
                "sourceTimestamp": occurred_at,
            },
        }

    def compute_canonical_key(self, raw_payload: dict[str, Any]) -> str:
        data = raw_payload.get("data", raw_payload)
        post_id = data.get("id", data.get("name", ""))
        return f"reddit:{post_id}"
