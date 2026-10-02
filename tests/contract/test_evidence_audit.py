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
    references = {
        "signal_id": "sig-1",
        "model_output_id": "model-1",
        "recommendation_id": "rec-1",
        "human_decision_id": "dec-1",
        "outcome_id": "out-1",
    }
    for referenced_id in references.values():
        audit_manager.record(
            kind="signal_ingested",
            value_id=referenced_id,
            actor="fixture",
        )
    audit_manager.record(
        kind="signal_ingested",
        value_id=value_id,
        actor="ingest",
        references=references,
    )
    r = client.get(f"/api/v1/evidence/audit/{value_id}")
    assert r.status_code == 200
    body = r.json()
    assert body["chain_complete"] is True
    assert body["missing_references"] == []
    assert len(body["entries"]) == 6
    assert all(entry["storage_source"] == "hot+cold" for entry in body["entries"])


def test_audit_trace_chain_incomplete(client):
    value_id = "kpi-value-002"
    audit_manager.record(
        kind="signal_ingested",
        value_id=value_id,
        actor="ingest",
        references={"signal_id": "sig-1"},
    )
    r = client.get(f"/api/v1/evidence/audit/{value_id}")
    assert r.status_code == 200
    assert r.json()["chain_complete"] is False
    assert "model_output_id" in r.json()["missing_references"]
