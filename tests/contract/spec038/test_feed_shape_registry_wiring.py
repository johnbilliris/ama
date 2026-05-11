"""Spec-038 T072: source-shape registry → feed-shape module wiring.

Asserts that every entry in ``source_shapes.json`` resolves to a feed
module under ``apps/api/app/services/simulation/feeds/`` exposing an
``emit()`` function whose envelope ``source_shape`` matches the registry id.
"""

from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]
REGISTRY = (
    REPO / "apps" / "api" / "app" / "services" / "simulation" / "feeds" / "source_shapes.json"
)

# Map shape id -> module name (the import side of the wiring contract).
SHAPE_TO_MODULE = {
    "bom.severe_weather_warning.v1": "bom_severe_weather_warning",
    "bom.cyclone_track.v1": "bom_cyclone_track",
    "bom.fire_weather_fdi.v1": "bom_fire_weather_fdi",
    "bom.flood_gauge.v1": "bom_flood_gauge",
    "ga.earthquake_event.v1": "ga_earthquake_event",
    "ga.tsunami_threat.v1": "ga_tsunami_threat",
    "epa.pm25.v1": "epa_pm25",
    "traffic.road_closure.v1": "traffic_road_closure",
    "utility.outage.v1": "utility_outage",
    "ambulance.cad.v1": "ambulance_cad",
    "social.chatter.v1": "social_chatter",
    "sensor.telemetry.v1": "sensor_telemetry",
    "synthetic.fallback.v1": "synthetic_fallback",
}


def _registry_ids() -> list[str]:
    return [s["id"] for s in json.loads(REGISTRY.read_text(encoding="utf-8"))["shapes"]]


def test_every_registry_id_has_module_mapping() -> None:
    ids = set(_registry_ids())
    assert ids == set(SHAPE_TO_MODULE), (
        f"registry/wiring drift — missing modules for {ids - set(SHAPE_TO_MODULE)}, "
        f"unknown mappings for {set(SHAPE_TO_MODULE) - ids}"
    )


@pytest.mark.parametrize("shape_id,module_name", sorted(SHAPE_TO_MODULE.items()))
def test_module_emit_envelope_matches_registry(shape_id: str, module_name: str) -> None:
    mod = importlib.import_module(
        f"app.services.simulation.feeds.{module_name}"
    )
    assert hasattr(mod, "emit"), f"{module_name} missing emit()"
    assert getattr(mod, "SOURCE_SHAPE", None) == shape_id, (
        f"{module_name}.SOURCE_SHAPE != {shape_id!r}"
    )
    # Smoke: emit a single record and check envelope.
    rec = next(iter(mod.emit("nsw-bushfire-summer", 1, count=1)))
    payload = rec.model_dump()
    assert payload["source_shape"] == shape_id
    assert payload["simulated"] is True
    assert payload["fictitious"] is True
    assert payload["residency"] == "AU"
    assert payload["feed_version"] == "v1"
