import logging
import math
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx

from apps.api.app.services.ingestion.pipeline_base import IngestionPipelineBase
from apps.ingestion.normalisers.timestamps import parse_bom_local_timestamp, to_utc_iso_z

EPA_ENDPOINTS: dict[str, str] = {
    "nsw": "https://data.airquality.nsw.gov.au/api/Data/get_Observations",
    "vic": "https://www.epa.vic.gov.au/EPAAirWatch/api/observations",
    "qld": "https://apps.des.qld.gov.au/air-quality/api/observations",
}

logger = logging.getLogger(__name__)

EPA_METADATA_ENDPOINTS: dict[str, str] = {
    "nsw": "https://data.airquality.nsw.gov.au/api/Data/get_SiteDetails",
}


class EpaAirQualityPipeline(IngestionPipelineBase):
    """Polls the NSW EPA API for the latest air quality observations."""

    def __init__(
        self,
        endpoint_url: str | None = None,
        metadata_endpoint_url: str | None = None,
        **kwargs: Any,
    ):
        self._endpoint_url = endpoint_url or EPA_ENDPOINTS["nsw"]
        self._metadata_endpoint = metadata_endpoint_url or EPA_METADATA_ENDPOINTS["nsw"]
        super().__init__(
            pipeline_id="epa-air-quality",
            data_source_ids=["epa-air-quality"],
            poll_interval_seconds=3600,
            trust_tier="tier_3_operational_sensor",
            expected_update_seconds=3600,
            **kwargs,
        )

    async def poll_source(self) -> list[dict[str, Any]]:
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "disaster-response-hub/1.0",
        }
        async with httpx.AsyncClient(timeout=60, follow_redirects=True) as client:
            metadata_response = await client.get(self._metadata_endpoint, headers=headers)
            metadata_response.raise_for_status()
            sites = _parse_sites(metadata_response.json())

            observation_response = await client.post(self._endpoint_url, headers=headers)
            observation_response.raise_for_status()
            observations = _parse_observations(observation_response.json())

        payloads: list[dict[str, Any]] = []
        sites_without_coordinates: set[int] = set()
        regional_aggregates_skipped = 0
        for observation in observations:
            site_id = _required_site_id(observation, context="observation")
            site = sites.get(site_id)
            if site is None:
                raise ValueError(f"NSW EPA observation references unknown Site_Id {site_id}")
            try:
                _required_coordinate(site, "Longitude")
                _required_coordinate(site, "Latitude")
            except (TypeError, ValueError):
                if _is_regional_aggregate_site(site):
                    regional_aggregates_skipped += 1
                    continue
                sites_without_coordinates.add(site_id)
                continue
            payloads.append(
                {
                    "observation": observation,
                    "site": site,
                    "data_source_id": "epa-air-quality",
                    "source_kind": "sensor",
                    "source_uri": self._endpoint_url,
                    "collection_method": "sensor_network",
                    "jurisdiction_id": "nsw",
                }
            )
        if regional_aggregates_skipped:
            logger.info(
                "Skipped %d non-geospatial NSW EPA regional aggregate observations",
                regional_aggregates_skipped,
            )
        if sites_without_coordinates:
            logger.warning(
                "Skipped NSW EPA observations for sites without coordinates: %s",
                ", ".join(str(site_id) for site_id in sorted(sites_without_coordinates)),
            )
        return payloads

    def normalise(self, raw_payload: dict[str, Any]) -> dict[str, Any]:
        observation = _required_mapping(raw_payload.get("observation"), "observation")
        site = _required_mapping(raw_payload.get("site"), "site")
        parameter = _required_mapping(observation.get("Parameter"), "observation.Parameter")

        site_id = _required_site_id(observation, context="observation")
        station_name = str(site.get("SiteName") or f"NSW EPA site {site_id}").strip()
        observation_time = _observation_timestamp(observation)
        parameter_code = str(parameter.get("ParameterCode") or "").strip()

        validation_issues: list[str] = []
        if not parameter_code:
            validation_issues.append("Parameter.ParameterCode is missing")

        raw_value = observation.get("Value")
        numeric_value: float | None = None
        if raw_value is not None:
            if isinstance(raw_value, bool):
                validation_issues.append("Value must be a number or null")
            else:
                try:
                    numeric_value = float(raw_value)
                except (TypeError, ValueError):
                    validation_issues.append(f"Value {raw_value!r} is not numeric")
                else:
                    if not math.isfinite(numeric_value):
                        validation_issues.append(f"Value {raw_value!r} is not finite")
                        numeric_value = None

        air_quality_category = observation.get("AirQualityCategory")
        if air_quality_category is not None and not isinstance(air_quality_category, str):
            validation_issues.append("AirQualityCategory must be a string or null")
        if numeric_value is None and not str(air_quality_category or "").strip():
            validation_issues.append("observation has neither a numeric Value nor an AirQualityCategory")

        longitude = _required_coordinate(site, "Longitude")
        latitude = _required_coordinate(site, "Latitude")
        validation_status = "rejected" if validation_issues else "validated"

        provenance: dict[str, Any] = {
            "collectionMethod": raw_payload.get("collection_method", "sensor_network"),
            "sourceUri": str(raw_payload.get("source_uri", "")),
            "sourceTimestamp": observation_time,
        }
        if validation_issues:
            provenance["validationNotes"] = "; ".join(validation_issues)

        return {
            "source": {
                "dataSourceId": raw_payload.get("data_source_id", "epa-air-quality"),
                "name": station_name,
                "kind": raw_payload.get("source_kind", "sensor"),
            },
            "category": "weather",
            "occurredAt": observation_time,
            "receivedAt": datetime.now(UTC).isoformat(),
            "jurisdictionId": raw_payload.get("jurisdiction_id", "nsw"),
            "location": {
                "type": "Point",
                "coordinates": [longitude, latitude],
                "precisionMeters": 10,
            },
            "payload": {
                "stationId": str(site_id),
                "stationName": station_name,
                "region": site.get("Region"),
                "observationTimestamp": observation_time,
                "parameter": {
                    "code": parameter_code,
                    "description": parameter.get("ParameterDescription"),
                    "units": parameter.get("Units"),
                    "unitsDescription": parameter.get("UnitsDescription"),
                    "category": parameter.get("Category"),
                    "subCategory": parameter.get("SubCategory"),
                    "frequency": parameter.get("Frequency"),
                },
                "value": numeric_value,
                "airQualityCategory": air_quality_category,
                "determiningPollutant": observation.get("DeterminingPollutant"),
                "hourDescription": observation.get("HourDescription"),
                "rawRecord": observation,
            },
            "confidenceScore": 0.2 if validation_issues else 0.75,
            "validationStatus": validation_status,
            "provenance": provenance,
        }

    def compute_canonical_key(self, raw_payload: dict[str, Any]) -> str:
        observation = _required_mapping(raw_payload.get("observation"), "observation")
        parameter = _required_mapping(observation.get("Parameter"), "observation.Parameter")
        site_id = _required_site_id(observation, context="observation")
        timestamp = _observation_timestamp(observation)
        dimensions = (
            parameter.get("ParameterCode"),
            parameter.get("Category"),
            parameter.get("SubCategory"),
            parameter.get("Frequency"),
        )
        return "epa-air:{}:{}:{}:{}:{}:{}".format(site_id, *dimensions, timestamp)


def _is_regional_aggregate_site(site: dict[str, Any]) -> bool:
    site_id = _required_site_id(site, context="site")
    site_name = str(site.get("SiteName") or "").strip().casefold()
    region_name = str(site.get("Region") or "").strip().casefold()
    return site_id >= 10_000_000 and site_id % 10_000_000 == 0 and site_name == region_name


def _parse_sites(data: Any) -> dict[int, dict[str, Any]]:
    if not isinstance(data, list):
        raise TypeError("NSW EPA get_SiteDetails response must be an array")

    sites: dict[int, dict[str, Any]] = {}
    for index, item in enumerate(data):
        site = _required_mapping(item, f"site[{index}]")
        site_id = _required_site_id(site, context=f"site[{index}]")
        sites[site_id] = site
    return sites


def _parse_observations(data: Any) -> list[dict[str, Any]]:
    if isinstance(data, dict):
        if "Values" not in data:
            raise ValueError("NSW EPA get_Observations response is missing Values")
        data = data["Values"]
    if not isinstance(data, list):
        raise TypeError("NSW EPA get_Observations response must be a Values array or an array")
    return [_required_mapping(item, f"observation[{index}]") for index, item in enumerate(data)]


def _required_mapping(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise TypeError(f"NSW EPA {field} must be an object")
    return value


def _required_site_id(record: dict[str, Any], *, context: str) -> int:
    raw_site_id = record.get("Site_Id")
    if isinstance(raw_site_id, bool) or not isinstance(raw_site_id, int):
        raise TypeError(f"NSW EPA {context}.Site_Id must be an integer")
    return raw_site_id


def _required_coordinate(site: dict[str, Any], field: str) -> float:
    value = site.get(field)
    if isinstance(value, bool) or not isinstance(value, (int, float, str)):
        raise TypeError(f"NSW EPA site.{field} must be a finite number")
    try:
        coordinate = float(value)
    except (TypeError, ValueError) as exc:
        raise TypeError(f"NSW EPA site.{field} must be a finite number") from exc
    if not math.isfinite(coordinate):
        raise ValueError(f"NSW EPA site.{field} must be a finite number")
    return coordinate


def _observation_timestamp(observation: dict[str, Any]) -> str:
    raw_date = observation.get("Date")
    if not isinstance(raw_date, str):
        raise TypeError("NSW EPA observation.Date must be a string in yyyy-MM-dd format")
    date_text = raw_date.strip()
    try:
        date_start = datetime.strptime(date_text, "%Y-%m-%d")
    except ValueError as exc:
        raise ValueError(f"NSW EPA observation.Date must use yyyy-MM-dd: {date_text!r}") from exc

    raw_hour = observation.get("Hour")
    if isinstance(raw_hour, bool) or not isinstance(raw_hour, int):
        raise TypeError("NSW EPA observation.Hour must be an integer from 0 to 24")
    hour = raw_hour
    if hour < 0 or hour > 24:
        raise ValueError("NSW EPA observation.Hour must be from 0 to 24")

    period_end = date_start + timedelta(hours=hour)
    local_timestamp = period_end.strftime("%Y%m%d%H%M%S")
    return to_utc_iso_z(
        parse_bom_local_timestamp(
            local_timestamp,
            source_timezone="Australia/Sydney",
            provider="nsw_epa_air_quality",
            field="Date/Hour",
        )
    )
