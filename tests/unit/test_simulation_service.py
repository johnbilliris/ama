import asyncio
from datetime import UTC, datetime, timedelta

import pytest
from app.repositories.simulation_repository import SimulationRepository
from app.services.simulation_audit_writer import SimulationAuditWriter
from app.services.simulation_service import SimulationService


@pytest.fixture
def repo():
    return SimulationRepository()


@pytest.fixture
def service(repo):
    return SimulationService(simulation_repository=repo)


class TestSimulationService:
    @pytest.mark.asyncio
    async def test_create_tenant_success(self, service, repo):
        tenant = await service.create_tenant(
            scenario_type="Bushfire",
            jurisdictions=["nsw-sw"],
            participants=["user-001"],
            creator_oid="user-001",
        )
        assert tenant.tenant_id.startswith("sim-")
        assert tenant.tenant_id == f"sim-{tenant.scenario_run_id}"
        assert tenant.scenario_id == tenant.scenario_run_id
        assert tenant.status == "Active"
        assert "user-001" in tenant.participants
        run = await repo.get_document(document_type="scenario_run", document_id=tenant.scenario_run_id)
        assert run is not None
        assert run["tenant_id"] == tenant.tenant_id

    @pytest.mark.asyncio
    async def test_failed_namespace_provisioning_never_reports_active(self, repo):
        class _UnavailableRedis:
            async def set(self, *args, **kwargs):  # noqa: ANN002, ANN003, ANN202, ARG002
                raise ConnectionError("redis unavailable")

        service = SimulationService(simulation_repository=repo, redis_client=_UnavailableRedis())

        with pytest.raises(RuntimeError, match="namespace provisioning failed"):
            await service.create_tenant(
                scenario_type="Flood",
                jurisdictions=["nsw"],
                participants=["user-001"],
                creator_oid="user-001",
            )

        tenants, total = await repo.list_by_status()
        assert total == 1
        assert tenants[0].status == "Provisioning"

    def test_simulation_repository_requires_cosmos_in_production(self, monkeypatch):
        monkeypatch.setenv("AMA_ENVIRONMENT", "production")
        monkeypatch.delenv("COSMOS_ENDPOINT", raising=False)

        with pytest.raises(RuntimeError, match="requires COSMOS_ENDPOINT"):
            SimulationRepository()

    @pytest.mark.asyncio
    async def test_create_tenant_validates_scenario_type(self, service):
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            await service.create_tenant(
                scenario_type="earthquake",
                jurisdictions=[],
                participants=["user-001"],
                creator_oid="user-001",
            )
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_create_tenant_validates_participants(self, service):
        from fastapi import HTTPException

        with pytest.raises(HTTPException):
            await service.create_tenant(
                scenario_type="Flood",
                jurisdictions=[],
                participants=[],
                creator_oid="user-001",
            )

    @pytest.mark.asyncio
    async def test_concurrency_limit(self, service, repo):
        from fastapi import HTTPException

        for i in range(3):
            await service.create_tenant(
                scenario_type="Flood",
                jurisdictions=[],
                participants=[f"user-{i}"],
                creator_oid=f"user-{i}",
            )

        with pytest.raises(HTTPException) as exc_info:
            await service.create_tenant(
                scenario_type="Flood",
                jurisdictions=[],
                participants=["user-x"],
                creator_oid="user-x",
            )
        assert exc_info.value.status_code == 409

    @pytest.mark.asyncio
    async def test_concurrent_creation_reserves_only_configured_capacity(self, service):
        async def create(index: int):
            try:
                return await service.create_tenant(
                    scenario_type="Flood",
                    jurisdictions=[],
                    participants=[f"user-{index}"],
                    creator_oid=f"user-{index}",
                )
            except Exception as exc:  # noqa: BLE001
                return exc

        results = await asyncio.gather(*(create(index) for index in range(4)))

        successes = [result for result in results if not isinstance(result, Exception)]
        conflicts = [result for result in results if getattr(result, "status_code", None) == 409]
        assert len(successes) == 3
        assert len(conflicts) == 1
        assert len(conflicts[0].detail["activeSimulationIds"]) == 3

    @pytest.mark.asyncio
    async def test_get_tenant(self, service):
        tenant = await service.create_tenant(
            scenario_type="Cyclone",
            jurisdictions=["qld-fnq"],
            participants=["user-001"],
            creator_oid="user-001",
        )
        retrieved = await service.get_tenant(tenant.tenant_id)
        assert retrieved is not None
        assert retrieved.tenant_id == tenant.tenant_id

    @pytest.mark.asyncio
    async def test_list_tenants(self, service):
        await service.create_tenant(
            scenario_type="Bushfire",
            jurisdictions=[],
            participants=["user-001"],
            creator_oid="user-001",
        )
        tenants, total = await service.list_tenants()
        assert total >= 1
        assert len(tenants) >= 1

    @pytest.mark.asyncio
    async def test_list_tenants_filters_results_and_total_by_participant(self, service):
        owned = await service.create_tenant(
            scenario_type="Bushfire",
            jurisdictions=[],
            participants=["user-owned"],
            creator_oid="user-owned",
        )
        await service.create_tenant(
            scenario_type="Flood",
            jurisdictions=[],
            participants=["user-other"],
            creator_oid="user-other",
        )

        tenants, total = await service.list_tenants(participant_oid="user-owned")

        assert total == 1
        assert [tenant.tenant_id for tenant in tenants] == [owned.tenant_id]

    @pytest.mark.asyncio
    async def test_lifecycle_transitions(self, service, repo):
        tenant = await service.create_tenant(
            scenario_type="Bushfire",
            jurisdictions=[],
            participants=["user-001"],
            creator_oid="user-001",
        )
        assert tenant.status == "Active"
        assert tenant.elapsed_seconds == 0.0

        tenant = tenant.transition_to("Paused", elapsed_seconds=45.0)
        tenant = await repo.update(tenant)
        assert tenant.status == "Paused"
        assert tenant.elapsed_seconds == 45.0

        tenant = tenant.transition_to("Active", elapsed_seconds=45.0)
        tenant = await repo.update(tenant)
        assert tenant.status == "Active"
        assert tenant.elapsed_seconds == 45.0

    @pytest.mark.asyncio
    async def test_expiry_notice_is_once_and_activity_extends_idle_ttl(self, repo):
        audit = SimulationAuditWriter()
        service = SimulationService(simulation_repository=repo, audit_writer=audit)
        tenant = await service.create_tenant(
            scenario_type="Flood",
            jurisdictions=["nsw"],
            participants=["user-001"],
            creator_oid="user-001",
        )
        now = datetime.now(UTC)
        tenant = await repo.update(
            tenant.model_copy(
                update={
                    "last_activity_at": now - timedelta(hours=49),
                    "expires_at": now + timedelta(hours=23),
                    "expiry_notice_sent_at": None,
                }
            )
        )

        first = await service.run_expiry_tick(now)
        second = await service.run_expiry_tick(now + timedelta(minutes=1))

        assert first["notified"] == [tenant.tenant_id]
        assert second["notified"] == []
        touched = await repo.touch_activity(tenant.tenant_id, now + timedelta(hours=1))
        assert touched.expiry_notice_sent_at is None
        assert touched.expires_at == now + timedelta(hours=1 + tenant.ttl_hours)

    @pytest.mark.asyncio
    async def test_expiry_claim_allows_only_current_lease_owner(self, repo):
        service = SimulationService(simulation_repository=repo)
        tenant = await service.create_tenant(
            scenario_type="Flood",
            jurisdictions=["nsw"],
            participants=["user-001"],
            creator_oid="user-001",
        )
        now = datetime.now(UTC)

        assert await repo.claim_expiry(tenant.tenant_id, "worker-a", now) is True
        assert await repo.claim_expiry(tenant.tenant_id, "worker-b", now + timedelta(seconds=1)) is False
        assert await repo.claim_expiry(tenant.tenant_id, "worker-a", now + timedelta(seconds=1)) is True
