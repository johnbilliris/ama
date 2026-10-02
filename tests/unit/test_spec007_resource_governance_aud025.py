"""AUD-025 — live-first resource governance over real utilisation and every write path."""

from __future__ import annotations

import asyncio
from uuid import uuid4

import pytest
from app.repositories.incident_mode_repository import IncidentModeRepository
from app.repositories.signal_repository import SignalRepository
from app.repositories.simulation_repository import SimulationRepository
from app.services.resource_governor import (
    USAGE_OK,
    USAGE_UNAVAILABLE,
    USAGE_UNCONFIGURED,
    ProcessReservationStore,
    RedisReservationStore,
    ResourceGovernor,
    build_usage_provider,
)

from packages.domain.src.domain.models.simulation_tenant import SimulationTenant

pytestmark = pytest.mark.spec007_isolation

USAGE_ENV_VARS = ("AMA_USAGE_COSMOS_RU_PCT", "AMA_USAGE_LLM_TOKEN_PCT", "AMA_USAGE_COMPUTE_PCT", "AMA_USAGE_PROVIDERS")


class _Clock:
    def __init__(self) -> None:
        self.value = 0.0

    def __call__(self) -> float:
        return self.value

    def advance(self, seconds: float) -> None:
        self.value += seconds


class _Redis:
    def __init__(self, used: int = 0, maximum: int = 0, fail: bool = False) -> None:
        self._used = used
        self._maximum = maximum
        self._fail = fail

    async def info(self, _section: str) -> dict[str, int]:
        if self._fail:
            raise ConnectionError("cache telemetry unreachable")
        return {"used_memory": self._used, "maxmemory": self._maximum}


class _WriteSpy:
    """Records every guarded write attempt and its admission decision."""

    def __init__(self, governor: ResourceGovernor) -> None:
        self._governor = governor
        self.attempts: list[str] = []
        self.admitted: list[str] = []

    async def reserve_write(self, tenant_id: str, kind: str, storage_bytes: int = 0) -> bool:
        self.attempts.append(tenant_id)
        allowed = await self._governor.reserve_write(tenant_id, kind, storage_bytes)
        if allowed:
            self.admitted.append(tenant_id)
        return allowed

    async def release_write(self, tenant_id: str, kind: str, storage_bytes: int = 0) -> None:
        await self._governor.release_write(tenant_id, kind, storage_bytes)


@pytest.fixture(autouse=True)
def _clean_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    IncidentModeRepository.reset_for_tests()
    ProcessReservationStore.reset_for_tests()
    monkeypatch.delenv("COSMOS_ENDPOINT", raising=False)
    for name in USAGE_ENV_VARS:
        monkeypatch.delenv(name, raising=False)


@pytest.fixture
def repo() -> SimulationRepository:
    return SimulationRepository()


async def _tenant(repo: SimulationRepository, *, max_signals: int = 50) -> SimulationTenant:
    tenant = SimulationTenant(
        tenant_id=f"sim-{uuid4()}",
        scenario_id=str(uuid4()),
        scenario_run_id=str(uuid4()),
        scenario_type="Flood",
        created_by="user-1",
        participants=["user-1"],
        status="Active",
        resource_limits={"max_signals": max_signals, "max_recommendations": 20, "max_duration_hours": 4},
    )
    return await repo.create(tenant)


# ── Usage composition: unconfigured must not throttle every deployment ──


@pytest.mark.asyncio
async def test_unconfigured_telemetry_is_distinct_from_unavailable(repo):
    provider = build_usage_provider(None)
    reading = await provider.read_usage()

    assert reading.status == USAGE_UNCONFIGURED
    assert await ResourceGovernor(repo, usage_provider=provider).evaluate_utilisation() == "normal"


@pytest.mark.asyncio
async def test_configured_but_unreadable_telemetry_fails_safe_to_throttled(repo):
    provider = build_usage_provider(_Redis(used=10, maximum=100, fail=True))
    reading = await provider.read_usage()

    assert reading.status == USAGE_UNAVAILABLE
    assert await ResourceGovernor(repo, usage_provider=provider).evaluate_utilisation() == "throttled"


@pytest.mark.asyncio
async def test_composite_merges_cosmos_llm_and_cache_telemetry(repo, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("AMA_USAGE_COSMOS_RU_PCT", "55")
    monkeypatch.setenv("AMA_USAGE_LLM_TOKEN_PCT", "82")
    monkeypatch.setenv("AMA_USAGE_COMPUTE_PCT", "12")
    provider = build_usage_provider(_Redis(used=30, maximum=100))

    reading = await provider.read_usage()

    assert reading.status == USAGE_OK
    assert reading.values == {"cosmos_ru": 55.0, "llm_tokens": 82.0, "compute": 12.0, "cache": 30.0}
    assert reading.maximum == 82.0
    assert await ResourceGovernor(repo, usage_provider=provider).evaluate_utilisation() == "throttled"


@pytest.mark.asyncio
async def test_unparseable_configured_gauge_is_unavailable(repo, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("AMA_USAGE_PROVIDERS", "cosmos_ru")
    monkeypatch.setenv("AMA_USAGE_COSMOS_RU_PCT", "not-a-number")

    reading = await build_usage_provider(None).read_usage()

    assert reading.status == USAGE_UNAVAILABLE


@pytest.mark.asyncio
async def test_unbounded_cache_is_unconfigured_not_an_outage(repo):
    reading = await build_usage_provider(_Redis(used=10, maximum=0)).read_usage()

    assert reading.status == USAGE_UNCONFIGURED


# ── Shared reservations ──


@pytest.mark.asyncio
async def test_independent_governors_share_throttle_reservations(repo):
    tenant = await _tenant(repo, max_signals=4)
    clock = _Clock()
    first = ResourceGovernor(repo, reservation_store=ProcessReservationStore(clock=clock))
    second = ResourceGovernor(repo, reservation_store=ProcessReservationStore(clock=clock))

    decisions = [
        await first.check_write_allowed(tenant.tenant_id),
        await second.check_write_allowed(tenant.tenant_id),
        await first.check_write_allowed(tenant.tenant_id),
        await second.check_write_allowed(tenant.tenant_id),
        await second.check_write_allowed(tenant.tenant_id),
    ]

    assert decisions == [True, True, True, True, False]


@pytest.mark.asyncio
async def test_redis_reservation_store_shares_state_across_replicas(repo):
    class _SharedRedis:
        def __init__(self) -> None:
            self.values: dict[str, int] = {}

        async def incrby(self, key: str, amount: int) -> int:
            self.values[key] = self.values.get(key, 0) + amount
            return self.values[key]

        async def expire(self, key: str, seconds: int) -> bool:  # noqa: ARG002
            return True

        async def get(self, key: str) -> int | None:
            return self.values.get(key)

    tenant = await _tenant(repo, max_signals=4)
    shared = _SharedRedis()
    replica_a = ResourceGovernor(repo, reservation_store=RedisReservationStore(shared))
    replica_b = ResourceGovernor(repo, reservation_store=RedisReservationStore(shared))

    assert await replica_a.check_write_allowed(tenant.tenant_id) is True
    assert await replica_b.check_write_allowed(tenant.tenant_id) is True
    assert len(shared.values) == 1, "replicas must contend for one shared reservation key"


@pytest.mark.asyncio
async def test_mode_transition_preserves_token_state_without_refill(repo):
    tenant = await _tenant(repo, max_signals=100)
    clock = _Clock()
    governor = ResourceGovernor(repo, reservation_store=ProcessReservationStore(clock=clock))

    for _ in range(98):
        assert await governor.check_write_allowed(tenant.tenant_id) is True

    await repo.update(tenant.model_copy(update={"throttle_mode": "throttled"}))

    # Capacity halves to 50 but the two remaining tokens are not refilled to full.
    assert await governor.check_write_allowed(tenant.tenant_id) is True
    assert await governor.check_write_allowed(tenant.tenant_id) is False


@pytest.mark.asyncio
async def test_tokens_refill_over_time_after_transition(repo):
    tenant = await _tenant(repo, max_signals=60)
    clock = _Clock()
    governor = ResourceGovernor(repo, reservation_store=ProcessReservationStore(clock=clock))

    for _ in range(60):
        await governor.check_write_allowed(tenant.tenant_id)
    assert await governor.check_write_allowed(tenant.tenant_id) is False

    clock.advance(10.0)
    assert await governor.check_write_allowed(tenant.tenant_id) is True


# ── Live priority ──


@pytest.mark.asyncio
async def test_live_reservations_make_simulations_yield_and_live_always_writes(repo):
    tenant = await _tenant(repo, max_signals=100)
    clock = _Clock()
    governor = ResourceGovernor(
        repo,
        reservation_store=ProcessReservationStore(clock=clock),
        shared_capacity=10,
    )

    assert await governor.check_write_allowed(tenant.tenant_id) is True

    await governor.reserve_live_capacity(10)
    assert await governor.live_reserved_capacity() == 10
    assert await governor.check_write_allowed(tenant.tenant_id) is False
    assert await governor.check_write_allowed("live") is True

    await governor.release_live_capacity(10)
    assert await governor.check_write_allowed(tenant.tenant_id) is True


@pytest.mark.asyncio
async def test_mixed_live_and_simulation_queue_admits_live_while_simulation_is_exhausted(repo):
    tenant = await _tenant(repo, max_signals=2)
    clock = _Clock()
    governor = ResourceGovernor(repo, reservation_store=ProcessReservationStore(clock=clock))
    signals = SignalRepository(write_guard=governor)
    simulation_writer = signals.bind(tenant.tenant_id)
    live_writer = signals.bind("live")

    admitted = 0
    for index in range(4):
        await live_writer.create_signal("live", {"signal_id": f"live-{index}", "category": "flood"})
        try:
            await simulation_writer.create_signal(tenant.tenant_id, {"signal_id": f"sim-{index}", "category": "flood"})
        except PermissionError:
            continue
        admitted += 1

    assert admitted == 2
    assert await live_writer.count_by_tenant("live") == 4
    assert await simulation_writer.count_by_tenant(tenant.tenant_id) == 2


# ── Incident during seed ──


@pytest.mark.asyncio
async def test_incident_declared_during_seed_throttles_simulation_writes_only(repo):
    tenant = await _tenant(repo, max_signals=50)
    clock = _Clock()
    governor = ResourceGovernor(repo, reservation_store=ProcessReservationStore(clock=clock))
    spy = _WriteSpy(governor)
    signals = SignalRepository(write_guard=spy)
    seeding = signals.bind(tenant.tenant_id)
    live_writer = signals.bind("live")

    for index in range(3):
        await seeding.create_signal(tenant.tenant_id, {"signal_id": f"seed-{index}", "category": "flood"})

    declaration = await governor.declare_incident_with_status("admin-1")
    assert declaration["status"] == "incident_declared"
    throttled = await repo.get_by_tenant_id(tenant.tenant_id)
    assert throttled.throttle_mode == "incident-throttled"
    assert throttled.throttle_quota_pct == 20
    assert "Live incident active" in throttled.throttle_notice

    blocked = 0
    for index in range(6):
        try:
            await seeding.create_signal(tenant.tenant_id, {"signal_id": f"post-{index}", "category": "flood"})
        except PermissionError:
            blocked += 1

    await live_writer.create_signal("live", {"signal_id": "live-during-incident", "category": "flood"})

    assert blocked > 0, "incident mode must stop simulation seed writes"
    assert len(spy.admitted) < len(spy.attempts)
    assert await live_writer.count_by_tenant("live") == 1
    assert await seeding.count_by_tenant(tenant.tenant_id) == len(spy.admitted)


@pytest.mark.asyncio
async def test_concurrent_seed_writes_never_exceed_the_shared_bucket(repo):
    tenant = await _tenant(repo, max_signals=6)
    clock = _Clock()
    governor = ResourceGovernor(repo, reservation_store=ProcessReservationStore(clock=clock))

    results = await asyncio.gather(*(governor.check_write_allowed(tenant.tenant_id) for _ in range(12)))

    assert sum(1 for allowed in results if allowed) == 6
