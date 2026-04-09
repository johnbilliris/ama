import logging
from typing import Any

import httpx

from apps.api.app.services.ingestion.pipeline_base import IngestionPipelineBase
from apps.ingestion.normalisers.geojson_normaliser import normalise_geojson_feature

logger = logging.getLogger(__name__)

STATE_CONFIGS: dict[str, dict[str, str]] = {
    "nsw": {
        "data_source_id": "nsw-rfs-fires-near-me",
        "name": "NSW Rural Fire Service — Fires Near Me",
        "feed_url": "https://www.rfs.nsw.gov.au/feeds/majorIncidents.json",
        "state_key": "nsw-rfs",
    },
    "vic": {
        "data_source_id": "vic-cfa",
        "name": "VIC Emergency Management — OSOM",
        "feed_url": "https://www.emergency.vic.gov.au/public/osom-geojson.json",
        "state_key": "vic-cfa",
    },
    "qld": {
        "data_source_id": "qld-qfes",
        "name": "QLD Fire Department (formerly QFES)",
        "feed_url": "https://www.fire.qld.gov.au/current-incidents",
        "state_key": "qld-qfes",
    },
    "sa": {
        "data_source_id": "sa-cfs",
        "name": "SA Country Fire Service",
        "feed_url": "https://data.cfs.sa.gov.au/incidents.json",
        "state_key": "default",
    },
    "wa": {
        "data_source_id": "wa-dfes",
        "name": "WA Department of Fire and Emergency Services",
        "feed_url": "https://www.dfes.wa.gov.au/data/incidents.json",
        "state_key": "default",
    },
    "tas": {
        "data_source_id": "tas-tfs",
        "name": "TAS Fire Service",
        "feed_url": "https://www.fire.tas.gov.au/data/incidents.json",
        "state_key": "default",
    },
    "act": {
        "data_source_id": "act-esa",
        "name": "ACT Emergency Services Agency",
        "feed_url": "https://www.esa.act.gov.au/data/incidents.json",
        "state_key": "default",
    },
    "nt": {
        "data_source_id": "nt-pfes",
        "name": "NT Police, Fire and Emergency Services",
        "feed_url": "https://www.pfes.nt.gov.au/data/incidents.json",
        "state_key": "default",
    },
}


class FireServicePipeline(IngestionPipelineBase):
    """Parameterizable fire service pipeline for Australian state/territory fire agencies."""

    def __init__(self, state_code: str, endpoint_url: str | None = None, **kwargs: Any):
        if state_code not in STATE_CONFIGS:
            raise ValueError(f"Unknown state_code: {state_code}. Must be one of {list(STATE_CONFIGS)}")

        config = STATE_CONFIGS[state_code]
        self._state_code = state_code
        self._config = config
        self._endpoint_url = endpoint_url or config["feed_url"]

        super().__init__(
            pipeline_id=f"fire-{state_code}",
            data_source_ids=[config["data_source_id"]],
            poll_interval_seconds=60,
            trust_tier="tier_1_authoritative_government",
            expected_update_seconds=60,
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
        envelope["category"] = "fire"
        return envelope

    def compute_canonical_key(self, raw_payload: dict[str, Any]) -> str:
        props = raw_payload.get("properties", {})
        feature_id = raw_payload.get("id", props.get("id", ""))
        updated = props.get("updated", props.get("pubDate", ""))
        return f"{self._config['data_source_id']}:{feature_id}:{updated}"
