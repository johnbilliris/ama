
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
        assert tenant.elapsed_seconds == 0.0

        # UI reports 60s elapsed when pausing
        tenant = tenant.transition_to("Paused", elapsed_seconds=60.0)
        tenant = await repo.update(tenant)
        assert tenant.status == "Paused"
        assert tenant.elapsed_seconds == 60.0

        # UI reports same 60s when resuming (timer was frozen)
        tenant = tenant.transition_to("Active", elapsed_seconds=60.0)
        tenant = await repo.update(tenant)
        assert tenant.status == "Active"
        assert tenant.elapsed_seconds == 60.0

        # UI reports 90s when archiving
        tenant = tenant.transition_to("Archiving", elapsed_seconds=90.0)
        tenant = await repo.update(tenant)
        assert tenant.status == "Archiving"
        assert tenant.elapsed_seconds == 90.0

        tenant = tenant.transition_to("Archived")
        tenant = await repo.update(tenant)
        assert tenant.status == "Archived"
        assert tenant.elapsed_seconds == 90.0

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

    @pytest.mark.asyncio
    async def test_elapsed_preserved_across_pause_resume(self, service, repo):
        """Elapsed seconds sent by the UI are preserved through transitions."""
        tenant = await service.create_tenant(
            scenario_type="Flood",
            jurisdictions=[],
            participants=["user-001"],
            creator_oid="user-001",
        )
        assert tenant.elapsed_seconds == 0.0

        # Pause with 120s elapsed
        tenant = tenant.transition_to("Paused", elapsed_seconds=120.0)
        assert tenant.elapsed_seconds == 120.0

        # Resume — elapsed stays at 120s (timer was paused)
        tenant = tenant.transition_to("Active", elapsed_seconds=120.0)
        assert tenant.elapsed_seconds == 120.0

        # Pause again with 180s elapsed
        tenant = tenant.transition_to("Paused", elapsed_seconds=180.0)
        assert tenant.elapsed_seconds == 180.0

        # Archive from paused with same value
        tenant = tenant.transition_to("Archiving", elapsed_seconds=180.0)
        assert tenant.elapsed_seconds == 180.0

    @pytest.mark.asyncio
    async def test_transition_without_elapsed_keeps_existing(self, service, repo):
        """Transitions that don't supply elapsed_seconds preserve the stored value."""
        tenant = await service.create_tenant(
            scenario_type="Cyclone",
            jurisdictions=[],
            participants=["user-001"],
            creator_oid="user-001",
        )
        tenant = tenant.transition_to("Paused", elapsed_seconds=50.0)
        assert tenant.elapsed_seconds == 50.0

        # Resume without explicit elapsed_seconds — should keep 50.0
        tenant = tenant.transition_to("Active")
        assert tenant.elapsed_seconds == 50.0
