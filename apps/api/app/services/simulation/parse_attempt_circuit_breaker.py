"""Parse-attempt token-bucket circuit breaker (T-C06 / FR-009 layer-2).

Implements plan-decision #4:

* Opens when **>60 parse-attempts in a 60-second sliding window**, OR
* >10 attempts in any 1-second burst, for a given user.

When the circuit opens for a user, callers route to the regex fallback
extractor for a 60 s cooldown, then a single half-open probe is allowed
before the circuit closes again.

The breaker is per-user (keyed on ``user_id``) and per-process. In
production the controller_service shares a singleton.

Emits ``injection.circuit_open`` audit entries via the writer registered at
construction time.
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections import deque
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)

# Plan-decision #4 thresholds.
WINDOW_SECONDS = 60
WINDOW_THRESHOLD = 60
BURST_WINDOW_SECONDS = 1.0
BURST_THRESHOLD = 10
COOLDOWN_SECONDS = 60.0


@dataclass
class _UserState:
    timestamps: deque[float] = field(default_factory=deque)
    state: str = "closed"  # closed | open | half_open
    opened_at: float | None = None
    half_open_outstanding: bool = False


class ParseAttemptCircuitBreaker:
    """Per-user token-bucket parse-attempt breaker."""

    def __init__(
        self,
        *,
        audit_writer: Any | None = None,
        clock: Callable[[], float] | None = None,
    ) -> None:
        self._users: dict[str, _UserState] = {}
        self._lock = asyncio.Lock()
        self._audit_writer = audit_writer
        self._clock = clock or time.monotonic

    def _state(self, user_id: str) -> _UserState:
        state = self._users.get(user_id)
        if state is None:
            state = _UserState()
            self._users[user_id] = state
        return state

    def _purge(self, state: _UserState, now: float) -> None:
        cutoff = now - WINDOW_SECONDS
        while state.timestamps and state.timestamps[0] < cutoff:
            state.timestamps.popleft()

    def _burst_count(self, state: _UserState, now: float) -> int:
        cutoff = now - BURST_WINDOW_SECONDS
        return sum(1 for ts in state.timestamps if ts >= cutoff)

    async def attempt(
        self,
        *,
        user_id: str,
        simulation_id: str | None = None,
        record_attempt: bool = True,
    ) -> str:
        """Register a parse attempt and return the resulting circuit state.

        Returns one of ``"closed"``, ``"open"``, or ``"half_open"``. Callers
        treat ``"open"`` as the signal to route to the fallback extractor.
        """
        async with self._lock:
            now = self._clock()
            state = self._state(user_id)
            self._purge(state, now)

            # Cooldown elapsed → half-open with a single probe.
            if state.state == "open" and state.opened_at is not None:
                if now - state.opened_at >= COOLDOWN_SECONDS:
                    state.state = "half_open"
                    state.half_open_outstanding = False

            if record_attempt:
                state.timestamps.append(now)
                # Re-purge after append (cheap — single element check).
                self._purge(state, now)

            if state.state == "open":
                return "open"

            if state.state == "half_open":
                if state.half_open_outstanding:
                    return "open"
                state.half_open_outstanding = True
                return "half_open"

            # Closed state — check both thresholds.
            window_count = len(state.timestamps)
            burst_count = self._burst_count(state, now)
            if window_count > WINDOW_THRESHOLD or burst_count > BURST_THRESHOLD:
                state.state = "open"
                state.opened_at = now
                await self._emit_circuit_open(
                    user_id=user_id,
                    simulation_id=simulation_id,
                    attempts_in_window=window_count,
                )
                return "open"
            return "closed"

    async def record_success(self, user_id: str) -> None:
        """Reset the breaker on a successful parse (closes a half-open probe)."""
        async with self._lock:
            state = self._users.get(user_id)
            if state is None:
                return
            if state.state in {"open", "half_open"}:
                logger.info("parse_attempt_breaker.closed user=%s", user_id)
            state.state = "closed"
            state.opened_at = None
            state.half_open_outstanding = False
            state.timestamps.clear()

    async def _emit_circuit_open(
        self,
        *,
        user_id: str,
        simulation_id: str | None,
        attempts_in_window: int,
    ) -> None:
        if self._audit_writer is None or simulation_id is None:
            return
        try:
            writer_call = getattr(self._audit_writer, "write")
            result: Any = writer_call(
                "injection.circuit_open",
                simulation_id=simulation_id,
                actor="parse_attempt_breaker",
                details={
                    "user_id": user_id,
                    "attempts_in_window": attempts_in_window,
                    "threshold": WINDOW_THRESHOLD,
                    "window_seconds": WINDOW_SECONDS,
                    "enforcement_layer": "in_process",
                    "cooldown_seconds": int(COOLDOWN_SECONDS),
                },
            )
            if isinstance(result, Awaitable):
                await result
        except Exception:  # pragma: no cover - defensive
            logger.exception("parse_attempt_breaker.audit_failed")
