import logging
from typing import Any

import httpx

from apps.api.app.services.ingestion.pipeline_base import IngestionPipelineBase
from apps.ingestion.normalisers.geojson_normaliser import normalise_geojson_collection

logger = logging.getLogger(__name__)

# GA Earthquakes SPA has no public JSON API; use USGS GeoJSON feed
# filtered for Australia-region events in normalisation.
GA_EARTHQUAKES_URL = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_day.geojson"


class GaEarthquakePipeline(IngestionPipelineBase):
    """Polls GA Earthquakes web service for GeoJSON earthquake alerts (FR-005)."""

    def __init__(self, **kwargs: Any):
        super().__init__(
            pipeline_id="ga-earthquakes",
            data_source_ids=["ga-earthquake-alerts"],
            poll_interval_seconds=60,
            trust_tier="tier_1_authoritative_government",
            expected_update_seconds=60,
            **kwargs,
        )

    async def poll_source(self) -> list[dict[str, Any]]:
        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            resp = await client.get(GA_EARTHQUAKES_URL)
            resp.raise_for_status()
            data = resp.json()

        features = data.get("features", [])
        payloads = []
        for feature in features[:50]:
            coords = (feature.get("geometry") or {}).get("coordinates", [0, 0])
            lon, lat = coords[0], coords[1]
            # Filter to Australian region: lat -10 to -45, lon 110 to 155
            if not (-45 <= lat <= -10 and 110 <= lon <= 155):
                continue
            feature["data_source_id"] = "ga-earthquake-alerts"
            feature["source_name"] = "Geoscience Australia — Earthquake Alerts"
            feature["source_kind"] = "authoritative"
            feature["jurisdiction_id"] = "national"
            props = feature.get("properties", {})
            props.setdefault("category", "earthquake")
            payloads.append(feature)
        return payloads

    def normalise(self, raw_payload: dict[str, Any]) -> dict[str, Any]:
        from apps.ingestion.normalisers.geojson_normaliser import normalise_geojson_feature
        context = {
            "data_source_id": "ga-earthquake-alerts",
            "source_name": "Geoscience Australia — Earthquake Alerts",
            "source_kind": "authoritative",
            "source_uri": GA_EARTHQUAKES_URL,
            "jurisdiction_id": "national",
        }
        envelope = normalise_geojson_feature(raw_payload, context)
        envelope["category"] = "geohazard"
        return envelope

    def compute_canonical_key(self, raw_payload: dict[str, Any]) -> str:
        props = raw_payload.get("properties", {})
        eq_id = props.get("id", props.get("quake_id", ""))
        updated = props.get("updated", props.get("time", ""))
        return f"ga-eq:{eq_id}:{updated}"
