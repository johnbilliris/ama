"""AUD-022 — archive returns 202 and administrators delete without participant membership."""

from __future__ import annotations

import base64
import json
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient


def _auth_headers(sub: str, roles: list[str] | None = None) -> dict[str, str]:
    claims = {
        "sub": sub,
        "agency_id": "test-agency",
        "jurisdiction_ids": [],
        "roles": roles or ["SimulationUser"],
    }
    token = base64.b64encode(json.dumps(claims).encode()).decode()
    return {"X-MS-CLIENT-PRINCIPAL": token}


@pytest.fixture
def context(monkeypatch):
    from app.api.dependencies import simulation_composition
    from app.api.routes import simulations as sim_routes
    from app.main import app
    from app.repositories.signal_repository import SignalRepository
    from app.repositories.simulation_event_repository import SimulationEventRepository
    from app.repositories.simulation_repository import SimulationRepository
    from app.services.exercise_report_service import ExerciseReportService
    from app.services.simulation_audit_writer import SimulationAuditWriter
    from app.services.simulation_clock_service import SimulationClockService
    from app.services.simulation_event_recorder import SimulationEventRecorder
    from app.services.simulation_service import SimulationService

    repo = SimulationRepository()
    event_repo = SimulationEventRepository()
    signal_repo = SignalRepository()
    audit = SimulationAuditWriter()
    clock = SimulationClockService()
    recorder = SimulationEventRecorder(event_repo)
    reports = ExerciseReportService(
        simulation_repository=repo,
        signal_repository=signal_repo,
        event_repository=event_repo,
        audit_writer=audit,
    )
    service = SimulationService(
        simulation_repository=repo,
        audit_writer=audit,
        clock_service=clock,
        event_recorder=recorder,
        report_service=reports,
        signal_repository=signal_repo,
        event_repository=event_repo,
    )

    monkeypatch.setattr(sim_routes, "_repo", repo)
    monkeypatch.setattr(simulation_composition, "_SIMULATION_REPOSITORY", repo)
    monkeypatch.setattr(sim_routes, "_signal_repo", signal_repo)
    monkeypatch.setattr(sim_routes, "_event_repo", event_repo)
    monkeypatch.setattr(sim_routes, "_clock", clock)
    monkeypatch.setattr(sim_routes, "_recorder", recorder)
    monkeypatch.setattr(sim_routes, "_report_service", reports)
    monkeypatch.setattr(sim_routes, "_service", service)

    return TestClient(app), repo


def _create(client, oid: str = "owner-1") -> str:
    response = client.post(
        "/api/simulations",
        json={"scenario_type": "Flood", "jurisdictions": ["NSW"], "participants": [oid]},
        headers=_auth_headers(oid),
    )
    assert response.status_code == 201, response.text
    return response.json()["tenant_id"]


def test_archive_returns_202_archiving_then_completes(context):
    client, _repo = context
    tenant_id = _create(client)

    response = client.post(f"/api/simulations/{tenant_id}/archive", json={}, headers=_auth_headers("owner-1"))

    assert response.status_code == 202, response.text
    assert response.json()["status"] == "Archiving"

    # The background archive job runs once the response is returned.
    detail = client.get(f"/api/simulations/{tenant_id}", headers=_auth_headers("owner-1")).json()
    assert detail["status"] == "Archived"
    assert detail["archive_job_state"] == "completed"
    assert detail["archive_cleanup"]["verified"] is True


def test_administrator_deletes_without_participant_membership(context):
    client, repo = context
    tenant_id = _create(client)
    client.post(f"/api/simulations/{tenant_id}/archive", json={}, headers=_auth_headers("owner-1"))

    import anyio

    async def _expire_retention() -> None:
        tenant = await repo.get_by_tenant_id(tenant_id)
        await repo.update(tenant.model_copy(update={"delete_after": datetime.now(UTC) - timedelta(seconds=1)}))

    anyio.run(_expire_retention)

    admin_headers = _auth_headers("admin-outsider", ["SimulationUser", "simulation.admin"])
    response = client.delete(f"/api/simulations/{tenant_id}", headers=admin_headers)

    assert response.status_code == 204, response.text

    async def _evidence():
        return await repo.get_archive_evidence(tenant_id)

    evidence = anyio.run(_evidence)
    assert evidence is not None
    assert evidence["deleted_by"] == "admin-outsider"


def test_non_administrator_participant_cannot_delete(context):
    client, repo = context
    tenant_id = _create(client)
    client.post(f"/api/simulations/{tenant_id}/archive", json={}, headers=_auth_headers("owner-1"))

    import anyio

    async def _expire_retention() -> None:
        tenant = await repo.get_by_tenant_id(tenant_id)
        await repo.update(tenant.model_copy(update={"delete_after": datetime.now(UTC) - timedelta(seconds=1)}))

    anyio.run(_expire_retention)

    response = client.delete(f"/api/simulations/{tenant_id}", headers=_auth_headers("owner-1"))

    assert response.status_code == 403, response.text


def test_delete_before_retention_is_rejected(context):
    client, _repo = context
    tenant_id = _create(client)
    client.post(f"/api/simulations/{tenant_id}/archive", json={}, headers=_auth_headers("owner-1"))

    admin_headers = _auth_headers("admin-outsider", ["SimulationUser", "simulation.admin"])
    response = client.delete(f"/api/simulations/{tenant_id}", headers=admin_headers)

    assert response.status_code == 409
