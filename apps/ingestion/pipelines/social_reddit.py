import logging
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from apps.api.app.services.ingestion.pipeline_base import IngestionPipelineBase

logger = logging.getLogger(__name__)

AUSTRALIAN_SUBREDDITS = [
    "australia", "sydney", "melbourne", "brisbane", "perth", "adelaide",
    "canberra", "hobart", "darwin", "bushfire", "AustralianEmergency",
]


class RedditPipeline(IngestionPipelineBase):
    """Reddit JSON API polling for Australian disaster-related subreddits."""

    def __init__(self, **kwargs: Any):
        super().__init__(
            pipeline_id="reddit-australia",
            data_source_ids=["reddit-australia"],
            poll_interval_seconds=120,
            trust_tier="tier_6_social_unverified",
            expected_update_seconds=120,
            **kwargs,
        )
        self._subreddits = AUSTRALIAN_SUBREDDITS

    async def poll_source(self) -> list[dict[str, Any]]:
        # Production: Reddit JSON API (append .json to subreddit URLs).
        return []

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
        occurred_at = datetime.fromtimestamp(created_utc, tz=UTC).isoformat() if created_utc else now

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
            },
        }

    def compute_canonical_key(self, raw_payload: dict[str, Any]) -> str:
        data = raw_payload.get("data", raw_payload)
        post_id = data.get("id", data.get("name", ""))
        return f"reddit:{post_id}"
