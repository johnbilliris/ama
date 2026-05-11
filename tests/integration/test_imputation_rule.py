"""Spec-038 / T-B02 — Forward-impute + small-sample gate."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.services.evidence.measurement.imputation import (
    forward_impute,
    small_sample_gate,
    small_sample_share,
)
from app.services.evidence.models.signal import CanonicalEventChain


def _ts(offset: int) -> datetime:
    return datetime(2026, 5, 11, 10, 0, tzinfo=UTC) + timedelta(minutes=offset)


def test_forward_impute_fills_missing_call_received():
    chain = CanonicalEventChain(
        call_received_at=None,
        dispatched_at=_ts(0),
        arrived_at=_ts(5),
        controlled_at=_ts(20),
        cleared_at=_ts(40),
    )
    out = forward_impute(chain)
    assert out.call_received_at == _ts(0)
    assert "call_received_at" in out.imputed_fields


def test_imputation_no_op_when_complete():
    chain = CanonicalEventChain(
        call_received_at=_ts(-2),
        dispatched_at=_ts(0),
        arrived_at=_ts(5),
        controlled_at=_ts(20),
        cleared_at=_ts(40),
    )
    out = forward_impute(chain)
    assert out.imputed_fields == []


def test_small_sample_gate_fires_above_10_percent():
    populated = CanonicalEventChain(
        call_received_at=_ts(0),
        dispatched_at=_ts(1),
        arrived_at=_ts(2),
        controlled_at=_ts(3),
        cleared_at=_ts(4),
    )
    chains = [populated for _ in range(8)] + [
        forward_impute(
            CanonicalEventChain(
                call_received_at=None, dispatched_at=_ts(1), arrived_at=_ts(2), controlled_at=_ts(3), cleared_at=_ts(4)
            )
        )
        for _ in range(2)
    ]
    assert small_sample_share(chains) == 0.2
    assert small_sample_gate(chains, threshold=0.10) is True
    assert small_sample_gate(chains, threshold=0.30) is False
