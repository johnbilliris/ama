"""Contract tests for lessons management API."""

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
        title="Heat Event Echo",
        incident_type="extreme_heat",
        status="active",
        severity="warning",
        affected_jurisdiction_ids=["jur-1"],
    )
    INCIDENTS[incident_id] = inc
    return inc


def _create_lesson(client, **overrides) -> dict:
    payload = {
        "incident_id": "inc-1",
        "title": "Comms delay observed",
        "description": "Warning message delayed by 15 min",
        "aiims_function": "public_information",
        "pprr_phase": "response",
        "severity": "high",
        "created_by": "analyst-1",
        **overrides,
    }
    resp = client.post("/api/lessons/", json=payload)
    assert resp.status_code == 200
    return resp.json()


# ---- POST /api/lessons/ ----


def test_capture_lesson(client):
    _seed_incident()
    body = _create_lesson(client)
    assert "lesson_id" in body
    assert body["title"] == "Comms delay observed"
    assert body["status"] == "identified"


# ---- GET /api/lessons/ ----


def test_list_lessons(client):
    _seed_incident()
    _create_lesson(client)
    resp = client.get("/api/lessons/")
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body, list)
    assert len(body) >= 1


# ---- GET /api/lessons/{id} ----


def test_get_lesson_by_id(client):
    _seed_incident()
    created = _create_lesson(client)
    lesson_id = created["lesson_id"]
    resp = client.get(f"/api/lessons/{lesson_id}")
    assert resp.status_code == 200
    assert resp.json()["lesson_id"] == lesson_id


def test_get_lesson_not_found(client):
    resp = client.get("/api/lessons/nonexistent")
    assert resp.status_code == 404


# ---- PUT /api/lessons/{id}/assign ----


def test_assign_lesson(client):
    _seed_incident()
    created = _create_lesson(client)
    lesson_id = created["lesson_id"]
    resp = client.put(
        f"/api/lessons/{lesson_id}/assign",
        json={"assigned_to": "team-lead-1"},
    )
    assert resp.status_code == 200
    assert resp.json()["assigned_to"] == "team-lead-1"


# ---- PUT /api/lessons/{id}/resolve ----


def test_resolve_lesson(client):
    _seed_incident()
    created = _create_lesson(client)
    lesson_id = created["lesson_id"]
    # Assign first
    client.put(
        f"/api/lessons/{lesson_id}/assign",
        json={"assigned_to": "team-lead-1"},
    )
    resp = client.put(
        f"/api/lessons/{lesson_id}/resolve",
        json={
            "resolution_reference": "PR-123",
            "resolution_notes": "Fixed comms pipeline",
        },
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "resolved"


# ---- GET /api/lessons/trends ----


def test_get_trends(client):
    _seed_incident()
    _create_lesson(client)
    resp = client.get("/api/lessons/trends")
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body, dict)
