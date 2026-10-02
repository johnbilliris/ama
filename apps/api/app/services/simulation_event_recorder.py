"""Write-boundary event recorder for simulation events (feature 026).

Research decision R3 — we intercept event writes at the service
boundary (signal delivery, chat turns, tool invocations, state changes)
and record them to the ``sim-events`` Cosmos container. Failures are
swallowed and logged (FR-010a graceful degradation): after three
consecutive failures the simulation's ``playback_status`` is downgraded
to ``"partial"`` by the service layer.

The recorder also opportunistically writes :class:`PlaybackSnapshot`
records at every 100 events or whenever the simulated clock crosses a
300-second boundary, whichever comes first.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from app.repositories.simulation_event_repository import SimulationEventRepository

from packages.domain.src.domain.models.simulation_event import (
    PlaybackSnapshot,
    SimulationEvent,
)

logger = logging.getLogger(__name__)

_SNAPSHOT_EVENT_INTERVAL = 100
_SNAPSHOT_TIME_INTERVAL_SECONDS = 300.0
_FAILURE_THRESHOLD = 3


class SimulationEventRecorder:
    """Thin façade around :class:`SimulationEventRepository` with helpers."""

    def __init__(self, repository: SimulationEventRepository) -> None:
        self._repo = repository
        self._consecutive_failures: dict[str, int] = {}
        self._last_snapshot_time: dict[str, float] = {}
        self._healthy: dict[str, bool] = {}

    # ------------------------------------------------------------------
    # core record
    # ------------------------------------------------------------------

    def record_event(
        self,
        tenant_id: str,
        event_type: str,
        sim_time_offset: float,
        payload: dict[str, Any],
    ) -> SimulationEvent | None:
        try:
            seq = self._repo.next_sequence(tenant_id)
            event = SimulationEvent(
                tenant_id=tenant_id,
                event_seq=seq,
                event_type=event_type,  # type: ignore[arg-type]
                sim_time_offset=float(sim_time_offset),
                wall_clock_time=datetime.now(UTC),
                payload=payload,
            )
            self._repo.append_event(event)
            self._consecutive_failures[tenant_id] = 0
            self._healthy[tenant_id] = True
            self._maybe_create_snapshot(tenant_id, event)
            return event
        except Exception as exc:  # noqa: BLE001
            failures = self._consecutive_failures.get(tenant_id, 0) + 1
            self._consecutive_failures[tenant_id] = failures
            logger.warning(
                "record_event failed tenant_id=%s type=%s failures=%s err=%s",
                tenant_id,
                event_type,
                failures,
                exc,
            )
            if failures >= _FAILURE_THRESHOLD:
                self._healthy[tenant_id] = False
                logger.error(
                    "simulation_event_recording_unhealthy tenant_id=%s threshold=%s",
                    tenant_id,
                    _FAILURE_THRESHOLD,
                )
            return None

    def is_healthy(self, tenant_id: str) -> bool:
        return self._healthy.get(tenant_id, True)

    # ------------------------------------------------------------------
    # convenience recorders
    # ------------------------------------------------------------------

    def record_signal_delivered(
        self,
        tenant_id: str,
        sim_time: float,
        *,
        signal_id: str,
        data_source_id: str,
        category: str,
        offset_seconds: float,
    ) -> SimulationEvent | None:
        return self.record_event(
            tenant_id,
            "signal_delivered",
            sim_time,
            {
                "signal_id": signal_id,
                "data_source_id": data_source_id,
                "category": category,
                "offset_seconds": offset_seconds,
            },
        )

    def record_chat_turn(
        self,
        tenant_id: str,
        sim_time: float,
        *,
        turn_sequence: int,
        role: str,
        message_preview: str,
        tool_calls: list[str] | None = None,
    ) -> SimulationEvent | None:
        event_type = "chat_turn_user" if role == "user" else "chat_turn_assistant"
        payload: dict[str, Any] = {
            "turn_sequence": turn_sequence,
            "message_preview": message_preview[:200],
        }
        if event_type == "chat_turn_assistant":
            payload["tool_calls"] = tool_calls or []
        return self.record_event(tenant_id, event_type, sim_time, payload)

    def record_tool_invocation(
        self,
        tenant_id: str,
        sim_time: float,
        *,
        tool_name: str,
        outcome: str,
        latency_ms: int,
    ) -> SimulationEvent | None:
        return self.record_event(
            tenant_id,
            "tool_invocation",
            sim_time,
            {"tool_name": tool_name, "outcome": outcome, "latency_ms": latency_ms},
        )

    def record_state_change(
        self,
        tenant_id: str,
        sim_time: float,
        *,
        from_status: str,
        to_status: str,
        trigger: str,
    ) -> SimulationEvent | None:
        return self.record_event(
            tenant_id,
            "state_change",
            sim_time,
            {"from_status": from_status, "to_status": to_status, "trigger": trigger},
        )

    def record_warp_speed_change(
        self,
        tenant_id: str,
        sim_time: float,
        *,
        old_speed: float,
        new_speed: float,
    ) -> SimulationEvent | None:
        return self.record_event(
            tenant_id,
            "warp_speed_change",
            sim_time,
            {"old_speed": old_speed, "new_speed": new_speed},
        )

    def record_ui_log(
        self,
        tenant_id: str,
        sim_time: float,
        *,
        text: str,
        author_oid: str | None = None,
        category: str | None = None,
    ) -> SimulationEvent | None:
        """Persist a free-form Event-Log line emitted by the dashboard UI.

        Used so optimistic client-side entries (Deploy / SITREP / sub-agent
        replies / scenario seeds / etc.) survive a page refresh by landing
        in the durable ``sim-events`` Cosmos container instead of being
        pruned once polling overlaps them.
        """
        payload: dict[str, Any] = {"text": text[:500]}
        if author_oid:
            payload["author_oid"] = author_oid
        if category:
            payload["category"] = category
        return self.record_event(tenant_id, "ui_log", sim_time, payload)

    # ------------------------------------------------------------------
    # snapshots
    # ------------------------------------------------------------------

    def _maybe_create_snapshot(self, tenant_id: str, event: SimulationEvent) -> None:
        last = self._last_snapshot_time.get(tenant_id)
        crossed_time = last is not None and event.sim_time_offset - last >= _SNAPSHOT_TIME_INTERVAL_SECONDS
        crossed_count = event.event_seq % _SNAPSHOT_EVENT_INTERVAL == 0
        # On the very first event, seed the anchor so the 300-second
        # window is measured from the initial event's sim time.
        if last is None and not crossed_count:
            self._last_snapshot_time[tenant_id] = event.sim_time_offset
            return
        if not (crossed_count or crossed_time):
            return
        try:
            snapshot = PlaybackSnapshot(
                tenant_id=tenant_id,
                event_seq=event.event_seq,
                sim_time_offset=event.sim_time_offset,
                state={
                    "last_event_type": event.event_type,
                    "last_event_payload": event.payload,
                },
                wall_clock_time=event.wall_clock_time,
            )
            self._repo.save_snapshot(snapshot)
            self._last_snapshot_time[tenant_id] = event.sim_time_offset
        except Exception as exc:  # noqa: BLE001
            self._healthy[tenant_id] = False
            logger.warning("snapshot_write_failed tenant_id=%s err=%s", tenant_id, exc)
