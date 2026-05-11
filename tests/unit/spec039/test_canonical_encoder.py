"""Spec-039 T016: tests for canonical encoder, SimulatedClock, correlation_id."""

from __future__ import annotations

import re

import pytest

from app.services.simulation.feeds._canonical import (
    LF,
    SimulatedClock,
    correlation_id,
    encode_ndjson,
)


def test_encode_ndjson_sorts_keys_and_terminates_with_lf():
    a = encode_ndjson({"b": 1, "a": 2})
    assert a.endswith(LF)
    # Sorted keys → 'a' first, then 'b'
    line = a.rstrip(LF).decode("utf-8")
    assert line.index('"a"') < line.index('"b"')


def test_encode_ndjson_byte_identical_across_invocations():
    record = {"z": [3, 2, 1], "payload": {"id": "x", "n": 5}, "ts": "2026-01-01T00:00:00Z"}
    a = encode_ndjson(record)
    b = encode_ndjson(record)
    assert a == b


def test_encode_ndjson_byte_identical_regardless_of_input_key_order():
    a = encode_ndjson({"x": 1, "y": 2, "z": 3})
    b = encode_ndjson({"z": 3, "y": 2, "x": 1})
    assert a == b


def test_simulated_clock_is_monotone():
    clk = SimulatedClock("s", 1)
    t1 = clk.tick(1)
    t2 = clk.tick(1)
    t3 = clk.tick(10)
    assert t1 < t2 < t3


def test_simulated_clock_iso_format():
    clk = SimulatedClock("s", 1)
    t = clk.tick(1)
    assert re.match(
        r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}Z$", t
    ), f"unexpected ISO format: {t}"


def test_simulated_clock_different_seeds_do_not_overlap():
    """FR-026 — two concurrent scenarios with different seeds must occupy
    disjoint time bands so concurrent runs do not collide."""
    a = SimulatedClock("scenario", 1)
    b = SimulatedClock("scenario", 2)
    a_times = {a.tick(1) for _ in range(50)}
    b_times = {b.tick(1) for _ in range(50)}
    assert a_times.isdisjoint(b_times)


def test_simulated_clock_deterministic_across_instances():
    a = SimulatedClock("nsw-bushfire-summer", 42)
    b = SimulatedClock("nsw-bushfire-summer", 42)
    seq_a = [a.tick(7) for _ in range(5)]
    seq_b = [b.tick(7) for _ in range(5)]
    assert seq_a == seq_b


def test_simulated_clock_rejects_negative_tick():
    clk = SimulatedClock("s", 1)
    with pytest.raises(ValueError):
        clk.tick(-1)


def test_correlation_id_is_32_char_hex():
    cid = correlation_id("s", 1, 0)
    assert re.match(r"^[0-9a-f]{32}$", cid)


def test_correlation_id_is_deterministic():
    assert correlation_id("s", 1, 0) == correlation_id("s", 1, 0)
    assert correlation_id("s", 1, 1) != correlation_id("s", 1, 0)
    assert correlation_id("s", 2, 0) != correlation_id("s", 1, 0)
