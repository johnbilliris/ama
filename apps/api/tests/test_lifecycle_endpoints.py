"""Phase E — lifecycle endpoint tests (T-E01/E02/E03/E04/E06 / FR-059)."""

from __future__ import annotations

import asyncio

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from apps.api.app.api.dependencies.simulation_rbac import (
    CoordinatorPrincipal,
    require_simulation_coordinator,
)
from apps.api.app.api.routes.simulations_036 import router
from apps.api.app.services.simulation import cancellation as cancel_scope
from apps.api.app.services.simulation.audit_writer import AuditWriter
from apps.api.app.services.simulation.controller_tools import ALLOW_LIST
from apps.api.app.services.simulation.repositories.simulation_state import (
    reset_simulation_state_repository_for_tests,
)


def _coordinator_principal() -> CoordinatorPrincipal:
    return CoordinatorPrincipal(
        user_id="coord-1",
        tenant_id="tenant-1",
        roles=("simulation.coordinator",),
    )


def _client() -> TestClient:
    AuditWriter.reset_memory_for_test()
    cancel_scope.reset_for_tests()
    reset_simulation_state_repository_for_tests()
    app = FastAPI()
    app.include_router(router, prefix="/api")
    app.dependency_overrides[require_simulation_coordinator] = _coordinator_principal
    return TestClient(app)


def test_pause_emits_audit_envelope() -> None:
    client = _client()
    sim_id = "11111111-2222-3333-4444-555555555555"
    r = client.post(f"/api/simulations/{sim_id}/pause")
    assert r.status_code == 200
    assert r.json()["state"] == "paused"
    entries = AuditWriter.memory_for_test(sim_id)
    assert any(e.entry_type == "lifecycle.paused" for e in entries)


def test_resume_emits_audit_envelope() -> None:
    client = _client()
    sim_id = "11111111-2222-3333-4444-666666666666"
    r = client.post(f"/api/simulations/{sim_id}/resume")
    assert r.status_code == 200
    assert r.json()["state"] == "active"
    entries = AuditWriter.memory_for_test(sim_id)
    assert any(e.entry_type == "lifecycle.resumed" for e in entries)


def test_abort_with_no_in_flight_emits_only_lifecycle_aborted() -> None:
    client = _client()
    sim_id = "11111111-2222-3333-4444-777777777777"
    r = client.post(f"/api/simulations/{sim_id}/abort", json={"reason": "drill-end"})
    assert r.status_code == 200
    body = r.json()
    assert body["aborted"] is True
    assert body["cancelled_invocations"] == 0
    entries = AuditWriter.memory_for_test(sim_id)
    types = {e.entry_type for e in entries}
    assert "lifecycle.aborted" in types
    assert "sub_agent.cancel" not in types


@pytest.mark.asyncio
async def test_abort_cancels_in_flight_and_emits_sub_agent_cancel() -> None:
    AuditWriter.reset_memory_for_test()
    cancel_scope.reset_for_tests()
    sim_id = "11111111-2222-3333-4444-888888888888"

    async def _busy(name: str) -> None:
        await asyncio.sleep(60.0)

    tasks = []
    for name in ("planning", "monitoring", "risk-assessment"):
        t = asyncio.create_task(_busy(name))
        await cancel_scope.register(
            simulation_id=sim_id,
            task=t,
            sub_agent=name,
            correlation_id=f"corr-{name}",
        )
        tasks.append(t)

    # Direct invocation of cancel_all + audit (mirroring the route handler).
    audit = AuditWriter()

    async def _record(sub_agent: str, correlation_id: str | None, reason: str) -> None:
        await audit.write(
            "sub_agent.cancel",
            simulation_id=sim_id,
            actor="cancellation_scope",
            details={
                "correlation_id": correlation_id or "",
                "sub_agent": sub_agent,
                "cancellation_reason": "aborted",
                "elapsed_ms": 0,
            },
        )

    cancelled = await cancel_scope.cancel_all(simulation_id=sim_id, on_cancel=_record, reason="aborted")
    # Drain cancellations
    for t in tasks:
        with pytest.raises(asyncio.CancelledError):
            await t

    assert cancelled == 3
    entries = AuditWriter.memory_for_test(sim_id)
    cancels = [e for e in entries if e.entry_type == "sub_agent.cancel"]
    assert len(cancels) == 3
    sub_agents = {e.details["sub_agent"] for e in cancels}
    assert sub_agents == {"planning", "monitoring", "risk-assessment"}


def test_controller_tools_allow_list_e06() -> None:
    """T-E06 — pause_simulation/resume_simulation present, abort_simulation absent."""
    assert "pause_simulation" in ALLOW_LIST
    assert "resume_simulation" in ALLOW_LIST
    assert "abort_simulation" not in ALLOW_LIST
    # inject_telemetry from Phase C also present
    assert "inject_telemetry" in ALLOW_LIST


def test_invalid_sim_id_400_lifecycle() -> None:
    client = _client()
    for verb in ("abort", "pause", "resume"):
        r = client.post(f"/api/simulations/not-a-uuid/{verb}")
        assert r.status_code == 400
