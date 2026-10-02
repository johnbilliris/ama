import pytest

from apps.ingestion.normalisers.json_observation_normaliser import normalise_json_observation


def _base_payload(record: dict):
    return {
        "observations": {"data": [record]},
        "data_source_id": "bom-aws-stations",
        "source_kind": "sensor",
        "source_uri": "https://example.test/obs",
        "collection_method": "sensor_network",
    }


def test_rejects_record_with_no_recognized_measurement() -> None:
    env = normalise_json_observation(
        _base_payload(
            {
                "station_id": "s1",
                "name": "Station 1",
                "timestamp": "2026-03-25T10:00:00Z",
                "lat": -33.8,
                "lon": 151.2,
                "foo": 10,
            }
        )
    )
    assert env["validationStatus"] == "rejected"


def test_rejects_non_finite_measurements() -> None:
    env = normalise_json_observation(
        _base_payload(
            {
                "station_id": "s2",
                "name": "Station 2",
                "timestamp": "2026-03-25T10:00:00Z",
                "lat": -33.8,
                "lon": 151.2,
                "air_temp": "NaN",
            }
        )
    )
    assert env["validationStatus"] == "rejected"


def test_rejects_out_of_range_value() -> None:
    env = normalise_json_observation(
        _base_payload(
            {
                "station_id": "s3",
                "name": "Station 3",
                "timestamp": "2026-03-25T10:00:00Z",
                "lat": -33.8,
                "lon": 151.2,
                "air_temp": 150,
            }
        )
    )
    assert env["validationStatus"] == "rejected"


def test_accepts_boundary_values() -> None:
    env = normalise_json_observation(
        _base_payload(
            {
                "station_id": "s4",
                "name": "Station 4",
                "timestamp": "2026-03-25T10:00:00Z",
                "lat": -33.8,
                "lon": 151.2,
                "air_temp": -20.0,
                "wind_spd_kmh": 0.0,
                "press_msl": 1100.0,
            }
        )
    )
    assert env["validationStatus"] == "validated"
    assert env["payload"]["observations"]["temperature"] == -20.0


def test_requires_coordinates_from_record_or_metadata() -> None:
    with pytest.raises(ValueError, match="coordinates"):
        normalise_json_observation(
            _base_payload(
                {
                    "station_id": "s5",
                    "name": "Station 5",
                    "timestamp": "2026-03-25T10:00:00Z",
                    "air_temp": 25.0,
                }
            )
        )


def test_uses_station_metadata_coordinates() -> None:
    payload = _base_payload(
        {
            "station_id": "s6",
            "name": "Station 6",
            "timestamp": "2026-03-25T10:00:00Z",
            "air_temp": 22.0,
        }
    )
    payload["station_metadata"] = {"latitude": -37.8, "longitude": 145.0}
    env = normalise_json_observation(payload)
    assert env["location"]["coordinates"] == [145.0, -37.8]


def test_maps_river_value_and_parametertype_and_applies_threshold_crossing() -> None:
    payload = _base_payload(
        {
            "gauge_id": "210012",
            "station_name": "Gauge A",
            "timestamp": "2026-03-25T10:00:00Z",
            "value": 3.4,
            "parametertype": "Water Course Level",
            "quality": "1",
        }
    )
    payload["station_metadata"] = {"latitude": -33.7, "longitude": 150.9}
    payload["flood_thresholds"] = {"minor": 2.0, "moderate": 3.0, "major": 4.0}
    env = normalise_json_observation(payload)

    assert env["category"] == "hydrology"
    assert env["validationStatus"] == "validated"
    assert env["payload"]["observations"]["water_level"] == 3.4
    assert env["payload"]["qualityCode"] == "good"
    assert env["payload"]["thresholdCrossing"]["level"] == "moderate"
    assert env["confidenceScore"] == 0.9


def test_maps_epa_fields_to_canonical_measurements() -> None:
    env = normalise_json_observation(
        _base_payload(
            {
                "site_id": "epa-1",
                "name": "EPA Site",
                "timestamp": "2026-03-25T10:00:00Z",
                "PM2.5": 18.0,
                "PM10": 25.0,
                "O3": 11.0,
                "lat": -33.9,
                "lon": 151.1,
            }
        )
    )
    obs = env["payload"]["observations"]
    assert obs["pm25"] == 18.0
    assert obs["pm10"] == 25.0
    assert obs["ozone"] == 11.0

def test_bom_compact_utc_publication_timestamp_is_not_parsed_as_epoch_milliseconds() -> None:
    envelope = normalise_json_observation(
        _base_payload(
            {
                "wmo": 94767,
                "lat": -33.9,
                "lon": 151.2,
                "local_date_time_full": "20260922183000",
                "aifstime_utc": "20260922083000",
                "air_temp": 20.0,
            }
        )
    )

    assert envelope["occurredAt"] == "2026-09-22T08:30:00Z"
    assert envelope["payload"]["publicationTimestamp"] == "2026-09-22T08:30:00Z"
