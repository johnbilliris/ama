"""Spec-038 / T-F03 — Non-AU region refused at write + audit row created."""

from __future__ import annotations

from unittest import mock

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
    assert refusals[0]["payload"]["rejected_region"] == "eastus2"
    archived = get_registry().blob_archive.list_json(f"audit/{refusals[0]['audit_id']}/")
    assert len(archived) == 1
    assert archived[0][1]["payload_sha256"] == refusals[0]["payload_sha256"]


def test_assert_au_region_helper_raises():
    with pytest.raises(NonAuRegionError):
        assert_au_region({"id": "x", "region": "westeurope"})
    with pytest.raises(NonAuRegionError):
        assert_au_region({"id": "missing-region"})


def test_http_refusal_is_audited_before_422(monkeypatch):
    monkeypatch.setenv("AMA_TEST_MODE", "1")
    from app.main import create_app
    from fastapi.testclient import TestClient

    reset_registry()
    with TestClient(create_app()) as client:
        response = client.post(
            "/api/v1/evidence/signals",
            json=_signal_payload("westus"),
            headers={"x-ama-correlation-id": "refusal-order"},
        )
        rows = get_registry().get("evidence_audit").all()

    assert response.status_code == 422
    assert response.json()["title"] == "non-au-region-refused"
    assert response.headers["x-ama-correlation-id"] == "refusal-order"
    assert [row["kind"] for row in rows] == ["non_au_signal_refused"]
    assert get_registry().get("kpi_signals").all() == []


def test_http_refusal_returns_503_when_locked_blob_write_fails(monkeypatch):
    monkeypatch.setenv("AMA_TEST_MODE", "1")
    from app.main import create_app
    from fastapi.testclient import TestClient

    reset_registry()
    with TestClient(create_app()) as client:
        registry = get_registry()
        with mock.patch.object(
            registry.blob_archive,
            "create_json",
            side_effect=ConnectionError("private backend detail"),
        ):
            response = client.post(
                "/api/v1/evidence/signals",
                json=_signal_payload("westus"),
            )

    assert response.status_code == 503
    body = response.json()
    assert body["title"] == "audit-write-unavailable"
    assert "private backend detail" not in str(body)
    assert get_registry().get("kpi_signals").all() == []


def test_missing_region_is_durably_refused(monkeypatch):
    monkeypatch.setenv("AMA_TEST_MODE", "1")
    from app.main import create_app
    from fastapi.testclient import TestClient

    payload = _signal_payload("australiaeast")
    payload.pop("region")
    reset_registry()
    with TestClient(create_app()) as client:
        response = client.post("/api/v1/evidence/signals", json=payload)
        refusal = get_registry().get("evidence_audit").all()[0]

    assert response.status_code == 422
    assert refusal["payload"]["rejected_region"] == "<missing>"


@pytest.mark.parametrize(
    ("confidence", "expected_band"),
    [("0.49", "low"), ("0.50", "medium"), ("0.79", "medium"), ("0.80", "high")],
)
def test_confidence_band_boundaries(confidence, expected_band):
    from app.services.evidence.models.signal import ConfidenceScore

    assert ConfidenceScore(value=confidence).band == expected_band


def test_low_confidence_requires_explicit_fidelity_flags():
    from pydantic import ValidationError

    reset_registry()
    payload = _signal_payload("australiaeast")
    payload["confidence"] = {"value": "0.49"}

    with pytest.raises(ValidationError, match="advisory_only"):
        signal_ingest.ingest_signal(payload)

    payload["advisory_only"] = True
    payload["reduced_fidelity"] = True
    assert signal_ingest.ingest_signal(payload).confidence.band == "low"
