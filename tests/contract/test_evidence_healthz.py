"""Spec-038 / T-G08 — /healthz/evidence contract test."""

from __future__ import annotations

import pytest
from app.main import create_app
from app.services.evidence._clients import reset_registry
from fastapi.testclient import TestClient


@pytest.fixture()
def client():
    reset_registry()
    app = create_app()
    with TestClient(app) as c:
        yield c


def test_healthz_evidence_ok(client):
    r = client.get("/api/healthz/evidence")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] in {"ok", "degraded"}
    # 7 Cosmos containers + cold-archive Blob
    expected = {
        "kpi_ladder",
        "kpi_signals",
        "delta_scorecards",
        "causal_chains",
        "benchmark_register",
        "evidence_audit",
        "evidence_audit_dlq",
        "evidence-audit-cold",
    }
    assert expected <= set(body["checks"].keys())
