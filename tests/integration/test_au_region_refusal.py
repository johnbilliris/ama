"""Spec-038 / T-F03 — Non-AU region refused at write + audit row created."""

from __future__ import annotations

import pytest
from app.services.evidence._clients import get_registry, reset_registry
from app.services.evidence._guards import NonAuRegionError, assert_au_region
from app.services.evidence.instrumentation import signal_ingest


def _signal_payload(region: str) -> dict:
    return {
        "id": "sig-1",
        "scenario_id": "bushfire",
        "seed": "S1",
        "mode": "baseline",
        "kpi_id": "response_time_p1",
        "capability_id": "monitoring-agent",
        "capability_version": "0.1.0",
        "actor": "ingest",
        "source": "fixture",
        "occurred_at": "2026-05-11T10:00:00+00:00",
        "region": region,
        "chain": {},
        "confidence": {"value": "0.90"},
        "payload": {},
        "correlation_id": "test-cid",
    }


def test_au_region_accepted():
    reset_registry()
    payload = _signal_payload("australiaeast")
    signal_ingest.ingest_signal(payload)
    rows = get_registry().get("kpi_signals").all()
    assert len(rows) == 1


def test_non_au_region_refused_and_audit_logged():
    reset_registry()
    payload = _signal_payload("eastus2")
    with pytest.raises(NonAuRegionError):
        signal_ingest.ingest_signal(payload)
    audit_rows = get_registry().get("evidence_audit").all()
    refusals = [r for r in audit_rows if r["kind"] == "non_au_signal_refused"]
    assert len(refusals) == 1
    assert refusals[0]["payload"]["region"] == "eastus2"


def test_assert_au_region_helper_raises():
    with pytest.raises(NonAuRegionError):
        assert_au_region({"id": "x", "region": "westeurope"})
    # No-op when region missing
    assert_au_region({"id": "x"})
