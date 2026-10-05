"""Server-owned canonical simulation clock (feature 026-sim-warp-playback).

Research decision R2 — the server owns the clock so all participants
observe identical simulated time regardless of browser/network state.
This module is **pure** and stateless: callers pass a
:class:`SimulationTenant` and receive a new instance with updated
clock fields. Persistence is handled by the simulation service layer.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime

from packages.domain.src.domain.models.simulation_tenant import SimulationTenant
from packages.domain.src.domain.models.warp_constants import (
    DEFAULT_WARP_SPEED,
    validate_warp_speed,
)
from packages.domain.src.domain.models.warp_speed_change import WarpSpeedChange


class SimulationClockService:
    """Pure functions that mutate a tenant's clock state."""

    def __init__(self, now_provider: Callable[[], datetime] | None = None) -> None:
        self._now = now_provider or (lambda: datetime.now(UTC))

    # ------------------------------------------------------------------
    # lifecycle transitions
    # ------------------------------------------------------------------

    def start_clock(
        self,
        tenant: SimulationTenant,
        warp_speed: float = DEFAULT_WARP_SPEED,
    ) -> SimulationTenant:
        if not tenant.clock_paused and tenant.last_resumed_at is not None:
            raise ValueError("Clock is already running")
        speed = validate_warp_speed(warp_speed)
        return tenant.model_copy(
            update={
                "current_warp_speed": speed,
                "last_resumed_at": self._now(),
                "clock_paused": False,
            }
        )

    def pause_clock(self, tenant: SimulationTenant) -> SimulationTenant:
        if tenant.clock_paused:
            raise ValueError("Clock is already paused")
        accumulated = self._compute_accumulated(tenant)
        return tenant.model_copy(
            update={
                "accumulated_sim_seconds": accumulated,
                "last_resumed_at": None,
                "clock_paused": True,
                "elapsed_seconds": accumulated,
            }
        )

    def resume_clock(self, tenant: SimulationTenant) -> SimulationTenant:
        if not tenant.clock_paused:
            raise ValueError("Clock is already running")
        return tenant.model_copy(
            update={
                "last_resumed_at": self._now(),
                "clock_paused": False,
            }
        )

    def change_speed(self, tenant: SimulationTenant, new_speed: float) -> SimulationTenant:
        target = validate_warp_speed(new_speed)
        old_speed = tenant.current_warp_speed
        now = self._now()
        if tenant.clock_paused or tenant.last_resumed_at is None:
            # Speed change while paused just records the new speed.
            change = WarpSpeedChange(
                sim_time_offset=tenant.accumulated_sim_seconds,
                old_speed=old_speed,
                new_speed=target,
                changed_at=now,
            )
            return tenant.model_copy(
                update={
                    "current_warp_speed": target,
                    "warp_speed_history": [*tenant.warp_speed_history, change],
                }
            )

        accumulated = self._compute_accumulated(tenant, now=now)
        change = WarpSpeedChange(
            sim_time_offset=accumulated,
            old_speed=old_speed,
            new_speed=target,
            changed_at=now,
        )
        return tenant.model_copy(
            update={
                "accumulated_sim_seconds": accumulated,
                "current_warp_speed": target,
                "last_resumed_at": now,
                "elapsed_seconds": accumulated,
                "warp_speed_history": [*tenant.warp_speed_history, change],
            }
        )

    # ------------------------------------------------------------------
    # reads
    # ------------------------------------------------------------------

    def get_current_sim_seconds(self, tenant: SimulationTenant) -> float:
        if tenant.clock_paused or tenant.last_resumed_at is None:
            return tenant.accumulated_sim_seconds
        return self._compute_accumulated(tenant)

    def _compute_accumulated(self, tenant: SimulationTenant, *, now: datetime | None = None) -> float:
        if tenant.last_resumed_at is None:
            return tenant.accumulated_sim_seconds
        now = now or self._now()
        delta = (now - tenant.last_resumed_at).total_seconds()
        delta = max(delta, 0.0)
        return tenant.accumulated_sim_seconds + delta * tenant.current_warp_speed
