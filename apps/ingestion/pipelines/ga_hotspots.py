import logging
from typing import Any

import httpx

from apps.api.app.services.ingestion.pipeline_base import IngestionPipelineBase
from apps.ingestion.normalisers.geojson_normaliser import normalise_geojson_feature

logger = logging.getLogger(__name__)

GA_HOTSPOTS_URL = "https://hotspots.dea.ga.gov.au/data/recent-hotspots.json"


class GaHotspotPipeline(IngestionPipelineBase):
    """Polls GA Digital Earth Australia Hotspots service for satellite-detected thermal anomalies (FR-005)."""

    def __init__(self, **kwargs: Any):
        super().__init__(
            pipeline_id="ga-hotspots",
            data_source_ids=["ga-sentinel-hotspots"],
            poll_interval_seconds=900,
            trust_tier="tier_1_authoritative_government",
            expected_update_seconds=600,
            **kwargs,
        )

    async def poll_source(self) -> list[dict[str, Any]]:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.get(GA_HOTSPOTS_URL)
            resp.raise_for_status()
            data = resp.json()

        features = data.get("features", [])
        payloads = []
        for feature in features[:50]:
            feature["data_source_id"] = "ga-sentinel-hotspots"
            feature["source_name"] = "Geoscience Australia — Sentinel Hotspot Data"
            feature["source_kind"] = "authoritative"
            feature["jurisdiction_id"] = "national"
            payloads.append(feature)
        return payloads

    def normalise(self, raw_payload: dict[str, Any]) -> dict[str, Any]:
        context = {
            "data_source_id": "ga-sentinel-hotspots",
            "source_name": "Geoscience Australia — Sentinel Hotspot Data",
            "source_kind": "authoritative",
            "source_uri": GA_HOTSPOTS_URL,
            "jurisdiction_id": "national",
        }
        envelope = normalise_geojson_feature(raw_payload, context)
        envelope["category"] = "fire"
        return envelope

    def compute_canonical_key(self, raw_payload: dict[str, Any]) -> str:
        props = raw_payload.get("properties", {})
        hotspot_id = props.get("id", props.get("hotspot_id", ""))
        acq_time = props.get("datetime", props.get("acq_time", ""))
        return f"ga-hotspot:{hotspot_id}:{acq_time}"
