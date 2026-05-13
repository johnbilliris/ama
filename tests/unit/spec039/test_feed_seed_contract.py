"""Spec-039 T074: deterministic generator-seed contract per feed shape.

Every feed module must accept and respect the ``(scenario_id, seed)`` pair,
producing byte-identical canonical NDJSON for identical inputs and
diverging streams for distinct seeds.
"""

from __future__ import annotations

import hashlib
import importlib

import pytest
from app.services.simulation.feeds._canonical import SimulatedClock, encode_ndjson

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


def _digest(emit_fn, scenario_id: str, seed: int) -> str:
    h = hashlib.sha256()
    clock = SimulatedClock(scenario_id, seed)
    for r in emit_fn(scenario_id, seed, count=3, clock=clock):
        h.update(encode_ndjson(r.model_dump()))
    return h.hexdigest()


@pytest.mark.parametrize("module_name", ALL_MODULES)
def test_same_seed_same_digest(module_name: str) -> None:
    mod = importlib.import_module(f"app.services.simulation.feeds.{module_name}")
    assert _digest(mod.emit, "nsw-bushfire-summer", 42) == _digest(mod.emit, "nsw-bushfire-summer", 42)


@pytest.mark.parametrize("module_name", ALL_MODULES)
def test_different_seed_different_digest(module_name: str) -> None:
    mod = importlib.import_module(f"app.services.simulation.feeds.{module_name}")
    assert _digest(mod.emit, "nsw-bushfire-summer", 42) != _digest(mod.emit, "nsw-bushfire-summer", 43)


def test_seed_zero_emits_userwarning_via_resolve_seed() -> None:
    """The shared seed contract from Phase 2 must warn on default 0 (CL-8)."""
    import warnings

    from scripts.generators._seed_contract import resolve_seed

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        resolved = resolve_seed(fn_arg=None, cli_arg=None, env={})
    assert resolved == 0
    assert any(issubclass(w.category, UserWarning) for w in caught)
