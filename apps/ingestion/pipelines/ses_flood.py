import logging
from typing import Any

import httpx

from apps.api.app.services.ingestion.pipeline_base import IngestionPipelineBase
from apps.ingestion.normalisers.geojson_normaliser import normalise_geojson_feature

logger = logging.getLogger(__name__)

STATE_CONFIGS: dict[str, dict[str, str]] = {
    "nsw": {
        "data_source_id": "nsw-ses-flood",
        "name": "NSW State Emergency Service — Flood Data",
        "feed_url": "https://www.ses.nsw.gov.au/api/flood/current",
        "state_key": "default",
    },
    "vic": {
        "data_source_id": "vic-ses-flood",
        "name": "VIC State Emergency Service — Flood Data",
        "feed_url": "https://www.ses.vic.gov.au/data/flood-incidents.json",
        "state_key": "default",
    },
    "qld": {
        "data_source_id": "qld-ses-flood",
        "name": "QLD State Emergency Service — Flood Data",
        "feed_url": "https://www.ses.qld.gov.au/data/flood-incidents.json",
        "state_key": "default",
    },
}


class SesFloodPipeline(IngestionPipelineBase):
    """State Emergency Service flood incident pipeline."""

    def __init__(self, state_code: str, endpoint_url: str | None = None, **kwargs: Any):
        if state_code not in STATE_CONFIGS:
            raise ValueError(f"Unknown state_code: {state_code}. Must be one of {list(STATE_CONFIGS)}")

        config = STATE_CONFIGS[state_code]
        self._state_code = state_code
        self._config = config
        self._endpoint_url = endpoint_url or config["feed_url"]

        super().__init__(
            pipeline_id=f"ses-flood-{state_code}",
            data_source_ids=[config["data_source_id"]],
            poll_interval_seconds=120,
            trust_tier="tier_1_authoritative_government",
            expected_update_seconds=120,
            **kwargs,
        )

    async def poll_source(self) -> list[dict[str, Any]]:
        headers = {"User-Agent": "disaster-response-hub/1.0"}
        async with httpx.AsyncClient(timeout=60, follow_redirects=True) as client:
            resp = await client.get(self._endpoint_url, headers=headers)
            resp.raise_for_status()
            data = resp.json()

        features = data.get("features", [])
        payloads: list[dict[str, Any]] = []
        for feature in features[:100]:
            feature["data_source_id"] = self._config["data_source_id"]
            feature["source_name"] = self._config["name"]
            feature["source_kind"] = "authoritative"
            feature["jurisdiction_id"] = self._state_code
            payloads.append(feature)
        return payloads

    def normalise(self, raw_payload: dict[str, Any]) -> dict[str, Any]:
        context = {
            "data_source_id": self._config["data_source_id"],
            "source_name": self._config["name"],
            "source_kind": "authoritative",
            "source_uri": self._endpoint_url,
            "jurisdiction_id": self._state_code,
            "state_key": self._config["state_key"],
        }
        envelope = normalise_geojson_feature(raw_payload, context)
        envelope["category"] = "hydrology"
        return envelope

    def compute_canonical_key(self, raw_payload: dict[str, Any]) -> str:
        props = raw_payload.get("properties", {})
        feature_id = raw_payload.get("id", props.get("id", ""))
        updated = props.get("updated", props.get("pubDate", ""))
        return f"{self._config['data_source_id']}:{feature_id}:{updated}"
