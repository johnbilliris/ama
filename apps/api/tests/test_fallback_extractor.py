"""T-C05 fallback extractor unit tests (FR-016)."""

from __future__ import annotations

from uuid import uuid4

from apps.agents.simulation_telemetry_injection.fallback_extractor import extract


def test_temperature_maps_to_weather() -> None:
    sig = extract(
        prompt="temperature 41C in penrith at 14:00",
        simulation_id=str(uuid4()),
        tenant_id="sim-a",
    )
    assert sig is not None
    assert sig.category == "weather"
    assert sig.confidence == "low"


def test_evacuation_phrasing_maps_to_evacuation_category() -> None:
    sig = extract(
        prompt="evacuating sector 12",
        simulation_id=str(uuid4()),
        tenant_id="sim-a",
    )
    assert sig is not None
    assert sig.category == "evacuation"


def test_unknown_phrasing_returns_none() -> None:
    sig = extract(
        prompt="ZZZ random gibberish QQQ",
        simulation_id=str(uuid4()),
        tenant_id="sim-a",
    )
    assert sig is None
