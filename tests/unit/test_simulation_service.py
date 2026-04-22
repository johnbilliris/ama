import pytest
from app.repositories.simulation_repository import SimulationRepository
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
        assert tenant.status == "Active"
        assert "user-001" in tenant.participants

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
