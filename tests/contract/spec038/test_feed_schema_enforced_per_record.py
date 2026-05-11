"""Spec-038 T073: every emitted record validates against simulator_feed.schema.json.

In particular, warning-shaped feeds must embed ``"TEST — DO NOT BROADCAST"``
in ``body.test_marker`` (FR-046, F-001 amendment).
"""

from __future__ import annotations

import importlib
import json
from pathlib import Path

import jsonschema
import pytest

REPO = Path(__file__).resolve().parents[3]
SCHEMA = (
    REPO / "apps" / "api" / "app" / "services" / "simulation" / "feeds" / "simulator_feed.schema.json"
)

ALL_MODULES = [
    "bom_severe_weather_warning",
    "bom_cyclone_track",
    "bom_fire_weather_fdi",
    "bom_flood_gauge",
    "ga_earthquake_event",
    "ga_tsunami_threat",
    "epa_pm25",
    "traffic_road_closure",
    "utility_outage",
    "ambulance_cad",
    "social_chatter",
    "sensor_telemetry",
    "synthetic_fallback",
]

WARNING_MODULES = {
    "bom_severe_weather_warning",
    "bom_cyclone_track",
    "ga_tsunami_threat",
}


@pytest.fixture(scope="module")
def validator() -> jsonschema.Draft202012Validator:
    return jsonschema.Draft202012Validator(json.loads(SCHEMA.read_text("utf-8")))


@pytest.mark.parametrize("module_name", ALL_MODULES)
def test_each_record_passes_schema(module_name: str, validator) -> None:
    mod = importlib.import_module(f"app.services.simulation.feeds.{module_name}")
    records = list(mod.emit("nsw-bushfire-summer", 7, count=3))
    assert records, f"{module_name} emitted no records"
    for r in records:
        validator.validate(r.model_dump())


@pytest.mark.parametrize("module_name", sorted(WARNING_MODULES))
def test_warning_feeds_embed_test_marker(module_name: str) -> None:
    mod = importlib.import_module(f"app.services.simulation.feeds.{module_name}")
    for r in mod.emit("nsw-bushfire-summer", 7, count=2):
        body = r.body
        assert body.get("test_marker") == "TEST — DO NOT BROADCAST", (
            f"{module_name}: warning record missing FR-046 test_marker"
        )
