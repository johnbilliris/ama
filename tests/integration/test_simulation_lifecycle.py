
import pytest
from app.repositories.simulation_repository import SimulationRepository
from app.services.simulation_service import SimulationService


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
            scenario_type="Bushfire",
            jurisdictions=["nsw-sw"],
            participants=["user-001"],
            creator_oid="user-001",
        )
        assert tenant.status == "Active"

        tenant = tenant.transition_to("Paused")
        tenant = await repo.update(tenant)
        assert tenant.status == "Paused"

        tenant = tenant.transition_to("Active")
        tenant = await repo.update(tenant)
        assert tenant.status == "Active"

        tenant = tenant.transition_to("Archiving")
        tenant = await repo.update(tenant)
        assert tenant.status == "Archiving"

        tenant = tenant.transition_to("Archived")
        tenant = await repo.update(tenant)
        assert tenant.status == "Archived"

        tenant = tenant.transition_to("Deleted")
        tenant = await repo.update(tenant)
        assert tenant.status == "Deleted"

    @pytest.mark.asyncio
    async def test_invalid_transition_raises(self, service, repo):
        tenant = await service.create_tenant(
            scenario_type="Flood",
            jurisdictions=[],
            participants=["user-001"],
            creator_oid="user-001",
        )
        assert tenant.status == "Active"

        with pytest.raises(ValueError, match="Cannot transition"):
            tenant.transition_to("Deleted")
