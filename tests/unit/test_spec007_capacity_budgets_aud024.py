"""AUD-024 — one concurrency cap across replicas, truthful counters, guarded writes."""

from __future__ import annotations

import pytest
from app.core.settings import get_settings
from app.repositories.signal_repository import SignalRepository
from app.repositories.simulation_repository import SimulationRepository
from app.services.resource_governor import ResourceGovernor
from app.services.simulation_service import SimulationService
from fastapi import HTTPException


class _StubReports:
    def __init__(self) -> None:
        self.report = type("Report", (), {"report_id": "rpt-capacity"})()

    async def generate_report(self, tenant_id):  # noqa: ANN001, ANN202, ARG002
        return self.report

    async def get_report(self, tenant_id):  # noqa: ANN001, ANN202, ARG002
        return self.report

    async def persist_archive_manifest(self, tenant_id, report, audit_writer=None):  # noqa: ANN001, ANN202, ARG002
        return f"simulation/{tenant_id}/archive/manifest.json"


@pytest.fixture
def repo() -> SimulationRepository:
    return SimulationRepository()


async def _create(service: SimulationService, oid: str):
    return await service.create_tenant(
        scenario_type="Flood",
        jurisdictions=["nsw"],
        participants=[oid],
        creator_oid=oid,
    )


@pytest.mark.asyncio
async def test_two_repository_instances_enforce_one_cap(repo):
    maximum = get_settings().max_concurrent_simulations
    service = SimulationService(simulation_repository=repo)
    for index in range(maximum):
        await _create(service, f"user-{index}")

    other_instance = SimulationRepository()
    other_service = SimulationService(simulation_repository=other_instance)

    with pytest.raises(HTTPException) as exc_info:
        await _create(other_service, "user-overflow")

    assert exc_info.value.status_code == 409
    assert len(exc_info.value.detail["activeSimulationIds"]) == maximum


@pytest.mark.asyncio
async def test_active_simulation_ids_exclude_archived_tenants(repo):
    maximum = get_settings().max_concurrent_simulations
    service = SimulationService(simulation_repository=repo, report_service=_StubReports())
    tenants = [await _create(service, f"user-{index}") for index in range(maximum)]

    archived = await service.archive_tenant(tenants[0].tenant_id)
    assert archived.status == "Archived"

    replacement = await _create(service, "user-replacement")
    active = await repo.list_active_tenants(limit=10)
    active_ids = [tenant.tenant_id for tenant in active]

    assert archived.tenant_id not in active_ids
    assert replacement.tenant_id in active_ids
    assert len(active_ids) == maximum


@pytest.mark.asyncio
async def test_failed_provisioning_releases_the_capacity_slot(repo):
    class _UnavailableRedis:
        async def set(self, *args, **kwargs):  # noqa: ANN002, ANN003, ANN202, ARG002
            raise ConnectionError("redis unavailable")

    maximum = get_settings().max_concurrent_simulations
    healthy = SimulationService(simulation_repository=repo)
    for index in range(maximum - 1):
        await _create(healthy, f"user-{index}")

    failing = SimulationService(simulation_repository=repo, redis_client=_UnavailableRedis())
    with pytest.raises(RuntimeError, match="namespace provisioning failed"):
        await _create(failing, "user-broken")

    # The slot is free again, and the stranded tenant is not advertised as active.
    recovered = await _create(healthy, "user-recovered")
    active_ids = [tenant.tenant_id for tenant in await repo.list_active_tenants(limit=10)]

    assert recovered.tenant_id in active_ids
    assert len(active_ids) == maximum
    assert await repo.count_active() == maximum


@pytest.mark.asyncio
async def test_cache_key_counter_tracks_namespace_provision_and_cleanup(repo):
    class _Redis:
        def __init__(self) -> None:
            self.keys: dict[str, str] = {}

        async def set(self, key, value, ex=None):  # noqa: ANN001, ANN202, ARG002
            self.keys[key] = value
            return True

        async def scan_iter(self, match):  # noqa: ANN001, ANN202
            prefix = match.rstrip("*")
            for key in list(self.keys):
                if key.startswith(prefix):
                    yield key

        async def delete(self, *keys):  # noqa: ANN002, ANN202
            for key in keys:
                self.keys.pop(key, None)
            return len(keys)

    redis = _Redis()
    service = SimulationService(
        simulation_repository=repo,
        redis_client=redis,
        report_service=_StubReports(),
    )

    tenant = await _create(service, "user-cache")
    assert tenant.resource_consumption.cache_keys == 1
    redis.keys[f"{tenant.tenant_id}:extra"] = "1"

    archived = await service.archive_tenant(tenant.tenant_id)

    assert archived.resource_consumption.cache_keys == 0
    assert archived.archive_cleanup.cache_keys_removed == 2
    assert redis.keys == {}


@pytest.mark.asyncio
async def test_signal_writes_stop_at_budget_plus_one(repo):
    service = SimulationService(simulation_repository=repo)
    tenant = await service.create_tenant(
        scenario_type="Flood",
        jurisdictions=["nsw"],
        participants=["user-budget"],
        creator_oid="user-budget",
        resource_limits={"max_signals": 3, "max_recommendations": 2, "max_duration_hours": 4},
    )
    governor = ResourceGovernor(repo)
    signals = SignalRepository(write_guard=governor).bind(tenant.tenant_id)

    for index in range(3):
        await signals.create_signal(tenant.tenant_id, {"signal_id": f"sig-{index}", "category": "flood"})

    with pytest.raises(PermissionError, match="budget"):
        await signals.create_signal(tenant.tenant_id, {"signal_id": "sig-overflow", "category": "flood"})

    persisted = await repo.get_by_tenant_id(tenant.tenant_id)
    assert persisted.resource_consumption.signal_count == 3
    assert persisted.resource_consumption.storage_bytes > 0
    assert await signals.count_by_tenant(tenant.tenant_id) == 3


@pytest.mark.asyncio
async def test_live_writes_are_not_charged_to_simulation_budgets(repo):
    governor = ResourceGovernor(repo)
    live = SignalRepository(write_guard=governor).bind("live")

    await live.create_signal("live", {"signal_id": "live-1", "category": "flood"})

    assert await live.count_by_tenant("live") == 1
    assert await repo.count_active() == 0


def test_api_ingestion_repositories_carry_the_shared_write_guard():
    from app.api.dependencies.simulation_composition import get_resource_governor
    from app.api.routes import incidents as incident_routes
    from app.api.routes import simulations as simulation_routes
    from app.services.ingestion.authoritative_ingestion import AuthoritativeIngestionService

    governor = get_resource_governor()
    assert simulation_routes._signal_repo._write_guard is governor
    assert incident_routes._signal_repository._write_guard is governor

    service = AuthoritativeIngestionService()
    assert service._signal_repository._write_guard is governor


def test_dead_count_then_create_validator_is_removed():
    from app.validators.simulation_validators import SimulationValidators

    assert not hasattr(SimulationValidators, "validate_concurrency_limit")
