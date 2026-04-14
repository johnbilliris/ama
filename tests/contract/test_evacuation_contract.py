"""Contract tests for evacuation stage management API."""

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
        title="Flood Foxtrot",
        incident_type="flood",
        status="active",
        severity="emergency",
        affected_jurisdiction_ids=["jur-1"],
    )
    INCIDENTS[incident_id] = inc
    return inc


def _create_stage(client, incident_id: str = "inc-1") -> dict:
    resp = client.post(
        f"/api/incidents/{incident_id}/evacuation/stages",
        json={
            "plan_id": "plan-1",
            "decision_authority": "ic-user",
            "decision_rationale": "Flood waters rising",
            "evacuation_type": "pre_warned",
            "evacuation_approach": "directed",
            "evacuation_scope": "total",
        },
    )
    assert resp.status_code == 200
    return resp.json()


# ---- POST /api/incidents/{id}/evacuation/stages ----


def test_create_evacuation_stage(client):
    _seed_incident()
    body = _create_stage(client)
    assert body["incident_id"] == "inc-1"
    assert body["current_stage"] == "decision"
    assert "stage_id" in body


def test_create_stage_incident_not_found(client):
    resp = client.post(
        "/api/incidents/no-inc/evacuation/stages",
        json={
            "plan_id": "plan-1",
            "decision_authority": "ic-user",
            "decision_rationale": "test",
        },
    )
    assert resp.status_code == 404


# ---- POST .../stages/{id}/transition ----


def test_transition_stage(client):
    _seed_incident()
    stage = _create_stage(client)
    stage_id = stage["stage_id"]
    resp = client.post(
        f"/api/incidents/inc-1/evacuation/stages/{stage_id}/transition",
        json={
            "target_stage": "warning",
            "authorized_by": "ic-user",
            "rationale": "Issue evacuation warning",
        },
    )
    assert resp.status_code == 200
    assert resp.json()["current_stage"] == "warning"


def test_transition_invalid_target(client):
    _seed_incident()
    stage = _create_stage(client)
    stage_id = stage["stage_id"]
    resp = client.post(
        f"/api/incidents/inc-1/evacuation/stages/{stage_id}/transition",
        json={
            "target_stage": "completed",
            "authorized_by": "ic-user",
            "rationale": "Skip to end",
        },
    )
    assert resp.status_code == 409


# ---- GET .../stages/{id} ----


def test_get_stage(client):
    _seed_incident()
    stage = _create_stage(client)
    stage_id = stage["stage_id"]
    resp = client.get(f"/api/incidents/inc-1/evacuation/stages/{stage_id}")
    assert resp.status_code == 200
    assert resp.json()["stage_id"] == stage_id


# ---- PUT .../stages/{id}/withdrawal ----


def test_update_withdrawal_fields(client):
    _seed_incident()
    stage = _create_stage(client)
    stage_id = stage["stage_id"]
    # Transition to warning then withdrawal
    client.post(
        f"/api/incidents/inc-1/evacuation/stages/{stage_id}/transition",
        json={
            "target_stage": "warning",
            "authorized_by": "ic-user",
            "rationale": "warn",
        },
    )
    client.post(
        f"/api/incidents/inc-1/evacuation/stages/{stage_id}/transition",
        json={
            "target_stage": "withdrawal",
            "authorized_by": "ic-user",
            "rationale": "begin withdrawal",
        },
    )
    resp = client.put(
        f"/api/incidents/inc-1/evacuation/stages/{stage_id}/withdrawal",
        json={"population_moved": 1500},
    )
    assert resp.status_code == 200
    assert resp.json()["population_moved"] == 1500
