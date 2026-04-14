"""Contract tests for PPRR lifecycle API."""

from __future__ import annotations

import pytest
from app.main import create_app
from app.services.state_store import INCIDENTS, reset_state
from fastapi.testclient import TestClient

from packages.domain.src.domain.models.incident import Incident


@pytest.fixture()
def client():
    app = create_app()
    with TestClient(app) as c:
        yield c
    reset_state()


def _seed_incident(incident_id: str = "inc-1") -> Incident:
    inc = Incident(
        incident_id=incident_id,
        title="Cyclone Charlie",
        incident_type="cyclone",
        status="active",
        severity="emergency",
        affected_jurisdiction_ids=["jur-1"],
        pprr_phase="response",
    )
    INCIDENTS[incident_id] = inc
    return inc


# ---- POST /api/incidents/{id}/pprr/transition ----


def test_transition_phase_success(client):
    _seed_incident()
    resp = client.post(
        "/api/incidents/inc-1/pprr/transition",
        json={
            "target_phase": "recovery",
            "rationale": "Threat has passed",
            "authorising_user": "ic-user",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "current_phase" in body or "pprr_phase" in body


def test_transition_phase_incident_not_found(client):
    resp = client.post(
        "/api/incidents/no-inc/pprr/transition",
        json={
            "target_phase": "recovery",
            "rationale": "test",
            "authorising_user": "user",
        },
    )
    assert resp.status_code == 404


# ---- GET /api/incidents/{id}/pprr ----


def test_get_pprr_phase_info(client):
    _seed_incident()
    resp = client.get("/api/incidents/inc-1/pprr")
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body, dict)


def test_get_pprr_incident_not_found(client):
    resp = client.get("/api/incidents/no-inc/pprr")
    assert resp.status_code == 404


# ---- POST /api/pprr/contexts ----


def test_create_pprr_context(client):
    resp = client.post(
        "/api/pprr/contexts",
        json={
            "context_type": "region",
            "context_reference_id": "region-nsw",
            "pprr_phase": "preparedness",
            "activated_by": "planner-1",
            "notes": "Pre-season prep",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["context_type"] == "region"
    assert body["pprr_phase"] == "preparedness"
    assert "context_id" in body


# ---- GET /api/pprr/contexts ----


def test_list_pprr_contexts(client):
    # Create one first
    client.post(
        "/api/pprr/contexts",
        json={
            "context_type": "scenario",
            "context_reference_id": "scenario-1",
            "pprr_phase": "prevention",
            "activated_by": "planner-2",
        },
    )
    resp = client.get("/api/pprr/contexts")
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body, list)
    assert len(body) >= 1
