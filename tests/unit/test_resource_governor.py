import pytest
from app.repositories.simulation_repository import SimulationRepository
from app.services.resource_governor import ResourceGovernor, TokenBucket

from packages.domain.src.domain.models.simulation_tenant import SimulationTenant


class TestTokenBucket:
    def test_consume_success(self):
        bucket = TokenBucket(rate=10.0, capacity=10)
        assert bucket.consume(1) is True

    def test_consume_exhaustion(self):
        bucket = TokenBucket(rate=0.0, capacity=2)
        assert bucket.consume(1) is True
        assert bucket.consume(1) is True
        assert bucket.consume(1) is False


class TestResourceGovernor:
    @pytest.fixture
    def repo(self):
        return SimulationRepository()

    @pytest.fixture
    def governor(self, repo):
        return ResourceGovernor(simulation_repository=repo)

    @pytest.mark.asyncio
    async def test_live_writes_always_allowed(self, governor):
        assert await governor.check_write_allowed("live") is True

    @pytest.mark.asyncio
    async def test_declare_incident_throttles(self, governor, repo):
        from uuid import uuid4

        tenant_id = f"sim-{uuid4()}"
        tenant = SimulationTenant(
            tenant_id=tenant_id,
            scenario_id=str(uuid4()),
            scenario_run_id=str(uuid4()),
            scenario_type="flood",
            created_by="user-001",
            participants=["user-001"],
            status="active",
        )
        await repo.create(tenant)

        affected = await governor.declare_incident()
        assert affected >= 1

        updated = await repo.get_by_tenant_id(tenant_id)
        assert updated is not None
        assert updated.throttle_mode == "incident-throttled"
        assert updated.throttle_quota_pct == 20

    @pytest.mark.asyncio
    async def test_resolve_incident_restores(self, governor, repo):
        from uuid import uuid4

        tenant_id = f"sim-{uuid4()}"
        tenant = SimulationTenant(
            tenant_id=tenant_id,
            scenario_id=str(uuid4()),
            scenario_run_id=str(uuid4()),
            scenario_type="bushfire",
            created_by="user-001",
            participants=["user-001"],
            status="active",
            throttle_mode="incident-throttled",
            throttle_quota_pct=20,
        )
        await repo.create(tenant)

        restored = await governor.resolve_incident()
        assert restored >= 1

        updated = await repo.get_by_tenant_id(tenant_id)
        assert updated is not None
        assert updated.throttle_mode == "normal"
        assert updated.throttle_quota_pct == 100
