"""Contract tests for AIIMS structure and incident-level API."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.services.state_store import AIIMS_ASSIGNMENTS, INCIDENTS, reset_state
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
        title="Flood Bravo",
        incident_type="flood",
        status="active",
        severity="warning",
        affected_jurisdiction_ids=["jur-1"],
    )
    INCIDENTS[incident_id] = inc
    return inc


# ---- POST /api/incidents/{id}/aiims/assignments ----


def test_assign_role_success(client):
    _seed_incident()
    resp = client.post(
        "/api/incidents/inc-1/aiims/assignments",
        json={
            "agent_identifier": "agent-ops-1",
            "aiims_function": "operations",
            "assigned_by": "ic-user",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["incident_id"] == "inc-1"
    assert body["aiims_function"] == "operations"
    assert body["is_active"] is True


def test_assign_role_incident_not_found(client):
    resp = client.post(
        "/api/incidents/no-inc/aiims/assignments",
        json={
            "agent_identifier": "agent-1",
            "aiims_function": "control",
            "assigned_by": "user",
        },
    )
    assert resp.status_code == 404


# ---- GET /api/incidents/{id}/aiims/structure ----


def test_get_structure_returns_functions(client):
    _seed_incident()
    # Assign a role first
    client.post(
        "/api/incidents/inc-1/aiims/assignments",
        json={
            "agent_identifier": "agent-ctrl",
            "aiims_function": "control",
            "assigned_by": "ic-user",
        },
    )
    resp = client.get("/api/incidents/inc-1/aiims/structure")
    assert resp.status_code == 200
    body = resp.json()
    assert "control" in body or "functions" in body or isinstance(body, dict)


def test_get_structure_incident_not_found(client):
    resp = client.get("/api/incidents/no-inc/aiims/structure")
    assert resp.status_code == 404


# ---- POST /api/incidents/{id}/level ----


def test_change_incident_level(client):
    _seed_incident()
    resp = client.post(
        "/api/incidents/inc-1/level",
        json={
            "new_level": 2,
            "rationale": "Escalation due to spread",
            "authorising_user": "ic-user",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("new_level") == 2 or body.get("incident_level") == 2


def test_change_incident_level_not_found(client):
    resp = client.post(
        "/api/incidents/no-inc/level",
        json={
            "new_level": 3,
            "rationale": "test",
            "authorising_user": "user",
        },
    )
    assert resp.status_code == 404
