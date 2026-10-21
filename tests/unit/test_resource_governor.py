import pytest
from app.repositories.incident_mode_repository import IncidentModeRepository
from app.repositories.simulation_repository import SimulationRepository
from app.services.resource_governor import ResourceGovernor, TokenBucket, UsageProvider

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
    @pytest.fixture(autouse=True)
    def _reset_incident_mode(self):
        IncidentModeRepository.reset_for_tests()

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
            scenario_type="Flood",
            created_by="user-001",
            participants=["user-001"],
            status="Active",
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
            scenario_type="Bushfire",
            created_by="user-001",
            participants=["user-001"],
            status="Active",
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

    @pytest.mark.asyncio
    async def test_signal_budget_is_reserved_and_released_atomically(self, governor, repo):
        from uuid import uuid4

        tenant_id = f"sim-{uuid4()}"
        tenant = SimulationTenant(
            tenant_id=tenant_id,
            scenario_id=str(uuid4()),
            scenario_run_id=str(uuid4()),
            scenario_type="Flood",
            created_by="user-001",
            participants=["user-001"],
            status="Active",
            resource_limits={"max_signals": 1, "max_recommendations": 1, "max_duration_hours": 1},
        )
        await repo.create(tenant)

        assert await repo.reserve_budget(tenant_id, "signal", 128) is True
        assert await repo.reserve_budget(tenant_id, "signal", 128) is False
        stored = await repo.get_by_tenant_id(tenant_id)
        assert stored.resource_consumption.signal_count == 1
        assert stored.resource_consumption.storage_bytes == 128

        await repo.release_budget(tenant_id, "signal", 128)
        assert await repo.reserve_budget(tenant_id, "signal", 64) is True
        stored = await repo.get_by_tenant_id(tenant_id)
        assert stored.resource_consumption.signal_count == 1
        assert stored.resource_consumption.storage_bytes == 64

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("percentage", "expected"),
        [(69.0, "normal"), (70.0, "throttled"), (71.0, "throttled")],
    )
    async def test_utilisation_thresholds(self, repo, percentage: float, expected: str):
        class _Usage(UsageProvider):
            async def read_percentages(self):  # noqa: ANN202
                return {"cosmos_ru": percentage, "llm_tokens": 20.0, "cache": 10.0}

        governor = ResourceGovernor(repo, usage_provider=_Usage())
        assert await governor.evaluate_utilisation() == expected

    @pytest.mark.asyncio
    async def test_missing_usage_telemetry_fails_safe_to_throttled(self, repo):
        class _Missing(UsageProvider):
            async def read_percentages(self):  # noqa: ANN202
                return None

        governor = ResourceGovernor(repo, usage_provider=_Missing())
        assert await governor.evaluate_utilisation() == "throttled"

    @pytest.mark.asyncio
    async def test_durable_incident_mode_is_visible_to_fresh_governor_and_new_tenant(self, repo):
        mode = IncidentModeRepository()
        first = ResourceGovernor(repo, incident_mode_repository=mode)
        await first.declare_incident("admin-1")

        fresh = ResourceGovernor(repo, incident_mode_repository=IncidentModeRepository())
        assert await fresh.incident_mode_active() is True

        from app.services.simulation_service import SimulationService

        service = SimulationService(repo, resource_governor=fresh)
        tenant = await service.create_tenant(
            scenario_type="Flood",
            jurisdictions=["nsw"],
            participants=["user-1"],
            creator_oid="user-1",
        )
        assert tenant.throttle_mode == "incident-throttled"
        assert tenant.throttle_quota_pct == 20
        assert "Live incident active" in tenant.throttle_notice

    @pytest.mark.asyncio
    async def test_incident_mode_persistence_failure_does_not_change_tenant(self, repo):
        class _FailingMode:
            async def transition(self, **kwargs):  # noqa: ANN003, ANN202, ARG002
                raise RuntimeError("governance unavailable")

            async def get(self):  # noqa: ANN202
                return {"active": False}

        tenant = SimulationTenant(
            tenant_id="sim-12345678-1234-1234-1234-123456789012",
            scenario_id="12345678-1234-1234-1234-123456789012",
            scenario_run_id="12345678-1234-1234-1234-123456789012",
            scenario_type="Flood",
            created_by="user-1",
            participants=["user-1"],
            status="Active",
        )
        await repo.create(tenant)
        governor = ResourceGovernor(repo, incident_mode_repository=_FailingMode())

        with pytest.raises(RuntimeError, match="governance unavailable"):
            await governor.declare_incident("admin-1")

        unchanged = await repo.get_by_tenant_id(tenant.tenant_id)
        assert unchanged.throttle_mode == "normal"
