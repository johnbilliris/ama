"""Spec-038 / T-G08 — /healthz/evidence contract test."""

from __future__ import annotations

import pytest
from app.main import create_app
from app.services.evidence._clients import reset_registry
from fastapi.testclient import TestClient


@pytest.fixture()
def client(monkeypatch):
    monkeypatch.setenv("AMA_TEST_MODE", "1")
    monkeypatch.setenv(
        "APPLICATIONINSIGHTS_CONNECTION_STRING",
        "InstrumentationKey=00000000-0000-0000-0000-000000000000",
    )
    reset_registry()
    app = create_app()
    with TestClient(app) as c:
        yield c


def test_healthz_evidence_ok(client):
    r = client.get("/api/healthz/evidence")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] in {"ok", "degraded"}
    # Seven physical Cosmos containers plus archive, mirror, and telemetry.
    expected = {
        "kpi_ladder",
        "kpi_signals",
        "delta_scorecards",
        "causal_chains",
        "benchmark_register",
        "evidence_audit",
        "evidence_audit_dlq",
        "evidence_audit_cold_blob",
        "audit_change_feed_mirror",
        "app_insights_ingestion",
    }
    assert set(body["checks"]) == expected
    assert body["degraded"] is False
