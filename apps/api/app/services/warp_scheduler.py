"""Durable, cursor-based signal scheduler for warped simulations.

Research decisions R1 (server-owned schedule) and R6 (durable cursor):
signal delivery timing is driven by the server-computed simulation
clock, not by real-time ``asyncio.sleep`` chains. The scheduler persists
its cursor (``SignalSchedulerState``) so delivery can resume across
process restarts without losing or duplicating signals.

Two modes:

1. **Polling delivery loop** (:meth:`run_delivery_loop`): coroutine that
   sleeps for the warp-scaled delay until the next signal, delivers,
   advances the cursor and loops. Respects pause/resume and burst-rate
   throttle.
2. **On-demand tick** (:meth:`deliver_next_signal`): delivers the next
   due signal if its scheduled sim time has been reached. Useful from
   tests and background sweepers.
"""

from __future__ import annotations

import asyncio
import logging
import os
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from app.repositories.signal_repository import SignalRepository
from app.repositories.simulation_event_repository import SimulationEventRepository
from app.repositories.simulation_repository import SimulationRepository
from app.services.simulation_clock_service import SimulationClockService
from app.services.simulation_event_recorder import SimulationEventRecorder

from packages.domain.src.domain.models.simulation_event import SignalSchedulerState

logger = logging.getLogger(__name__)

_MAX_BURST_RATE_PER_SECOND = 100
_HEARTBEAT_INTERVAL_SECONDS = 10
_LEASE_STALE_SECONDS = 30
_DEFAULT_DELIVERY_LAG_WARNING = 10.0


class WarpScheduler:
    """Delivers seeded simulation signals in warp-compressed wall time."""

    def __init__(
        self,
        signal_repository: SignalRepository,
        event_repository: SimulationEventRepository,
        simulation_repository: SimulationRepository,
        clock_service: SimulationClockService,
        event_recorder: SimulationEventRecorder,
        *,
        owner_id: str | None = None,
        max_burst_rate: int = _MAX_BURST_RATE_PER_SECOND,
    ) -> None:
        self._signals = signal_repository
        self._events = event_repository
        self._sim_repo = simulation_repository
        self._clock = clock_service
        self._recorder = event_recorder
        self._owner = owner_id or f"sched-{uuid4().hex[:8]}"
        self._max_burst = max_burst_rate
        self._timelines: dict[str, list[dict[str, Any]]] = {}

    # ------------------------------------------------------------------
    # initialisation
    # ------------------------------------------------------------------

    def initialize(
        self,
        tenant_id: str,
        signal_timeline: list[dict[str, Any]],
        warp_speed: float = 1.0,
    ) -> SignalSchedulerState:
        sorted_timeline = sorted(signal_timeline, key=lambda s: float(s.get("offset_seconds", 0.0)))
        self._timelines[tenant_id] = sorted_timeline
        state = SignalSchedulerState(
            id=f"sched-{tenant_id}",
            tenant_id=tenant_id,
            next_signal_index=0,
            last_delivered_signal_id=None,
            last_delivery_sim_time=0.0,
            scheduler_owner=self._owner,
            heartbeat_at=datetime.now(UTC),
            delivery_lag_seconds=0.0,
        )
        self._events.save_scheduler_state(state)
        logger.info(
            "warp_scheduler_initialized tenant=%s signals=%d warp=%s",
            tenant_id,
            len(sorted_timeline),
            warp_speed,
        )
        return state

    def load_timeline(self, tenant_id: str, signal_timeline: list[dict[str, Any]]) -> None:
        self._timelines[tenant_id] = sorted(
            signal_timeline, key=lambda s: float(s.get("offset_seconds", 0.0))
        )

    def get_state(self, tenant_id: str) -> SignalSchedulerState | None:
        return self._events.get_scheduler_state(tenant_id)

    # ------------------------------------------------------------------
    # timing
    # ------------------------------------------------------------------

    def next_delivery_delay(
        self,
        tenant,
        state: SignalSchedulerState,
        signal_timeline: list[dict[str, Any]] | None = None,
    ) -> float | None:
        timeline = signal_timeline or self._timelines.get(tenant.tenant_id, [])
        if state.next_signal_index >= len(timeline):
            return None
        signal = timeline[state.next_signal_index]
        offset = float(signal.get("offset_seconds", 0.0))
        current = self._clock.get_current_sim_seconds(tenant)
        remaining_sim = offset - current
        if remaining_sim <= 0:
            return 0.0
        speed = max(tenant.current_warp_speed, 1e-9)
        return remaining_sim / speed

    # ------------------------------------------------------------------
    # delivery
    # ------------------------------------------------------------------

    async def deliver_next_signal(self, tenant_id: str) -> bool:
        tenant = await self._sim_repo.get_by_tenant_id(tenant_id)
        if tenant is None or tenant.clock_paused:
            return False
        state = self._events.get_scheduler_state(tenant_id)
        if state is None:
            return False
        timeline = self._timelines.get(tenant_id) or []
        if state.next_signal_index >= len(timeline):
            return False

        signal = timeline[state.next_signal_index]
        offset = float(signal.get("offset_seconds", 0.0))
        current = self._clock.get_current_sim_seconds(tenant)
        if current + 1e-6 < offset:
            return False  # not due yet

        envelope = dict(signal.get("signal_envelope") or signal)
        envelope.setdefault("signal_id", f"sig-{uuid4().hex[:12]}")
        envelope["scope"] = tenant_id
        envelope["source_context"] = "simulation"
        envelope["offset_seconds"] = offset
        try:
            await self._signals.create_signal(tenant_id, envelope)
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "warp_scheduler_delivery_failed tenant=%s idx=%s err=%s",
                tenant_id,
                state.next_signal_index,
                exc,
            )
            return False

        self._recorder.record_signal_delivered(
            tenant_id,
            current,
            signal_id=envelope["signal_id"],
            data_source_id=envelope.get("data_source_id", "unknown"),
            category=envelope.get("category", envelope.get("hazard_type", "unknown")),
            offset_seconds=offset,
        )

        lag_sim_seconds = max(current - offset, 0.0)
        lag_wall_seconds = lag_sim_seconds / max(tenant.current_warp_speed, 1e-9)
        new_state = state.model_copy(
            update={
                "next_signal_index": state.next_signal_index + 1,
                "last_delivered_signal_id": envelope["signal_id"],
                "last_delivery_sim_time": offset,
                "scheduler_owner": self._owner,
                "heartbeat_at": datetime.now(UTC),
                "delivery_lag_seconds": lag_wall_seconds,
            }
        )
        self._events.save_scheduler_state(new_state)
        return True

    async def run_delivery_loop(self, tenant_id: str) -> None:
        """Infinite-ish loop that delivers signals as their sim time arrives.

        Exits when all signals delivered, the tenant disappears, or the
        clock is paused. Caller is responsible for restarting on resume.
        """

        heartbeat = datetime.now(UTC)
        last_burst: list[float] = []
        while True:
            tenant = await self._sim_repo.get_by_tenant_id(tenant_id)
            if tenant is None or tenant.status not in ("Active",) or tenant.clock_paused:
                return
            state = self._events.get_scheduler_state(tenant_id)
            if state is None:
                return
            delay = self.next_delivery_delay(tenant, state)
            if delay is None:
                return  # done

            # Burst-rate throttle (max N deliveries per wall-clock second).
            now_ts = asyncio.get_event_loop().time()
            last_burst = [t for t in last_burst if now_ts - t < 1.0]
            if len(last_burst) >= self._max_burst:
                await asyncio.sleep(1.0 - (now_ts - last_burst[0]))
                continue

            if delay > 0:
                await asyncio.sleep(min(delay, 1.0))
                continue

            delivered = await self.deliver_next_signal(tenant_id)
            if delivered:
                last_burst.append(asyncio.get_event_loop().time())

            # Periodic heartbeat.
            now = datetime.now(UTC)
            if (now - heartbeat).total_seconds() > _HEARTBEAT_INTERVAL_SECONDS:
                heartbeat = now
                state = self._events.get_scheduler_state(tenant_id)
                if state is not None:
                    self._events.save_scheduler_state(
                        state.model_copy(update={"heartbeat_at": now})
                    )

    # ------------------------------------------------------------------
    # control
    # ------------------------------------------------------------------

    def pause(self, tenant_id: str) -> None:
        state = self._events.get_scheduler_state(tenant_id)
        if state is not None:
            self._events.save_scheduler_state(
                state.model_copy(update={"heartbeat_at": datetime.now(UTC)})
            )

    def resume(self, tenant_id: str) -> None:
        self.pause(tenant_id)  # same bookkeeping

    def update_speed(self, tenant_id: str, new_speed: float) -> None:
        """Recalculate scheduler timing after a speed change.

        The cursor itself does not need to move; only the *wall-clock*
        delay until the next signal changes. The delivery loop re-reads
        the tenant and recomputes on its next iteration, so this hook
        exists primarily to refresh the heartbeat.
        """
        state = self._events.get_scheduler_state(tenant_id)
        if state is not None:
            self._events.save_scheduler_state(
                state.model_copy(update={"heartbeat_at": datetime.now(UTC)})
            )

    # ------------------------------------------------------------------
    # diagnostics
    # ------------------------------------------------------------------

    def delivery_lag_warning_threshold(self) -> float:
        try:
            return float(os.environ.get("SIM_DELIVERY_LAG_WARNING_SECONDS", _DEFAULT_DELIVERY_LAG_WARNING))
        except ValueError:
            return _DEFAULT_DELIVERY_LAG_WARNING
