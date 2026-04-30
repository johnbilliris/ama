"""Contract tests for warp-speed endpoints (feature 026)."""

from __future__ import annotations

import base64
import json

import pytest
from fastapi.testclient import TestClient


def _auth_headers(sub: str) -> dict[str, str]:
    claims = {
        "sub": sub,
        "agency_id": "test-agency",
        "jurisdiction_ids": [],
        "roles": ["SimulationUser"],
    }
    token = base64.b64encode(json.dumps(claims).encode()).decode()
    return {"X-MS-CLIENT-PRINCIPAL": token}


@pytest.fixture
def client(monkeypatch):
    from app.api.routes import simulations as sim_routes
    from app.main import app
    from app.repositories.signal_repository import SignalRepository
    from app.repositories.simulation_event_repository import SimulationEventRepository
    from app.repositories.simulation_repository import SimulationRepository
    from app.services.scenario_seeding_service import ScenarioSeedingService
    from app.services.simulation_audit_writer import SimulationAuditWriter
    from app.services.simulation_clock_service import SimulationClockService
    from app.services.simulation_event_recorder import SimulationEventRecorder
    from app.services.simulation_service import SimulationService
    from app.services.warp_scheduler import WarpScheduler

    repo = SimulationRepository()
    event_repo = SimulationEventRepository()
    clock = SimulationClockService()
    recorder = SimulationEventRecorder(event_repo)
    audit = SimulationAuditWriter()
    signal_repo = SignalRepository()
    service = SimulationService(
        simulation_repository=repo,
        audit_writer=audit,
        clock_service=clock,
        event_recorder=recorder,
    )
    scheduler = WarpScheduler(
        signal_repository=signal_repo,
        event_repository=event_repo,
        simulation_repository=repo,
        clock_service=clock,
        event_recorder=recorder,
    )
    seeding = ScenarioSeedingService(
        signal_repository=signal_repo,
        audit_writer=audit,
        warp_scheduler=scheduler,
        event_recorder=recorder,
    )

    monkeypatch.setattr(sim_routes, "_repo", repo)
    monkeypatch.setattr(sim_routes, "_signal_repo", signal_repo)
    monkeypatch.setattr(sim_routes, "_event_repo", event_repo)
    monkeypatch.setattr(sim_routes, "_clock", clock)
    monkeypatch.setattr(sim_routes, "_recorder", recorder)
    monkeypatch.setattr(sim_routes, "_service", service)
    monkeypatch.setattr(sim_routes, "_scheduler", scheduler)
    monkeypatch.setattr(sim_routes, "_seeding", seeding)

    return TestClient(app)


def _create_sim(client, *, warp_speed=None, user_oid="user-1"):
    body = {
        "scenario_type": "Bushfire",
        "jurisdictions": ["NSW"],
        "participants": [user_oid],
    }
    if warp_speed is not None:
        body["warp_speed"] = warp_speed
    return client.post("/api/simulations", json=body, headers=_auth_headers(user_oid))


def test_create_with_warp_speed_returns_clock_fields(client):
    resp = _create_sim(client, warp_speed=10)
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["warp_speed"] == 10.0
    assert data["current_warp_speed"] == 10.0
    assert "accumulated_sim_seconds" in data
    assert "clock_paused" in data


def test_create_without_warp_speed_defaults_to_1(client):
    resp = _create_sim(client)
    assert resp.status_code == 201, resp.text
    assert resp.json()["current_warp_speed"] == 1.0


def test_create_with_invalid_warp_speed_400(client):
    resp = _create_sim(client, warp_speed=7)
    assert resp.status_code == 400


def test_get_simulation_returns_clock(client):
    created = _create_sim(client, warp_speed=5).json()
    tenant_id = created["tenant_id"]
    resp = client.get(f"/api/simulations/{tenant_id}", headers=_auth_headers("user-1"))
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["current_warp_speed"] == 5.0
    assert "current_sim_seconds" in data
    assert "playback_status" in data
    assert "elapsed_seconds" in data


def test_pause_resume_server_computed(client):
    created = _create_sim(client, warp_speed=10).json()
    tenant_id = created["tenant_id"]

    pause = client.post(f"/api/simulations/{tenant_id}/pause", json={}, headers=_auth_headers("user-1"))
    assert pause.status_code == 200, pause.text
    assert pause.json()["status"] == "Paused"
    assert "accumulated_sim_seconds" in pause.json()
    assert "elapsed_seconds" in pause.json()

    resume = client.post(f"/api/simulations/{tenant_id}/resume", json={}, headers=_auth_headers("user-1"))
    assert resume.status_code == 200, resume.text
    assert resume.json()["status"] == "Active"
    assert resume.json()["current_warp_speed"] == 10.0


def test_clock_endpoint(client):
    created = _create_sim(client, warp_speed=2).json()
    tenant_id = created["tenant_id"]
    resp = client.get(f"/api/simulations/{tenant_id}/clock", headers=_auth_headers("user-1"))
    assert resp.status_code == 200, resp.text
    data = resp.json()
    for key in (
        "current_sim_seconds",
        "accumulated_sim_seconds",
        "current_warp_speed",
        "clock_paused",
        "delivery_lag_seconds",
    ):
        assert key in data


def test_change_warp_speed_controller_only(client):
    created = _create_sim(client, warp_speed=5, user_oid="controller-1").json()
    tenant_id = created["tenant_id"]

    bad = client.post(
        f"/api/simulations/{tenant_id}/warp-speed",
        json={"warp_speed": 7},
        headers=_auth_headers("controller-1"),
    )
    assert bad.status_code == 400

    client.post(
        f"/api/simulations/{tenant_id}/participants",
        json={"participants": [{"oid": "observer-2"}]},
        headers=_auth_headers("controller-1"),
    )
    forbidden = client.post(
        f"/api/simulations/{tenant_id}/warp-speed",
        json={"warp_speed": 24},
        headers=_auth_headers("observer-2"),
    )
    assert forbidden.status_code == 403

    ok = client.post(
        f"/api/simulations/{tenant_id}/warp-speed",
        json={"warp_speed": 24},
        headers=_auth_headers("controller-1"),
    )
    assert ok.status_code == 200, ok.text
    data = ok.json()
    assert data["previous_speed"] == 5.0
    assert data["current_warp_speed"] == 24.0
    assert "accumulated_sim_seconds" in data


def test_change_warp_speed_while_paused_succeeds(client):
    created = _create_sim(client, warp_speed=5, user_oid="controller-1").json()
    tenant_id = created["tenant_id"]

    pause = client.post(
        f"/api/simulations/{tenant_id}/pause",
        json={},
        headers=_auth_headers("controller-1"),
    )
    assert pause.status_code == 200, pause.text
    assert pause.json()["status"] == "Paused"

    changed = client.post(
        f"/api/simulations/{tenant_id}/warp-speed",
        json={"warp_speed": 10},
        headers=_auth_headers("controller-1"),
    )
    assert changed.status_code == 200, changed.text
    assert changed.json()["current_warp_speed"] == 10.0
    assert changed.json()["previous_speed"] == 5.0

    # Simulation should remain Paused after the warp change.
    detail = client.get(f"/api/simulations/{tenant_id}", headers=_auth_headers("controller-1")).json()
    assert detail["status"] == "Paused"
    assert detail["current_warp_speed"] == 10.0
