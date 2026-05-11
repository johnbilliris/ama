"""T-A01: SyntheticSignal model unit tests (FR-001/FR-006/FR-008)."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from domain.models.synthetic_signal import SyntheticSignal
from pydantic import ValidationError


def _kwargs(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "signal_id": str(uuid4()),
        "simulation_id": str(uuid4()),
        "tenant_id": "sim-tenant-a",
        "category": "weather",
        "parameters": {"temperature_c": 41.2},
        "observed_at": datetime.now(UTC),
        "freshness_window_seconds": 300,
        "confidence": "high",
    }
    base.update(overrides)
    return base


def test_synthetic_signal_default_synthetic_flag_is_true() -> None:
    sig = SyntheticSignal(**_kwargs())
    # FR-006: every injected event MUST carry this flag.
    assert sig.synthetic_signal is True
    assert sig.document_type == "synthetic_signal"


def test_synthetic_signal_categories_cover_fr008_set() -> None:
    expected = {
        "weather",
        "fire-behaviour",
        "hydrology",
        "geohazard",
        "utility",
        "transport",
        "evacuation",
        "resource",
        "comms-channel-state",
    }
    for cat in expected:
        SyntheticSignal(**_kwargs(category=cat))


def test_synthetic_signal_extra_field_forbidden() -> None:
    with pytest.raises(ValidationError):
        SyntheticSignal(**_kwargs(extra_field="boom"))


def test_synthetic_signal_partition_key_equals_simulation_id() -> None:
    sig = SyntheticSignal(**_kwargs())
    assert sig.partition_key == sig.simulation_id


def test_synthetic_signal_frozen() -> None:
    sig = SyntheticSignal(**_kwargs())
    with pytest.raises(ValidationError):
        sig.confidence = "low"  # type: ignore[misc]


def test_synthetic_signal_invalid_gps_rejected() -> None:
    with pytest.raises(ValidationError):
        SyntheticSignal(**_kwargs(gps={"lat": 95.0, "lng": 0.0}))


def test_synthetic_signal_freshness_negative_rejected() -> None:
    with pytest.raises(ValidationError):
        SyntheticSignal(**_kwargs(freshness_window_seconds=-1))
