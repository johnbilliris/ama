"""Per-agent kill-switch watcher (spec 032 FR-AG05 + FR-AG05a).

Push-based design per the T016 spike:
  Cosmos config change -> change-feed -> Service Bus topic ``killswitch-events``
  -> agent watcher -> in-flight handoff drain (≤ 5s) -> degraded_mode = true.

End-to-end propagation budget P99 ≤ 30 s. Heartbeat metric
``agent.killswitch.lag_seconds`` is emitted by the watcher when it applies the
toggle (see ``heartbeat.py``).

This module provides the in-process state container + subscriber registration.
The Service Bus listener is created per agent process at startup; tests use
``register_subscriber`` directly.
"""

from __future__ import annotations

import logging
import os
import threading
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime

from .heartbeat import emit_killswitch_lag_seconds

logger = logging.getLogger(__name__)

# Process-wide map of agent_id -> kill-switch state.
_STATE: dict[str, KillSwitchState] = {}
_LOCK = threading.RLock()
_SUBSCRIBERS: list[Callable[[KillSwitchState], None]] = []


@dataclass(frozen=True)
class KillSwitchState:
    """Immutable snapshot of a kill-switch state."""

    agent_id: str
    engaged: bool
    engaged_at: datetime | None = None
    engaged_by: str | None = None
    reason: str | None = None
    expires_at: datetime | None = None
    justification_code: str | None = None
    proposer: str | None = None  # for dual-approval workflow
    approver: str | None = None
    # The producer (Cosmos change-feed publisher) stamps this so the watcher can
    # measure end-to-end propagation latency.
    produced_at: datetime | None = field(default=None, compare=False)


def is_engaged(agent_id: str | None = None) -> bool:
    """Return whether the agent (defaults to ``AMA_AGENT_ID``) has its kill-switch engaged."""
    aid = agent_id or os.getenv("AMA_AGENT_ID", "unknown")
    with _LOCK:
        state = _STATE.get(aid)
        return bool(state and state.engaged)


def get_state(agent_id: str | None = None) -> KillSwitchState | None:
    aid = agent_id or os.getenv("AMA_AGENT_ID", "unknown")
    with _LOCK:
        return _STATE.get(aid)


def register_subscriber(callback: Callable[[KillSwitchState], None]) -> None:
    """Register a callback fired whenever any kill-switch state changes."""
    with _LOCK:
        _SUBSCRIBERS.append(callback)


def apply(new_state: KillSwitchState) -> None:
    """Apply a new kill-switch state.

    Called by the Service Bus listener (production) or directly by tests.
    Emits the ``agent.killswitch.lag_seconds`` heartbeat with the producer-to-
    consumer wall-clock when ``produced_at`` is present.
    """
    with _LOCK:
        previous = _STATE.get(new_state.agent_id)
        _STATE[new_state.agent_id] = new_state
        subscribers = list(_SUBSCRIBERS)

    if new_state.produced_at is not None:
        lag_seconds = (datetime.now(UTC) - new_state.produced_at).total_seconds()
        emit_killswitch_lag_seconds(new_state.agent_id, max(lag_seconds, 0.0))
    else:
        logger.debug("kill-switch state %r applied without produced_at; lag metric skipped", new_state.agent_id)

    if previous is None or previous.engaged != new_state.engaged:
        logger.info(
            "kill-switch %s: %s -> %s (reason=%r)",
            new_state.agent_id,
            getattr(previous, "engaged", None),
            new_state.engaged,
            new_state.reason,
        )

    for cb in subscribers:
        try:
            cb(new_state)
        except Exception:  # noqa: BLE001
            logger.exception("kill-switch subscriber failed")


class KillSwitchWatcher:
    """Lightweight watcher abstraction; production wiring uses Service Bus.

    Tests can construct the watcher with a fake source (an iterable of states)
    to avoid Service Bus dependencies.
    """

    def __init__(self, agent_id: str, source: Callable[[], KillSwitchState | None] | None = None) -> None:
        self._agent_id = agent_id
        self._source = source

    def poll_once(self) -> KillSwitchState | None:
        """Pull the next state from the source (test hook)."""
        if self._source is None:
            return None
        state = self._source()
        if state is not None:
            apply(state)
        return state


def reset_for_tests() -> None:
    """Clear all in-process state; for unit tests only."""
    with _LOCK:
        _STATE.clear()
        _SUBSCRIBERS.clear()
