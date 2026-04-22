
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
        assert tenant.last_resumed_at is not None
        assert tenant.elapsed_seconds == 0.0

        tenant = tenant.transition_to("Paused")
        tenant = await repo.update(tenant)
        assert tenant.status == "Paused"
        assert tenant.elapsed_seconds >= 0.0
        assert tenant.last_resumed_at is None
        assert tenant.paused_at is not None

        tenant = tenant.transition_to("Active")
        tenant = await repo.update(tenant)
        assert tenant.status == "Active"
        assert tenant.last_resumed_at is not None
        assert tenant.paused_at is None

        tenant = tenant.transition_to("Archiving")
        tenant = await repo.update(tenant)
        assert tenant.status == "Archiving"
        assert tenant.last_resumed_at is None

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

    @pytest.mark.asyncio
    async def test_elapsed_accumulates_across_pause_resume(self, service, repo):
        """Elapsed time accumulates only while Active, not while Paused."""
        from datetime import UTC, datetime, timedelta

        tenant = await service.create_tenant(
            scenario_type="Flood",
            jurisdictions=[],
            participants=["user-001"],
            creator_oid="user-001",
        )
        assert tenant.elapsed_seconds == 0.0

        # Simulate 60 seconds of active time then pause
        t1 = datetime.now(UTC)
        t2 = t1 + timedelta(seconds=60)
        tenant = tenant.model_copy(update={"last_resumed_at": t1})
        tenant = tenant.transition_to("Paused", now=t2)
        assert tenant.elapsed_seconds == pytest.approx(60.0, abs=0.1)

        # Simulate 120 seconds of pause (should not accumulate)
        t3 = t2 + timedelta(seconds=120)
        tenant = tenant.transition_to("Active", now=t3)
        assert tenant.elapsed_seconds == pytest.approx(60.0, abs=0.1)

        # Simulate 30 more seconds of active time then archive
        t4 = t3 + timedelta(seconds=30)
        tenant = tenant.transition_to("Archiving", now=t4)
        assert tenant.elapsed_seconds == pytest.approx(90.0, abs=0.1)
        assert tenant.last_resumed_at is None
