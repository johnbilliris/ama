"""Spec-038 T070: byte-identical canonical-NDJSON replay (FR-022, SC-005, CL-4).

Re-encodes a sample feed twice with the same ``(scenario_id, seed)`` and
asserts the SHA-256 of the resulting NDJSON streams are identical. This is
the load-bearing determinism contract for Phase 5.
"""

from __future__ import annotations

import hashlib

import pytest
from app.services.simulation.feeds._canonical import SimulatedClock, encode_ndjson


def _sha(stream: bytes) -> str:
    return hashlib.sha256(stream).hexdigest()


def _emit_to_bytes(emit_fn, scenario_id: str, seed: int, **kwargs) -> bytes:
    out = bytearray()
    clock = SimulatedClock(scenario_id, seed)
    for rec in emit_fn(scenario_id, seed, clock=clock, **kwargs):
        # Pydantic model -> dict via model_dump (sorted by canonical encoder).
        out.extend(encode_ndjson(rec.model_dump()))
    return bytes(out)


@pytest.mark.parametrize(
    "module_name",
    [
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
    ],
)
def test_feed_replay_byte_identical(module_name: str) -> None:
    import importlib

    mod = importlib.import_module(
        f"app.services.simulation.feeds.{module_name}"
    )
    a = _emit_to_bytes(mod.emit, "nsw-bushfire-summer", 42, count=4)
    b = _emit_to_bytes(mod.emit, "nsw-bushfire-summer", 42, count=4)
    assert a == b, f"{module_name}: replay not byte-identical"
    assert _sha(a) == _sha(b)
    assert len(a) > 0


def test_replay_writer_then_reader_round_trip(tmp_path) -> None:
    """T070 — write a stream then read it back and re-encode; byte-identical."""
    from app.services.simulation.feeds import bom_severe_weather_warning as mod
    from app.services.simulation.replay.ndjson_reader import read_ndjson
    from app.services.simulation.replay.ndjson_writer import write_ndjson

    path = tmp_path / "round.ndjson"
    records1 = list(
        mod.emit(
            "nsw-bushfire-summer",
            42,
            count=3,
            jurisdiction="nsw",
            clock=SimulatedClock("nsw-bushfire-summer", 42),
        )
    )
    sha_first = write_ndjson(records1, path)
    bytes_first = path.read_bytes()

    re_records = list(read_ndjson(path))
    # Re-encode to bytes — must equal the original file bytes.
    out = bytearray()
    for r in re_records:
        out.extend(encode_ndjson(r))
    assert bytes(out) == bytes_first
    assert hashlib.sha256(bytes_first).hexdigest() == sha_first
