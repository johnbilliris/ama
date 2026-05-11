"""Spec-038 / T-F01 — Audit trace contract test (incl. 5-step chain)."""

from __future__ import annotations

import pytest
from app.main import create_app
from app.services.evidence._clients import reset_registry
from app.services.evidence.instrumentation import audit_manager
from fastapi.testclient import TestClient


@pytest.fixture()
def client():
    reset_registry()
    from app.services.evidence.kpi_ladder import router as kpi_router

    kpi_router._SEEDED = False
    app = create_app()
    with TestClient(app) as c:
        yield c


def test_audit_trace_404_for_missing_value(client):
    r = client.get("/api/v1/evidence/audit/value-not-found")
    assert r.status_code == 404


def test_audit_trace_chain_complete_when_all_5_steps_referenced(client):
    value_id = "kpi-value-001"
    # Stage entries that together cover all 5 chain steps.
    audit_manager.record(
        kind="signal_ingested",
        value_id=value_id,
        actor="ingest",
        references={"signal": "sig-1", "model_output": "model-1"},
    )
    audit_manager.record(
        kind="ladder_version_published",
        value_id=value_id,
        actor="risk-mgr",
        references={"recommendation": "rec-1", "human_decision": "dec-1", "outcome": "out-1"},
    )
    r = client.get(f"/api/v1/evidence/audit/{value_id}")
    assert r.status_code == 200
    body = r.json()
    assert body["chain_complete"] is True
    assert len(body["entries"]) >= 2


def test_audit_trace_chain_incomplete(client):
    value_id = "kpi-value-002"
    audit_manager.record(
        kind="signal_ingested",
        value_id=value_id,
        actor="ingest",
        references={"signal": "sig-1"},
    )
    r = client.get(f"/api/v1/evidence/audit/{value_id}")
    assert r.status_code == 200
    assert r.json()["chain_complete"] is False
