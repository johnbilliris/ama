import logging
from typing import Any

import pytest

from apps.ingestion.pipeline_configs import PIPELINE_CONFIGS
from apps.ingestion.pipelines import sensor_epa_air
from apps.ingestion.pipelines.sensor_epa_air import EpaAirQualityPipeline


class _Response:
    def __init__(self, payload: Any):
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> Any:
        return self._payload


class _Client:
    def __init__(self, sites: Any, observations: Any):
        self._sites = sites
        self._observations = observations
        self.calls: list[tuple[str, str, dict[str, Any]]] = []

    async def __aenter__(self) -> "_Client":
        return self

    async def __aexit__(self, *_args: Any) -> None:
        return None

    async def get(self, url: str, **kwargs: Any) -> _Response:
        self.calls.append(("GET", url, kwargs))
        return _Response(self._sites)

    async def post(self, url: str, **kwargs: Any) -> _Response:
        self.calls.append(("POST", url, kwargs))
        return _Response(self._observations)


@pytest.fixture
def site() -> dict[str, Any]:
    return {
        "Site_Id": 39,
        "SiteName": "ROZELLE",
        "Longitude": 151.16395,
        "Latitude": -33.86433,
        "Region": "Sydney East",
    }


@pytest.fixture
def observation() -> dict[str, Any]:
    return {
        "Site_Id": 39,
        "Parameter": {
            "ParameterCode": "PM2.5",
            "ParameterDescription": "PM2.5",
            "Units": "µg/m³",
            "UnitsDescription": "micrograms per cubic metre",
            "Category": "Averages",
            "SubCategory": "Hourly",
            "Frequency": "Hourly average",
        },
        "Date": "2024-01-01",
        "Hour": 1,
        "HourDescription": "12 am - 1 am",
        "Value": 18.5,
        "AirQualityCategory": "GOOD",
        "DeterminingPollutant": None,
    }


@pytest.mark.asyncio
@pytest.mark.parametrize("response_envelope", [True, False])
async def test_polls_contract_endpoint_with_bodyless_post_and_accepts_live_shape(
    monkeypatch: pytest.MonkeyPatch,
    site: dict[str, Any],
    observation: dict[str, Any],
    response_envelope: bool,
) -> None:
    observations: Any = {"Values": [observation]} if response_envelope else [observation]
    client = _Client([site], observations)
    monkeypatch.setattr(sensor_epa_air.httpx, "AsyncClient", lambda **_kwargs: client)

    payloads = await EpaAirQualityPipeline(schema_validator=None).poll_source()

    assert len(payloads) == 1
    assert payloads[0]["observation"] == observation
    assert payloads[0]["site"] == site
    assert [call[0] for call in client.calls] == ["GET", "POST"]
    post_kwargs = client.calls[1][2]
    assert "json" not in post_kwargs
    assert "content" not in post_kwargs
    assert post_kwargs["headers"]["Content-Type"] == "application/json"


@pytest.mark.asyncio
async def test_poll_rejects_observation_for_unknown_site(
    monkeypatch: pytest.MonkeyPatch,
    site: dict[str, Any],
    observation: dict[str, Any],
) -> None:
    unknown_site_observation = {**observation, "Site_Id": 9999}
    client = _Client([site], {"Values": [unknown_site_observation]})
    monkeypatch.setattr(sensor_epa_air.httpx, "AsyncClient", lambda **_kwargs: client)

    with pytest.raises(ValueError, match="unknown Site_Id 9999"):
        await EpaAirQualityPipeline(schema_validator=None).poll_source()


def test_normalises_swagger_observation_fields(site: dict[str, Any], observation: dict[str, Any]) -> None:
    pipeline = EpaAirQualityPipeline(schema_validator=None)
    payload = {
        "observation": observation,
        "site": site,
        "data_source_id": "epa-air-quality",
        "source_kind": "sensor",
        "source_uri": pipeline._endpoint_url,
        "collection_method": "sensor_network",
        "jurisdiction_id": "nsw",
    }

    envelope = pipeline.normalise(payload)

    assert envelope["occurredAt"] == "2023-12-31T14:00:00Z"
    assert envelope["location"]["coordinates"] == [151.16395, -33.86433]
    assert envelope["validationStatus"] == "validated"
    assert envelope["payload"]["stationId"] == "39"
    assert envelope["payload"]["parameter"]["code"] == "PM2.5"
    assert envelope["payload"]["value"] == 18.5
    assert envelope["payload"]["airQualityCategory"] == "GOOD"


def test_accepts_categorical_air_quality_observation(site: dict[str, Any], observation: dict[str, Any]) -> None:
    categorical = {
        **observation,
        "Parameter": {**observation["Parameter"], "ParameterCode": "AQC", "Units": "category"},
        "Value": None,
        "AirQualityCategory": "POOR",
        "DeterminingPollutant": "PM2.5",
    }
    pipeline = EpaAirQualityPipeline(schema_validator=None)

    envelope = pipeline.normalise(
        {
            "observation": categorical,
            "site": site,
            "source_uri": pipeline._endpoint_url,
        }
    )

    assert envelope["validationStatus"] == "validated"
    assert envelope["payload"]["value"] is None
    assert envelope["payload"]["airQualityCategory"] == "POOR"
    assert envelope["payload"]["determiningPollutant"] == "PM2.5"


def test_canonical_key_includes_parameter_dimensions(site: dict[str, Any], observation: dict[str, Any]) -> None:
    pipeline = EpaAirQualityPipeline(schema_validator=None)
    payload = {"observation": observation, "site": site}

    key = pipeline.compute_canonical_key(payload)

    assert key == "epa-air:39:PM2.5:Averages:Hourly:Hourly average:2023-12-31T14:00:00Z"


def test_pipeline_config_enables_observation_endpoint() -> None:
    config = next(config for config in PIPELINE_CONFIGS if config.pipeline_id == "epa-air-quality")

    assert config.enabled is True
    assert config.endpoint_url.endswith("/api/Data/get_Observations")


@pytest.mark.asyncio
async def test_poll_skips_sites_without_coordinates_with_warning(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
    site: dict[str, Any],
    observation: dict[str, Any],
) -> None:
    site_without_coordinates = {**site, "Longitude": None}
    client = _Client([site_without_coordinates], [observation])
    monkeypatch.setattr(sensor_epa_air.httpx, "AsyncClient", lambda **_kwargs: client)

    payloads = await EpaAirQualityPipeline(schema_validator=None).poll_source()

    assert payloads == []
    assert "sites without coordinates: 39" in caplog.text


@pytest.mark.asyncio
async def test_poll_skips_regional_aggregate_without_warning(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
    observation: dict[str, Any],
) -> None:
    caplog.set_level(logging.INFO, logger="apps.ingestion.pipelines.sensor_epa_air")
    regional_site = {
        "Site_Id": 10_000_000,
        "SiteName": "Central Coast",
        "Longitude": None,
        "Latitude": None,
        "Region": "Central Coast",
    }
    regional_observation = {**observation, "Site_Id": 10_000_000}
    client = _Client([regional_site], [regional_observation])
    monkeypatch.setattr(sensor_epa_air.httpx, "AsyncClient", lambda **_kwargs: client)

    payloads = await EpaAirQualityPipeline(schema_validator=None).poll_source()

    assert payloads == []
    assert "regional aggregate observations" in caplog.text
    assert "WARNING" not in caplog.text
