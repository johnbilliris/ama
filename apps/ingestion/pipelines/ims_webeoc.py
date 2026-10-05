from __future__ import annotations

import os
from datetime import UTC, datetime
from typing import Any

import httpx
from app.services.ingestion.exceptions import SourceUnavailable
from app.services.ingestion.raw_artifact import RawArtifact, attach_raw_artifact

from apps.api.app.services.ingestion.pipeline_base import IngestionPipelineBase
from apps.ingestion.normalisers.timestamps import parse_iso_timestamp, to_utc_iso_z


class _ImsTransport:
    async def poll(self, *, endpoint_url: str, bearer_token: str) -> tuple[list[dict[str, Any]], bytes, str]:
        headers = {
            "Authorization": f"Bearer {bearer_token}",
            "Accept": "application/json",
            "User-Agent": "ama-ingestion/ims",
        }
        async with httpx.AsyncClient(timeout=30, follow_redirects=False) as client:
            response = await client.get(endpoint_url, headers=headers)
            response.raise_for_status()
            data = response.json()
            records = data if isinstance(data, list) else data.get("incidents", data.get("items", []))
            if isinstance(records, dict):
                records = [records]
            return records, response.content, response.headers.get("Content-Type", "application/json")


class _BaseImsPipeline(IngestionPipelineBase):
    def __init__(
        self,
        *,
        pipeline_id: str,
        data_source_id: str,
        source_name: str,
        endpoint_url: str,
        token_env: str,
        provider: str,
        transport: Any = None,
        **kwargs: Any,
    ) -> None:
        self._provider = provider
        self._source_name = source_name
        self._endpoint_url = endpoint_url
        self._token_env = token_env
        self._transport = transport or _ImsTransport()
        super().__init__(
            pipeline_id=pipeline_id,
            data_source_ids=[data_source_id],
            poll_interval_seconds=120,
            trust_tier="tier_4_field_reports",
            expected_update_seconds=120,
            **kwargs,
        )

    async def poll_source(self) -> list[dict[str, Any]]:
        token = os.environ.get(self._token_env, "").strip()
        if not token:
            raise SourceUnavailable(self.data_source_ids[0], f"missing credential env {self._token_env}", blocked=True)

        try:
            records, raw_body, content_type = await self._transport.poll(
                endpoint_url=self._endpoint_url,
                bearer_token=token,
            )
        except httpx.HTTPStatusError as exc:
            code = exc.response.status_code
            if code in {401, 403}:
                raise SourceUnavailable(self.data_source_ids[0], f"IMS access denied ({code})", blocked=True) from exc
            if code == 429:
                retry_after = exc.response.headers.get("Retry-After")
                retry_seconds = int(retry_after) if retry_after and retry_after.isdigit() else None
                raise SourceUnavailable(
                    self.data_source_ids[0],
                    "IMS rate limit reached",
                    retry_after_seconds=retry_seconds,
                ) from exc
            raise

        artifact = RawArtifact(
            raw_bytes=raw_body,
            content_type=content_type,
            source_uri=self._endpoint_url,
            file_format="json",
        )
        return [attach_raw_artifact(self._normalise_record_shape(record), artifact) for record in records]

    def _normalise_record_shape(self, record: dict[str, Any]) -> dict[str, Any]:
        payload = dict(record)
        payload["_provider"] = self._provider
        return payload

    def normalise(self, raw_payload: dict[str, Any]) -> dict[str, Any]:
        occurred_at = _require_timestamp(raw_payload)
        lat, lon = _require_location(raw_payload)
        jurisdiction = str(raw_payload.get("jurisdiction", raw_payload.get("jurisdiction_id", ""))).strip().lower()
        if not jurisdiction:
            raise ValueError("IMS payload missing jurisdiction")

        reporter_identity = f"{self._provider}:authenticated"
        incident_type = str(raw_payload.get("incident_type", raw_payload.get("type", "community_report"))).lower()
        category = "community_report"
        if "fire" in incident_type:
            category = "fire"
        elif "flood" in incident_type:
            category = "hydrology"
        elif any(token in incident_type for token in ("storm", "cyclone", "weather")):
            category = "weather"

        return {
            "source": {
                "dataSourceId": self.data_source_ids[0],
                "name": self._source_name,
                "kind": "field_report",
            },
            "category": category,
            "occurredAt": occurred_at,
            "receivedAt": datetime.now(UTC).isoformat(),
            "jurisdictionId": jurisdiction,
            "location": {
                "type": "Point",
                "coordinates": [lon, lat],
                "precisionMeters": 100,
            },
            "payload": {
                "incidentId": str(raw_payload.get("incident_id", raw_payload.get("id", ""))),
                "title": str(raw_payload.get("title", raw_payload.get("description", ""))),
                "status": str(raw_payload.get("status", "")),
                "priority": str(raw_payload.get("priority", "")),
                "reporter": reporter_identity,
                "respondingUnits": raw_payload.get("responding_units", raw_payload.get("units", [])),
                "resources": raw_payload.get("resources", []),
                "situation": raw_payload.get("situation", raw_payload.get("summary", "")),
                "provider": self._provider,
            },
            "confidenceScore": 0.65,
            "validationStatus": "validated",
            "provenance": {
                "collectionMethod": "api_pull",
                "sourceUri": self._endpoint_url,
                "sourceTimestamp": occurred_at,
            },
        }

    def compute_canonical_key(self, raw_payload: dict[str, Any]) -> str:
        incident_id = str(raw_payload.get("incident_id", raw_payload.get("id", "")))
        updated_at = str(
            raw_payload.get("updated_at", raw_payload.get("last_modified", raw_payload.get("timestamp", "")))
        )
        return f"{self._provider}:{incident_id}:{updated_at}"


class WebEocPipeline(_BaseImsPipeline):
    def __init__(self, endpoint_url: str | None = None, transport: Any = None, **kwargs: Any) -> None:
        super().__init__(
            pipeline_id="webeoc-ims",
            data_source_id="webeoc-ims",
            source_name="WebEOC Incident Management",
            endpoint_url=endpoint_url or "https://webeoc.example.com/api/boards",
            token_env="IMS_WEBEOC_TOKEN",
            provider="webeoc",
            transport=transport,
            **kwargs,
        )


class IconPipeline(_BaseImsPipeline):
    def __init__(self, endpoint_url: str | None = None, transport: Any = None, **kwargs: Any) -> None:
        super().__init__(
            pipeline_id="icon-ims",
            data_source_id="icon-ims",
            source_name="ICON Incident Management",
            endpoint_url=endpoint_url or "https://icon.example.com/api/incidents",
            token_env="IMS_ICON_TOKEN",
            provider="icon",
            transport=transport,
            **kwargs,
        )


def _require_timestamp(raw_payload: dict[str, Any]) -> str:
    timestamp = raw_payload.get("updated_at", raw_payload.get("created_at", raw_payload.get("timestamp")))
    if timestamp is None or str(timestamp).strip() == "":
        raise ValueError("IMS payload missing timestamp")
    return to_utc_iso_z(parse_iso_timestamp(str(timestamp).strip(), provider="ims", field="timestamp"))


def _require_location(raw_payload: dict[str, Any]) -> tuple[float, float]:
    location_value = raw_payload.get("location")
    location_data = location_value if isinstance(location_value, dict) else {}
    lat = location_data.get("latitude", raw_payload.get("latitude"))
    lon = location_data.get("longitude", raw_payload.get("longitude"))
    if lat in (None, "") or lon in (None, ""):
        raise ValueError("IMS payload missing location coordinates")
    if not isinstance(lat, (int, float, str)) or not isinstance(lon, (int, float, str)):
        raise ValueError("IMS payload location coordinates must be numeric")
    return float(lat), float(lon)
