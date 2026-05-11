"""Spec-038 T013: contract test for apps/api/app/services/simulation/feeds/simulator_feed.schema.json.

Asserts the SimulatorRecord envelope requires simulated=true, scenario_id,
seed, source_shape, timestamp, feed_version, correlation_id, body.
"""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
SCHEMA_PATH = (
    REPO_ROOT
    / "apps"
    / "api"
    / "app"
    / "services"
    / "simulation"
    / "feeds"
    / "simulator_feed.schema.json"
)


@pytest.fixture(scope="module")
def schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def test_schema_file_exists():
    assert SCHEMA_PATH.exists()


def test_simulator_record_envelope_required(schema):
    rec = schema["$defs"]["SimulatorRecord"]
    required = set(rec["required"])
    for k in (
        "simulated",
        "fictitious",
        "residency",
        "scenario_id",
        "seed",
        "source_shape",
        "timestamp",
        "feed_version",
        "correlation_id",
        "body",
    ):
        assert k in required, f"FR-021/FR-027: SimulatorRecord must require {k}"
    assert rec["properties"]["simulated"]["const"] is True
    assert rec["properties"]["fictitious"]["const"] is True
    assert rec["properties"]["residency"]["const"] == "AU"


def test_warning_shaped_feed_requires_test_marker(schema):
    """FR-046 — bom severe-weather-warning + cyclone-track + ga tsunami-threat
    must embed body.test_marker == 'TEST — DO NOT BROADCAST'."""
    valid = {
        "simulated": True,
        "fictitious": True,
        "residency": "AU",
        "scenario_id": "nsw-bushfire-summer",
        "seed": 42,
        "source_shape": "bom.severe_weather_warning.v1",
        "timestamp": "2026-05-11T00:00:00.000000Z",
        "feed_version": "v1",
        "correlation_id": "a" * 32,
        "body": {"test_marker": "TEST — DO NOT BROADCAST"},
    }
    jsonschema.Draft202012Validator(schema["$defs"]["SimulatorRecord"]).validate(valid)

    bad = dict(valid, body={"area": "NSW"})
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.Draft202012Validator(schema["$defs"]["SimulatorRecord"]).validate(bad)


def test_non_warning_shape_does_not_require_test_marker(schema):
    """sensor.telemetry.v1 is not a warning shape."""
    rec = {
        "simulated": True,
        "fictitious": True,
        "residency": "AU",
        "scenario_id": "demo",
        "seed": 1,
        "source_shape": "sensor.telemetry.v1",
        "timestamp": "2026-05-11T00:00:00.000000Z",
        "feed_version": "v1",
        "correlation_id": "f" * 32,
        "body": {"reading": 42.0},
    }
    jsonschema.Draft202012Validator(schema["$defs"]["SimulatorRecord"]).validate(rec)


def test_fixture_header_validates(schema):
    hdr = {
        "_fixture_header": True,
        "fictitious": True,
        "residency": "AU",
        "licence": "CC-BY-4.0",
        "scenario_id": "nsw-bushfire-summer",
        "seed": 42,
    }
    jsonschema.Draft202012Validator(schema["$defs"]["FixtureHeader"]).validate(hdr)


def test_correlation_id_must_be_32hex(schema):
    bad = {
        "simulated": True,
        "fictitious": True,
        "residency": "AU",
        "scenario_id": "demo",
        "seed": 1,
        "source_shape": "sensor.telemetry.v1",
        "timestamp": "2026-05-11T00:00:00.000000Z",
        "feed_version": "v1",
        "correlation_id": "not-hex",
        "body": {},
    }
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.Draft202012Validator(schema["$defs"]["SimulatorRecord"]).validate(bad)
