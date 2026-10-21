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


class FacebookPipeline(IngestionPipelineBase):
    """Meta Graph API polling for disaster-related community posts."""

    def __init__(self, endpoint_url: str | None = None, transport: Any = None, **kwargs: Any):
        super().__init__(
            pipeline_id="facebook-community",
            data_source_ids=["facebook-community"],
            poll_interval_seconds=300,
            trust_tier="tier_6_social_unverified",
            expected_update_seconds=300,
            **kwargs,
        )
        self._endpoint_url = endpoint_url or "https://graph.facebook.com/v19.0/"
        self._transport = transport
        self._hourly_budget = 200

    def _consume_budget(self, call_count: int) -> None:
        if call_count > self._hourly_budget:
            raise SourceUnavailable("facebook-community", "meta hourly budget exceeded", retry_after_seconds=3600)
        self._hourly_budget -= call_count

    async def poll_source(self) -> list[dict[str, Any]]:
        token = os.environ.get("FACEBOOK_GRAPH_TOKEN", "").strip()
        if not token:
            raise SourceUnavailable("facebook-community", "facebook graph token is not configured", blocked=True)
        if self._transport is None:
            raise SourceUnavailable("facebook-community", "facebook transport is not configured", blocked=True)
        records = await self._transport.poll(endpoint_url=self._endpoint_url, access_token=token)
        if isinstance(records, tuple) and len(records) == 3:
            payloads, raw_bytes, content_type = records
            self._consume_budget(len(payloads))
            artifact = RawArtifact(
                raw_bytes=raw_bytes, content_type=content_type, source_uri=self._endpoint_url, file_format="json"
            )
            return [attach_raw_artifact(dict(item), artifact) for item in payloads]
        self._consume_budget(len(records) if hasattr(records, "__len__") else 1)
        return records

    def normalise(self, raw_payload: dict[str, Any]) -> dict[str, Any]:
        now = datetime.now(UTC).isoformat()
        created_raw = raw_payload.get("created_time")
        occurred_at = to_utc_iso_z(parse_iso_timestamp(created_raw, provider="facebook", field="created_time"))
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
            "occurredAt": occurred_at,
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
                "sourceTimestamp": occurred_at,
            },
        }

    def compute_canonical_key(self, raw_payload: dict[str, Any]) -> str:
        post_id = raw_payload.get("id", "")
        return f"facebook:{post_id}"
