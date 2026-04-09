import logging
from typing import Any

import httpx

from apps.api.app.services.ingestion.pipeline_base import IngestionPipelineBase
from apps.ingestion.normalisers.json_observation_normaliser import normalise_json_observation

logger = logging.getLogger(__name__)

BOM_AWS_URL = "http://www.bom.gov.au/fwo/IDN60901/IDN60901.94767.json"


class BomAwsSensorPipeline(IngestionPipelineBase):
    """Polls Bureau of Meteorology Automatic Weather Stations for JSON observations."""

    def __init__(self, endpoint_url: str | None = None, **kwargs: Any):
        self._endpoint_url = endpoint_url or BOM_AWS_URL
        super().__init__(
            pipeline_id="bom-aws-stations",
            data_source_ids=["bom-aws-stations"],
            poll_interval_seconds=300,
            trust_tier="tier_3_operational_sensor",
            expected_update_seconds=300,
            **kwargs,
        )

    async def poll_source(self) -> list[dict[str, Any]]:
        headers = {"User-Agent": "disaster-response-hub/1.0 (BoM data consumer)"}
        async with httpx.AsyncClient(timeout=60, follow_redirects=True) as client:
            resp = await client.get(self._endpoint_url, headers=headers)
            resp.raise_for_status()
            data = resp.json()

        observations = data.get("observations", {})
        records = observations.get("data", [])
        payloads: list[dict[str, Any]] = []
        for record in records[:50]:
            payloads.append({
                "observations": {"data": [record]},
                "data_source_id": "bom-aws-stations",
                "source_kind": "sensor",
                "source_uri": self._endpoint_url,
                "collection_method": "sensor_network",
            })
        return payloads

    def normalise(self, raw_payload: dict[str, Any]) -> dict[str, Any]:
        return normalise_json_observation(raw_payload)

    def compute_canonical_key(self, raw_payload: dict[str, Any]) -> str:
        obs = raw_payload.get("observations", raw_payload)
        if isinstance(obs, dict):
            data = obs.get("data", [obs])
        else:
            data = [raw_payload]
        record = data[0] if data else raw_payload
        station_id = record.get("wmo", record.get("station_id", ""))
        timestamp = record.get("local_date_time_full", record.get("timestamp", ""))
        return f"bom-aws:{station_id}:{timestamp}"
