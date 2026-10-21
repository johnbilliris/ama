"""AUD-026 — authorised, durable, truthfully-reported incident-mode transitions."""

from __future__ import annotations

import asyncio
import base64
import json
from uuid import uuid4

import pytest
from app.api.dependencies.simulation_composition import (
    get_resource_governor,
    reset_composition_for_tests,
    set_simulation_repository,
)
from app.main import create_app
from app.repositories.incident_mode_repository import (
    IncidentModeRepository,
    IncidentModeUnavailable,
)
from app.repositories.simulation_repository import SimulationRepository
from app.services.resource_governor import ProcessReservationStore, ResourceGovernor
from fastapi.testclient import TestClient

from packages.domain.src.domain.models.simulation_tenant import SimulationTenant

pytestmark = pytest.mark.spec007_isolation


def _headers(role: str, subject: str = "admin-1") -> dict[str, str]:
    claims = {
        "oid": subject,
        "roles": [role],
        "agency_id": "nema",
        "jurisdiction_ids": ["nsw"],
    }
    encoded = base64.b64encode(json.dumps(claims).encode("utf-8")).decode("ascii")
    return {"X-MS-CLIENT-PRINCIPAL": encoded}


class _OutageContainer:
    def read_item(self, **kwargs):  # noqa: ANN003, ANN201, ARG002
        raise RuntimeError("cosmos governance container unreachable")


class _OutageClient:
    def get_database_client(self, _name: str) -> _OutageClient:
        return self

    def get_container_client(self, _name: str) -> _OutageContainer:
        return _OutageContainer()


class _PartialFailureRepository:
    """Rejects the update for one tenant so mode fan-out cannot fully converge."""

    def __init__(self, inner: SimulationRepository, failing_tenant_id: str) -> None:
        self._inner = inner
        self._failing_tenant_id = failing_tenant_id

    def __getattr__(self, name: str):  # noqa: ANN204
        return getattr(self._inner, name)

    async def list_by_status(self, **kwargs):  # noqa: ANN003, ANN201
        return await self._inner.list_by_status(**kwargs)

    async def update(self, tenant):  # noqa: ANN001, ANN201
        if tenant.tenant_id == self._failing_tenant_id:
            raise RuntimeError("cosmos write rejected")
        return await self._inner.update(tenant)


class _RecordingRepository:
    def __init__(self) -> None:
        self.lookups: list[str] = []

    async def get_by_tenant_id(self, tenant_id: str):  # noqa: ANN201
        self.lookups.append(tenant_id)
        return None


@pytest.fixture(autouse=True)
def _environment(monkeypatch: pytest.MonkeyPatch) -> None:
    IncidentModeRepository.reset_for_tests()
    ProcessReservationStore.reset_for_tests()
    monkeypatch.setenv("AMA_ENVIRONMENT", "test")
    monkeypatch.setenv("AMA_TRUST_FORWARDED_PRINCIPAL", "1")
    monkeypatch.setenv("AMA_TEST_SUPPORT", "1")
    monkeypatch.delenv("COSMOS_ENDPOINT", raising=False)


@pytest.fixture
def repo() -> SimulationRepository:
    return SimulationRepository()


async def _tenant(repo: SimulationRepository) -> SimulationTenant:
    return await repo.create(
        SimulationTenant(
            tenant_id=f"sim-{uuid4()}",
            scenario_id=str(uuid4()),
            scenario_run_id=str(uuid4()),
            scenario_type="Flood",
            created_by="user-1",
            participants=["user-1"],
            status="Active",
        )
    )


# ── Authorisation ──


def test_anonymous_callers_cannot_change_incident_mode() -> None:
    with TestClient(create_app()) as client:
        declare = client.post("/api/incidents/declare")
        resolve = client.post("/api/incidents/resolve")

    assert declare.status_code == 401
    assert resolve.status_code == 401
    assert IncidentModeRepository._memory_document["version"] == 0


def test_non_administrator_is_refused_and_administrator_succeeds() -> None:
    with TestClient(create_app()) as client:
        denied = client.post("/api/incidents/declare", headers=_headers("SimulationUser", "operator-1"))
        allowed = client.post("/api/incidents/declare", headers=_headers("system-administrator"))

    assert denied.status_code == 403
    assert allowed.status_code == 200
    assert allowed.json()["status"] == "incident_declared"
    assert allowed.json()["converged"] is True


# ── Idempotent and concurrent transitions ──


@pytest.mark.asyncio
async def test_concurrent_resolves_produce_one_durable_transition(repo):
    await _tenant(repo)
    declarer = ResourceGovernor(repo, reservation_store=ProcessReservationStore())
    await declarer.declare_incident_with_status("admin-1")
    version_after_declare = IncidentModeRepository._memory_document["version"]

    first = ResourceGovernor(repo, incident_mode_repository=IncidentModeRepository())
    second = ResourceGovernor(repo, incident_mode_repository=IncidentModeRepository())
    results = await asyncio.gather(
        first.resolve_incident_with_status("admin-1"),
        second.resolve_incident_with_status("admin-2"),
    )

    assert sum(1 for result in results if result["mode_changed"]) == 1
    assert IncidentModeRepository._memory_document["version"] == version_after_declare + 1
    assert await first.incident_mode_active() is False


@pytest.mark.asyncio
async def test_repeated_declaration_is_idempotent(repo):
    await _tenant(repo)
    governor = ResourceGovernor(repo, reservation_store=ProcessReservationStore())

    first = await governor.declare_incident_with_status("admin-1")
    second = await governor.declare_incident_with_status("admin-1")

    assert first["mode_changed"] is True
    assert second["mode_changed"] is False
    assert second["mode_version"] == first["mode_version"]


# ── Governance storage outage must never look like local normal ──


@pytest.mark.asyncio
async def test_failing_read_item_is_reported_unavailable_not_normal(repo):
    outage = IncidentModeRepository(cosmos_client=_OutageClient())

    state = await outage.get_state()
    assert state.available is False
    assert state.source == "cosmos"

    with pytest.raises(IncidentModeUnavailable):
        await outage.get()

    governor = ResourceGovernor(repo, incident_mode_repository=outage)
    assert await governor.incident_mode_status() == (False, False)
    assert await governor.evaluate_utilisation() == "incident-throttled"

    mode, quota, notice = await governor.initial_tenant_mode()
    assert mode == "incident-throttled"
    assert quota == 20
    assert "unavailable" in notice


@pytest.mark.asyncio
async def test_local_memory_state_does_not_leak_into_a_configured_deployment(repo):
    local = IncidentModeRepository()
    await local.transition(active=True, actor_id="admin-1")

    configured = IncidentModeRepository(cosmos_client=_OutageClient())
    state = await configured.get_state()

    assert state.available is False
    assert state.document["active"] is False


# ── Partial fan-out must not claim complete success ──


@pytest.mark.asyncio
async def test_partial_apply_reports_pending_instead_of_complete(repo):
    stuck = await _tenant(repo)
    await _tenant(repo)
    governor = ResourceGovernor(
        _PartialFailureRepository(repo, stuck.tenant_id),
        reservation_store=ProcessReservationStore(),
    )

    outcome = await governor.declare_incident_with_status("admin-1")

    assert outcome["status"] == "incident_declare_pending"
    assert outcome["converged"] is False
    assert stuck.tenant_id in outcome["pending_tenant_ids"]
    unchanged = await repo.get_by_tenant_id(stuck.tenant_id)
    assert unchanged.throttle_mode == "normal"


# ── Route composition is resolved per call, not frozen at import ──


def test_routes_and_governor_follow_a_reset_composition() -> None:
    from app.api.routes import incidents as incident_routes
    from app.api.routes import simulations as simulation_routes

    original = SimulationRepository()
    governor = get_resource_governor()
    recording = _RecordingRepository()
    set_simulation_repository(recording)
    try:
        assert asyncio.run(simulation_routes._repo.get_by_tenant_id("sim-route-check")) is None
        assert asyncio.run(incident_routes._sim_repo.get_by_tenant_id("sim-incident-check")) is None
        assert asyncio.run(governor.check_write_allowed("sim-governor-check")) is False
        assert get_resource_governor() is governor
        assert simulation_routes._signal_repo._write_guard is governor
        assert incident_routes._signal_repository._write_guard is governor
    finally:
        reset_composition_for_tests(original)

    assert recording.lookups == ["sim-route-check", "sim-incident-check", "sim-governor-check"]
