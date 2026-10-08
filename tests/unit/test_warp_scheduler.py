"""Unit tests for :class:`WarpScheduler` (feature 026)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from app.repositories.signal_repository import SignalRepository
from app.repositories.simulation_event_repository import SimulationEventRepository
from app.repositories.simulation_repository import SimulationRepository
from app.services.simulation_clock_service import SimulationClockService
from app.services.simulation_event_recorder import SimulationEventRecorder
from app.services.warp_scheduler import WarpScheduler

from packages.domain.src.domain.models.simulation_tenant import SimulationTenant


class _FakeClock:
    def __init__(self) -> None:
        self.now = datetime(2026, 4, 22, 12, 0, 0, tzinfo=UTC)

    def advance(self, seconds: float) -> None:
        self.now += timedelta(seconds=seconds)

    def __call__(self) -> datetime:
        return self.now


@pytest.fixture
def wiring():
    fake_clock = _FakeClock()
    sim_repo = SimulationRepository()
    sig_repo = SignalRepository()
    evt_repo = SimulationEventRepository()
    clock = SimulationClockService(now_provider=fake_clock)
    recorder = SimulationEventRecorder(evt_repo)
    scheduler = WarpScheduler(
        signal_repository=sig_repo,
        event_repository=evt_repo,
        simulation_repository=sim_repo,
        clock_service=clock,
        event_recorder=recorder,
    )
    return fake_clock, sim_repo, sig_repo, evt_repo, clock, recorder, scheduler


def _tenant(warp: float, sim_repo, clock) -> SimulationTenant:
    tenant = SimulationTenant(
        tenant_id="sim-" + "a" * 36,
        scenario_id="s",
        scenario_run_id="r",
        scenario_type="Bushfire",
        created_by="u",
        participants=["u"],
    )
    tenant = clock.start_clock(tenant, warp_speed=warp)
    return tenant


def _timeline(*offsets: float) -> list[dict]:
    return [
        {
            "offset_seconds": off,
            "signal_envelope": {
                "signal_id": f"sig-{i}",
                "data_source_id": "ds-1",
                "category": "bushfire",
            },
        }
        for i, off in enumerate(offsets)
    ]


@pytest.mark.asyncio
async def test_initialize_creates_scheduler_state(wiring):
    _, sim_repo, _, evt_repo, clock, _, scheduler = wiring
    tenant = _tenant(10, sim_repo, clock)
    await sim_repo.create(tenant)
    scheduler.initialize(tenant.tenant_id, _timeline(0, 60, 600), warp_speed=10)
    state = evt_repo.get_scheduler_state(tenant.tenant_id)
    assert state is not None
    assert state.next_signal_index == 0
    assert state.scheduler_owner is not None

    @pytest.mark.asyncio
    async def test_initialize_persists_timeline_for_restart(wiring):
        _, sim_repo, sig_repo, evt_repo, clock, recorder, scheduler = wiring
        tenant = _tenant(10, sim_repo, clock)
        await sim_repo.create(tenant)
        timeline = _timeline(60, 120)
        scheduler.initialize(tenant.tenant_id, timeline, warp_speed=10)

        restarted = WarpScheduler(
            signal_repository=sig_repo,
            event_repository=evt_repo,
            simulation_repository=sim_repo,
            clock_service=clock,
            event_recorder=recorder,
        )

        assert restarted.start_delivery_loop(tenant.tenant_id) is True
        assert restarted.start_delivery_loop(tenant.tenant_id) is False
        await restarted.stop_delivery_loop(tenant.tenant_id)


@pytest.mark.asyncio
async def test_next_delivery_delay_respects_warp(wiring):
    _, sim_repo, _, _, clock, _, scheduler = wiring
    tenant = _tenant(10, sim_repo, clock)
    await sim_repo.create(tenant)
    state = scheduler.initialize(tenant.tenant_id, _timeline(0, 60, 600), warp_speed=10)
    # First signal at offset 0, current_sim_seconds==0 → delay 0
    assert scheduler.next_delivery_delay(tenant, state) == 0.0
    # Simulate delivery cursor advance to index 1 (offset=60 sim-sec at 10× = 6 wall-sec)
    state2 = state.model_copy(update={"next_signal_index": 1})
    assert scheduler.next_delivery_delay(tenant, state2) == pytest.approx(6.0)


@pytest.mark.asyncio
async def test_deliver_next_signal_advances_cursor_and_records(wiring):
    fake_clock, sim_repo, sig_repo, evt_repo, clock, _, scheduler = wiring
    tenant = _tenant(10, sim_repo, clock)
    await sim_repo.create(tenant)
    scheduler.initialize(tenant.tenant_id, _timeline(0, 60), warp_speed=10)

    delivered = await scheduler.deliver_next_signal(tenant.tenant_id)
    assert delivered is True
    state = evt_repo.get_scheduler_state(tenant.tenant_id)
    assert state.next_signal_index == 1
    # Event recorded
    events = evt_repo.list_events(tenant.tenant_id)
    assert len(events) == 1 and events[0].event_type == "signal_delivered"

    # Second signal not yet due at current sim time
    delivered = await scheduler.deliver_next_signal(tenant.tenant_id)
    assert delivered is False

    # Advance wall clock 6 seconds → 60 sim seconds at 10× → second signal due
    fake_clock.advance(6)
    delivered = await scheduler.deliver_next_signal(tenant.tenant_id)
    assert delivered is True


@pytest.mark.asyncio
async def test_paused_tenant_does_not_deliver(wiring):
    _, sim_repo, _, _, clock, _, scheduler = wiring
    tenant = _tenant(10, sim_repo, clock)
    tenant = clock.pause_clock(tenant)
    await sim_repo.create(tenant)
    scheduler.initialize(tenant.tenant_id, _timeline(0), warp_speed=10)
    assert await scheduler.deliver_next_signal(tenant.tenant_id) is False


@pytest.mark.asyncio
async def test_identity_at_1x(wiring):
    fake_clock, sim_repo, _, evt_repo, clock, _, scheduler = wiring
    tenant = _tenant(1, sim_repo, clock)
    await sim_repo.create(tenant)
    state = scheduler.initialize(tenant.tenant_id, _timeline(10), warp_speed=1)
    assert scheduler.next_delivery_delay(tenant, state) == pytest.approx(10.0)


@pytest.mark.asyncio
async def test_ordering_preserved_across_sources(wiring):
    _, sim_repo, _, evt_repo, clock, _, scheduler = wiring
    tenant = _tenant(60, sim_repo, clock)
    await sim_repo.create(tenant)
    # Unsorted input
    timeline = [
        {"offset_seconds": 30, "signal_envelope": {"signal_id": "b"}},
        {"offset_seconds": 0, "signal_envelope": {"signal_id": "a"}},
        {"offset_seconds": 15, "signal_envelope": {"signal_id": "c"}},
    ]
    scheduler.initialize(tenant.tenant_id, timeline, warp_speed=60)
    # Advance wall clock 1 sec → 60 sim sec → all due
    fake_clock = clock._now  # FakeClock
    fake_clock.advance(1)
    # Drain
    for _ in range(3):
        await scheduler.deliver_next_signal(tenant.tenant_id)
    events = evt_repo.list_events(tenant.tenant_id)
    # offset order: 0, 15, 30
    assert [e.payload["offset_seconds"] for e in events] == [0, 15, 30]


@pytest.mark.asyncio
async def test_scheduler_state_persists(wiring):
    fake_clock, sim_repo, _, evt_repo, clock, _, scheduler = wiring
    tenant = _tenant(10, sim_repo, clock)
    await sim_repo.create(tenant)
    scheduler.initialize(tenant.tenant_id, _timeline(0), warp_speed=10)
    await scheduler.deliver_next_signal(tenant.tenant_id)
    state = scheduler.get_state(tenant.tenant_id)
    assert state.last_delivered_signal_id is not None
    assert state.next_signal_index == 1
