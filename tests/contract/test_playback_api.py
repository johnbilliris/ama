"""Contract tests for playback + annotation endpoints (feature 026)."""

from __future__ import annotations

import base64
import json

import pytest
from fastapi.testclient import TestClient


def _auth_headers(sub: str) -> dict[str, str]:
    claims = {
        "sub": sub,
        "oid": sub,
        "agency_id": "test-agency",
        "jurisdiction_ids": [],
        "roles": ["SimulationUser"],
    }
    token = base64.b64encode(json.dumps(claims).encode()).decode()
    return {"X-MS-CLIENT-PRINCIPAL": token}


@pytest.fixture
def client(monkeypatch):
    from app.api.dependencies import simulation_composition
    from app.api.routes import simulation_playback as pb_routes
    from app.api.routes import simulations as sim_routes
    from app.main import app
    from app.repositories.signal_repository import SignalRepository
    from app.repositories.simulation_event_repository import SimulationEventRepository
    from app.repositories.simulation_repository import SimulationRepository
    from app.services.annotation_service import AnnotationService
    from app.services.playback_service import PlaybackService
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
    playback = PlaybackService(event_repository=event_repo, simulation_repository=repo)
    annotations = AnnotationService(event_repository=event_repo, simulation_repository=repo)

    monkeypatch.setattr(sim_routes, "_repo", repo)
    monkeypatch.setattr(simulation_composition, "_SIMULATION_REPOSITORY", repo)
    monkeypatch.setattr(sim_routes, "_signal_repo", signal_repo)
    monkeypatch.setattr(sim_routes, "_event_repo", event_repo)
    monkeypatch.setattr(sim_routes, "_clock", clock)
    monkeypatch.setattr(sim_routes, "_recorder", recorder)
    monkeypatch.setattr(sim_routes, "_service", service)
    monkeypatch.setattr(sim_routes, "_scheduler", scheduler)
    monkeypatch.setattr(sim_routes, "_seeding", seeding)

    monkeypatch.setattr(pb_routes, "_event_repo", event_repo)
    monkeypatch.setattr(pb_routes, "_repo", repo)
    monkeypatch.setattr(pb_routes, "_playback", playback)
    monkeypatch.setattr(pb_routes, "_annotations", annotations)

    return TestClient(app)


def _create(client, user="controller-1", warp=5):
    resp = client.post(
        "/api/simulations",
        json={
            "scenario_type": "Bushfire",
            "jurisdictions": ["NSW"],
            "participants": [user],
            "warp_speed": warp,
        },
        headers=_auth_headers(user),
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["tenant_id"]


def _seed_event(event_repo, tenant_id, seq, etype="signal_delivered", offset=0.0):
    from datetime import UTC, datetime

    from packages.domain.src.domain.models.simulation_event import SimulationEvent

    evt = SimulationEvent(
        tenant_id=tenant_id,
        event_seq=seq,
        event_type=etype,
        sim_time_offset=offset,
        wall_clock_time=datetime.now(UTC),
        payload={"seq": seq},
    )
    event_repo.append_event(evt)


# ── events ────────────────────────────────────────────────────────────


def test_get_events_returns_ordered(client, monkeypatch):
    from app.api.routes import simulation_playback as pb_routes

    tid = _create(client)
    for i in range(10, 15):
        _seed_event(pb_routes._event_repo, tid, i, offset=float(i))

    r = client.get(
        f"/api/simulations/{tid}/playback/events",
        headers=_auth_headers("controller-1"),
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["total_events"] >= 5
    seqs = [e["event_seq"] for e in body["events"]]
    assert seqs == sorted(seqs)
    assert "playback_status" in body


def test_get_events_after_seq_cursor(client):
    from app.api.routes import simulation_playback as pb_routes

    tid = _create(client)
    for i in range(1, 6):
        _seed_event(pb_routes._event_repo, tid, i, offset=float(i))

    r = client.get(
        f"/api/simulations/{tid}/playback/events?after_seq=3",
        headers=_auth_headers("controller-1"),
    )
    assert r.status_code == 200
    body = r.json()
    assert [e["event_seq"] for e in body["events"]] == [4, 5]


def test_get_events_non_participant_denied(client):
    tid = _create(client, user="controller-1")
    r = client.get(
        f"/api/simulations/{tid}/playback/events",
        headers=_auth_headers("stranger-9"),
    )
    assert r.status_code == 403


def test_get_events_not_found(client):
    r = client.get(
        "/api/simulations/sim-nonexistent/playback/events",
        headers=_auth_headers("u-1"),
    )
    assert r.status_code == 404


def test_get_events_empty_simulation(client):
    """Newly created sim may auto-record a state_change; that's a valid baseline."""
    tid = _create(client)
    r = client.get(
        f"/api/simulations/{tid}/playback/events",
        headers=_auth_headers("controller-1"),
    )
    assert r.status_code == 200
    body = r.json()
    # Initial state-change is recorded by the service; event count is low but present.
    assert body["total_events"] <= 5
    for e in body["events"]:
        assert e["event_type"] != "annotation"


def test_get_events_include_annotations_filter(client):
    from app.api.routes import simulation_playback as pb_routes

    tid = _create(client)
    _seed_event(pb_routes._event_repo, tid, 1, etype="signal_delivered")
    _seed_event(pb_routes._event_repo, tid, 2, etype="annotation")

    r = client.get(
        f"/api/simulations/{tid}/playback/events?include_annotations=false",
        headers=_auth_headers("controller-1"),
    )
    assert r.status_code == 200
    types = [e["event_type"] for e in r.json()["events"]]
    assert "annotation" not in types
    assert "signal_delivered" in types


# ── snapshots ─────────────────────────────────────────────────────────


def test_get_snapshots_returns_list(client):

    from app.api.routes import simulation_playback as pb_routes

    from packages.domain.src.domain.models.simulation_event import PlaybackSnapshot

    tid = _create(client)
    pb_routes._event_repo.save_snapshot(
        PlaybackSnapshot(
            tenant_id=tid,
            event_seq=100,
            sim_time_offset=300.0,
            state={"k": "v"},
        )
    )
    r = client.get(
        f"/api/simulations/{tid}/playback/snapshots",
        headers=_auth_headers("controller-1"),
    )
    assert r.status_code == 200
    assert len(r.json()["snapshots"]) == 1


# ── annotations (US5) ─────────────────────────────────────────────────


def test_create_annotation_201(client):
    tid = _create(client)
    r = client.post(
        f"/api/simulations/{tid}/playback/annotations",
        json={"sim_time_offset": 120.5, "text": "Key decision point"},
        headers=_auth_headers("controller-1"),
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["event_type"] == "annotation"
    assert body["payload"]["text"] == "Key decision point"
    assert body["payload"]["author_oid"] == "controller-1"


def test_annotation_appears_in_events(client):
    tid = _create(client)
    client.post(
        f"/api/simulations/{tid}/playback/annotations",
        json={"sim_time_offset": 10.0, "text": "note"},
        headers=_auth_headers("controller-1"),
    )
    r = client.get(
        f"/api/simulations/{tid}/playback/events",
        headers=_auth_headers("controller-1"),
    )
    types = [e["event_type"] for e in r.json()["events"]]
    assert "annotation" in types


def test_update_annotation_author_only(client):
    tid = _create(client)
    client.post(
        f"/api/simulations/{tid}/participants",
        json={"participants": [{"oid": "other-1"}]},
        headers=_auth_headers("controller-1"),
    )
    created = client.post(
        f"/api/simulations/{tid}/playback/annotations",
        json={"sim_time_offset": 0.0, "text": "orig"},
        headers=_auth_headers("controller-1"),
    ).json()
    ann_id = created["id"]

    bad = client.put(
        f"/api/simulations/{tid}/playback/annotations/{ann_id}",
        json={"text": "hacked"},
        headers=_auth_headers("other-1"),
    )
    assert bad.status_code == 403

    ok = client.put(
        f"/api/simulations/{tid}/playback/annotations/{ann_id}",
        json={"text": "updated"},
        headers=_auth_headers("controller-1"),
    )
    assert ok.status_code == 200
    assert ok.json()["payload"]["text"] == "updated"
    assert "updated_at" in ok.json()["payload"]


def test_delete_annotation_author_only(client):
    tid = _create(client)
    client.post(
        f"/api/simulations/{tid}/participants",
        json={"participants": [{"oid": "other-1"}]},
        headers=_auth_headers("controller-1"),
    )
    created = client.post(
        f"/api/simulations/{tid}/playback/annotations",
        json={"sim_time_offset": 0.0, "text": "x"},
        headers=_auth_headers("controller-1"),
    ).json()
    ann_id = created["id"]

    bad = client.delete(
        f"/api/simulations/{tid}/playback/annotations/{ann_id}",
        headers=_auth_headers("other-1"),
    )
    assert bad.status_code == 403

    ok = client.delete(
        f"/api/simulations/{tid}/playback/annotations/{ann_id}",
        headers=_auth_headers("controller-1"),
    )
    assert ok.status_code == 204


def test_create_annotation_non_participant_denied(client):
    tid = _create(client, user="controller-1")
    r = client.post(
        f"/api/simulations/{tid}/playback/annotations",
        json={"sim_time_offset": 0.0, "text": "x"},
        headers=_auth_headers("stranger-9"),
    )
    assert r.status_code == 403
