import pytest
from uuid import uuid4

from app.repositories.simulation_repository import SimulationRepository
from app.services.simulation_service import SimulationService

from packages.domain.src.domain.models.simulation_tenant import SimulationTenant


@pytest.fixture
def repo():
    return SimulationRepository()


@pytest.fixture
def service(repo):
    return SimulationService(simulation_repository=repo)


class TestSimulationLifecycle:
    """Full lifecycle: create → seed → operate → archive → delete."""

    @pytest.mark.asyncio
    async def test_full_lifecycle(self, service, repo):
        tenant = await service.create_tenant(
            scenario_type="bushfire",
            jurisdictions=["nsw-sw"],
            participants=["user-001"],
            creator_oid="user-001",
        )
        assert tenant.status == "active"

        tenant = tenant.transition_to("paused")
        tenant = await repo.update(tenant)
        assert tenant.status == "paused"

        tenant = tenant.transition_to("active")
        tenant = await repo.update(tenant)
        assert tenant.status == "active"

        tenant = tenant.transition_to("archiving")
        tenant = await repo.update(tenant)
        assert tenant.status == "archiving"

        tenant = tenant.transition_to("archived")
        tenant = await repo.update(tenant)
        assert tenant.status == "archived"

        tenant = tenant.transition_to("deleted")
        tenant = await repo.update(tenant)
        assert tenant.status == "deleted"

    @pytest.mark.asyncio
    async def test_invalid_transition_raises(self, service, repo):
        tenant = await service.create_tenant(
            scenario_type="flood",
            jurisdictions=[],
            participants=["user-001"],
            creator_oid="user-001",
        )
        assert tenant.status == "active"

        with pytest.raises(ValueError, match="Cannot transition"):
            tenant.transition_to("deleted")
