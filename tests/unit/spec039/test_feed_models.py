"""Spec-039 T019: tests for feed Pydantic models."""

from __future__ import annotations

import pytest
from app.services.simulation.feeds._models import (
    CanonicalRecord,
    FeedParams,
    ScenarioDefinition,
)
from pydantic import ValidationError

GOOD_RECORD = {
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


def test_canonical_record_valid():
    rec = CanonicalRecord.model_validate(GOOD_RECORD)
    assert rec.scenario_id == "nsw-bushfire-summer"


def test_canonical_record_rejects_bad_correlation_id():
    bad = dict(GOOD_RECORD, correlation_id="not-hex")
    with pytest.raises(ValidationError):
        CanonicalRecord.model_validate(bad)


def test_canonical_record_rejects_non_kebab_scenario():
    bad = dict(GOOD_RECORD, scenario_id="NSW Bushfire")
    with pytest.raises(ValidationError):
        CanonicalRecord.model_validate(bad)


def test_canonical_record_rejects_bad_timestamp():
    bad = dict(GOOD_RECORD, timestamp="2026-05-11T00:00:00Z")
    with pytest.raises(ValidationError):
        CanonicalRecord.model_validate(bad)


def test_canonical_record_rejects_oversize_seed():
    bad = dict(GOOD_RECORD, seed=(1 << 64))
    with pytest.raises(ValidationError):
        CanonicalRecord.model_validate(bad)


def test_feed_params_defaults_are_zero():
    p = FeedParams()
    assert (p.drop_rate, p.latency_jitter_us, p.malform_rate) == (0.0, 0, 0.0)


def test_feed_params_bounds():
    with pytest.raises(ValidationError):
        FeedParams(drop_rate=1.5)
    with pytest.raises(ValidationError):
        FeedParams(latency_jitter_us=-1)
    with pytest.raises(ValidationError):
        FeedParams(latency_jitter_us=10_000_001)


def test_scenario_definition_requires_feeds():
    with pytest.raises(ValidationError):
        ScenarioDefinition(
            scenario_id="x",
            default_seed=1,
            start_iso="2026-01-01T00:00:00Z",
            participating_feeds=(),
        )


def test_scenario_definition_validates_shape_ids():
    with pytest.raises(ValidationError):
        ScenarioDefinition(
            scenario_id="x",
            default_seed=1,
            start_iso="2026-01-01T00:00:00Z",
            participating_feeds=("not-a-shape",),
        )


def test_scenario_definition_happy_path():
    s = ScenarioDefinition(
        scenario_id="nsw-bushfire-summer",
        default_seed=42,
        start_iso="2026-01-01T00:00:00Z",
        participating_feeds=("bom.severe_weather_warning.v1", "bom.fire_weather_fdi.v1"),
    )
    assert s.default_seed == 42
