"""Unit tests for :class:`SimulationClockService` (feature 026)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from app.services.simulation_clock_service import SimulationClockService

from packages.domain.src.domain.models.simulation_tenant import SimulationTenant


class _FakeClock:
    def __init__(self, start: datetime) -> None:
        self.now = start

    def advance(self, seconds: float) -> None:
        self.now = self.now + timedelta(seconds=seconds)

    def __call__(self) -> datetime:
        return self.now


def _make_tenant() -> SimulationTenant:
    return SimulationTenant(
        tenant_id="sim-" + "a" * 36,
        scenario_id="sc",
        scenario_run_id="run",
        scenario_type="Bushfire",
        created_by="user",
        participants=["user"],
    )


def _service() -> tuple[SimulationClockService, _FakeClock]:
    fake = _FakeClock(datetime(2026, 4, 22, 12, 0, 0, tzinfo=UTC))
    return SimulationClockService(now_provider=fake), fake


def test_start_clock_sets_running_state() -> None:
    svc, fake = _service()
    tenant = svc.start_clock(_make_tenant(), warp_speed=10)
    assert tenant.clock_paused is False
    assert tenant.current_warp_speed == 10.0
    assert tenant.last_resumed_at == fake.now


def test_pause_clock_computes_accumulated_at_warp() -> None:
    svc, fake = _service()
    tenant = svc.start_clock(_make_tenant(), warp_speed=5)
    fake.advance(60)  # 60 wall-clock seconds @ 5× = 300 sim seconds
    tenant = svc.pause_clock(tenant)
    assert tenant.clock_paused is True
    assert tenant.last_resumed_at is None
    assert tenant.accumulated_sim_seconds == pytest.approx(300.0)
    assert tenant.elapsed_seconds == pytest.approx(300.0)


def test_change_speed_snapshots_and_records_history() -> None:
    svc, fake = _service()
    tenant = svc.start_clock(_make_tenant(), warp_speed=5)
    fake.advance(10)  # 50 sim-sec
    tenant = svc.change_speed(tenant, 24)
    assert tenant.current_warp_speed == 24.0
    assert tenant.accumulated_sim_seconds == pytest.approx(50.0)
    assert tenant.last_resumed_at == fake.now
    assert len(tenant.warp_speed_history) == 1
    entry = tenant.warp_speed_history[0]
    assert entry.old_speed == 5.0
    assert entry.new_speed == 24.0
    assert entry.sim_time_offset == pytest.approx(50.0)


def test_get_current_sim_seconds_live() -> None:
    svc, fake = _service()
    tenant = svc.start_clock(_make_tenant(), warp_speed=60)
    fake.advance(30)  # 30 wall × 60 = 1800 sim
    assert svc.get_current_sim_seconds(tenant) == pytest.approx(1800.0)


def test_resume_after_pause_preserves_offset() -> None:
    svc, fake = _service()
    tenant = svc.start_clock(_make_tenant(), warp_speed=10)
    fake.advance(5)
    tenant = svc.pause_clock(tenant)
    fake.advance(30)  # wall clock moves while paused
    tenant = svc.resume_clock(tenant)
    assert tenant.accumulated_sim_seconds == pytest.approx(50.0)
    assert tenant.clock_paused is False
    fake.advance(10)
    assert svc.get_current_sim_seconds(tenant) == pytest.approx(150.0)


def test_cannot_pause_already_paused() -> None:
    svc, _ = _service()
    with pytest.raises(ValueError):
        svc.pause_clock(_make_tenant())


def test_cannot_start_already_running() -> None:
    svc, _ = _service()
    running = svc.start_clock(_make_tenant(), warp_speed=1)
    with pytest.raises(ValueError):
        svc.start_clock(running, warp_speed=2)


def test_invalid_speed_rejected() -> None:
    svc, _ = _service()
    with pytest.raises(ValueError):
        svc.start_clock(_make_tenant(), warp_speed=7)
    running = svc.start_clock(_make_tenant(), warp_speed=1)
    with pytest.raises(ValueError):
        svc.change_speed(running, 3)


def test_multiple_speed_changes_preserve_time() -> None:
    svc, fake = _service()
    tenant = svc.start_clock(_make_tenant(), warp_speed=1)
    fake.advance(10)  # 10 sim sec
    tenant = svc.change_speed(tenant, 10)
    fake.advance(10)  # +100 sim sec
    tenant = svc.change_speed(tenant, 5)
    fake.advance(10)  # +50 sim sec
    assert svc.get_current_sim_seconds(tenant) == pytest.approx(160.0)
    assert len(tenant.warp_speed_history) == 2
