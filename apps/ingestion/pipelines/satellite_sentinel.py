import logging
from typing import Any

import httpx

from apps.api.app.services.ingestion.pipeline_base import IngestionPipelineBase
from apps.ingestion.normalisers.binary_metadata_normaliser import normalise_binary_metadata

logger = logging.getLogger(__name__)

SENTINEL_CATALOGUE_URL = "https://scihub.copernicus.eu/dhus/search"


class SentinelSatellitePipeline(IngestionPipelineBase):
    """Sentinel satellite imagery metadata pipeline."""

    def __init__(self, endpoint_url: str | None = None, product_type: str = "multispectral", **kwargs: Any):
        self._endpoint_url = endpoint_url or SENTINEL_CATALOGUE_URL
        self._product_type = product_type
        super().__init__(
            pipeline_id="sentinel-satellite",
            data_source_ids=["sentinel-satellite"],
            poll_interval_seconds=21600,
            trust_tier="tier_3_operational_sensor",
            expected_update_seconds=21600,
            **kwargs,
        )

    async def poll_source(self) -> list[dict[str, Any]]:
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.get(self._endpoint_url, params={
                "q": "platformname:Sentinel-2 AND footprint:\"Intersects(POLYGON((112 -44,154 -44,154 -10,112 -10,112 -44)))\"",
                "rows": "10",
                "format": "json",
            })
            resp.raise_for_status()
            data = resp.json()

        entries = data.get("feed", {}).get("entry", [])
        if isinstance(entries, dict):
            entries = [entries]
        payloads: list[dict[str, Any]] = []
        for entry in entries[:20]:
            payloads.append({
                "data_source_id": "sentinel-satellite",
                "source_name": "Copernicus Sentinel-2",
                "source_kind": "sensor",
                "product_type": self._product_type,
                "source_uri": entry.get("link", [{}])[0].get("href", "") if isinstance(entry.get("link"), list) else "",
                "timestamp": entry.get("date", [{}])[0].get("content", "") if isinstance(entry.get("date"), list) else "",
                "coverage_bbox": [112.0, -44.0, 154.0, -10.0],
                "file_format": "jp2",
                "product_code": entry.get("title", ""),
                "collection_method": "satellite_downlink",
                "jurisdiction_id": "national",
            })
        return payloads

    def normalise(self, raw_payload: dict[str, Any]) -> dict[str, Any]:
        return normalise_binary_metadata(raw_payload)

    def compute_canonical_key(self, raw_payload: dict[str, Any]) -> str:
        product_code = raw_payload.get("product_code", "")
        timestamp = raw_payload.get("timestamp", "")
        return f"sentinel:{product_code}:{timestamp}"
