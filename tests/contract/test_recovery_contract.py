"""Contract tests for community recovery API."""

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
        title="Storm Delta",
        incident_type="storm",
        status="recovery",
        severity="warning",
        affected_jurisdiction_ids=["jur-1"],
        pprr_phase="recovery",
    )
    INCIDENTS[incident_id] = inc
    return inc


def _init_tracker(client, incident_id: str = "inc-1") -> dict:
    resp = client.post(f"/api/incidents/{incident_id}/recovery")
    assert resp.status_code == 200
    return resp.json()


# ---- POST /api/incidents/{id}/recovery ----


def test_initialise_recovery_tracker(client):
    _seed_incident()
    body = _init_tracker(client)
    assert body["incident_id"] == "inc-1"
    assert "tracker_id" in body


def test_initialise_tracker_incident_not_found(client):
    resp = client.post("/api/incidents/no-inc/recovery")
    assert resp.status_code == 404


# ---- GET /api/incidents/{id}/recovery/dashboard ----


def test_get_recovery_dashboard(client):
    _seed_incident()
    _init_tracker(client)
    resp = client.get("/api/incidents/inc-1/recovery/dashboard")
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body, dict)


def test_get_dashboard_no_tracker(client):
    _seed_incident()
    resp = client.get("/api/incidents/inc-1/recovery/dashboard")
    assert resp.status_code == 404


# ---- PUT /api/incidents/{id}/recovery/indicators/{name} ----


def test_update_recovery_indicator(client):
    _seed_incident()
    _init_tracker(client)
    resp = client.put(
        "/api/incidents/inc-1/recovery/indicators/air_quality",
        json={"value": 72.5, "update_source": "manual"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body, dict)


# ---- GET /api/incidents/{id}/recovery/community ----


def test_get_community_view(client):
    _seed_incident()
    _init_tracker(client)
    resp = client.get("/api/incidents/inc-1/recovery/community")
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body, dict)
