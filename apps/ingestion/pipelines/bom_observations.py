import logging
from typing import Any

import httpx

from apps.api.app.services.ingestion.pipeline_base import IngestionPipelineBase
from apps.ingestion.normalisers.json_observation_normaliser import normalise_json_observation

logger = logging.getLogger(__name__)

BOM_OBS_BASE = "http://www.bom.gov.au/fwo"
# Each state maps to (product_code, representative_station_wmo_id)
STATE_OBS_PRODUCTS: dict[str, tuple[str, str]] = {
    "nsw": ("IDN60901", "94768"),  # Sydney
    "vic": ("IDV60901", "95936"),  # Melbourne
    "qld": ("IDQ60901", "94576"),  # Brisbane
    "sa": ("IDS60901", "94672"),  # Adelaide
    "wa": ("IDW60901", "94610"),  # Perth
    "tas": ("IDT60901", "94970"),  # Hobart
    "nt": ("IDD60901", "94120"),  # Darwin
    "act": ("IDN60903", "94926"),  # Canberra
}


class BomObservationsPipeline(IngestionPipelineBase):
    """Polls BoM web service for JSON station observations (FR-004)."""

    def __init__(self, state: str = "nsw", **kwargs: Any):
        self._state = state
        product_code, station_wmo = STATE_OBS_PRODUCTS.get(state, ("IDN60901", "94768"))
        self._product_id = product_code
        self._station_wmo = station_wmo
        super().__init__(
            pipeline_id=f"bom-observations-{state}",
            data_source_ids=["bom-observations"],
            poll_interval_seconds=300,
            trust_tier="tier_3_operational_sensor",
            expected_update_seconds=600,
            **kwargs,
        )

    async def poll_source(self) -> list[dict[str, Any]]:
        url = f"{BOM_OBS_BASE}/{self._product_id}/{self._product_id}.{self._station_wmo}.json"
        headers = {"User-Agent": "disaster-response-hub/1.0 (BoM data consumer)"}
        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
            data = resp.json()

        observations = data.get("observations", {}).get("data", [])
        payloads = []
        for obs in observations:
            payloads.append(
                {
                    "observations": {"data": [obs]},
                    "data_source_id": "bom-observations",
                    "source_kind": "sensor",
                    "collection_method": "sensor_network",
                    "source_uri": url,
                    "jurisdiction_id": self._state,
                }
            )
        return payloads

    def normalise(self, raw_payload: dict[str, Any]) -> dict[str, Any]:
        return normalise_json_observation(raw_payload)

    def compute_canonical_key(self, raw_payload: dict[str, Any]) -> str:
        obs = raw_payload.get("observations", {})
        data = obs.get("data", [{}]) if isinstance(obs, dict) else [{}]
        record = data[0] if data else {}
        station = record.get("wmo", record.get("station_id", "unknown"))
        timestamp = record.get("local_date_time_full", "unknown")
        return f"bom-obs:{station}:{timestamp}"
