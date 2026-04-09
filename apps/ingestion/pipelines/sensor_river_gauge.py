import logging
from typing import Any

import httpx

from apps.api.app.services.ingestion.pipeline_base import IngestionPipelineBase
from apps.ingestion.normalisers.json_observation_normaliser import normalise_json_observation

logger = logging.getLogger(__name__)

BOM_WATER_URL = "http://www.bom.gov.au/waterdata/services"

# Kisters API query to discover real-time river level timeseries
_KISTERS_TS_PARAMS: dict[str, str] = {
    "service": "kisters",
    "type": "queryServices",
    "request": "getTimeseriesList",
    "format": "json",
    "parametertype_name": "Water Course Level",
    "ts_name": "DMQaQc.Merged.AsStored*",
    "returnfields": "station_no,station_name,ts_id,ts_name",
    "station_no": "2100*",
}


class RiverGaugePipeline(IngestionPipelineBase):
    """Polls BoM Water Data Online for river gauge JSON observations."""

    def __init__(self, endpoint_url: str | None = None, **kwargs: Any):
        self._endpoint_url = endpoint_url or BOM_WATER_URL
        super().__init__(
            pipeline_id="bom-river-gauges",
            data_source_ids=["bom-river-gauges"],
            poll_interval_seconds=300,
            trust_tier="tier_3_operational_sensor",
            expected_update_seconds=300,
            **kwargs,
        )

    async def poll_source(self) -> list[dict[str, Any]]:
        headers = {"User-Agent": "disaster-response-hub/1.0 (BoM data consumer)"}
        async with httpx.AsyncClient(timeout=60, follow_redirects=True) as client:
            # Step 1: Discover timeseries IDs for river level gauges
            resp = await client.get(self._endpoint_url, params=_KISTERS_TS_PARAMS, headers=headers)
            resp.raise_for_status()
            ts_list = resp.json()  # [[header], [row1], ...]

        if len(ts_list) < 2:
            return []

        payloads: list[dict[str, Any]] = []
        # Use first 10 gauges to keep poll lightweight
        for row in ts_list[1:11]:
            station_no, station_name, ts_id, ts_name = row[0], row[1], row[2], row[3]
            try:
                async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
                    val_params = {
                        "service": "kisters",
                        "type": "queryServices",
                        "request": "getTimeseriesValues",
                        "format": "json",
                        "ts_id": ts_id,
                        "period": "P7D",
                        "returnfields": "Timestamp,Value,Quality Code",
                    }
                    vresp = await client.get(self._endpoint_url, params=val_params, headers=headers)
                    vresp.raise_for_status()
                    vdata = vresp.json()
                    readings = vdata[0].get("data", []) if vdata else []
                    for reading in readings[-5:]:
                        payloads.append({
                            "observations": {"data": [{
                                "timestamp": reading[0],
                                "value": reading[1],
                                "quality": reading[2] if len(reading) > 2 else "",
                                "gauge_id": station_no,
                                "station_name": station_name,
                            }]},
                            "data_source_id": "bom-river-gauges",
                            "source_kind": "sensor",
                            "source_uri": self._endpoint_url,
                            "collection_method": "sensor_network",
                        })
            except Exception as exc:
                logger.warning("Failed to fetch ts_id %s for station %s: %s", ts_id, station_no, exc)

        return payloads[:50]

    def normalise(self, raw_payload: dict[str, Any]) -> dict[str, Any]:
        envelope = normalise_json_observation(raw_payload)
        envelope["category"] = "hydrology"
        return envelope

    def compute_canonical_key(self, raw_payload: dict[str, Any]) -> str:
        obs = raw_payload.get("observations", raw_payload)
        if isinstance(obs, dict):
            data = obs.get("data", [obs])
        else:
            data = [raw_payload]
        record = data[0] if data else raw_payload
        gauge_id = record.get("gauge_id", record.get("station_id", ""))
        timestamp = record.get("timestamp", record.get("local_date_time_full", ""))
        return f"bom-river-gauge:{gauge_id}:{timestamp}"
