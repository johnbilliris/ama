"""T-C06 parse-attempt circuit breaker tests (FR-009 layer-2)."""

from __future__ import annotations

import pytest

from apps.api.app.services.simulation.parse_attempt_circuit_breaker import (
    BURST_THRESHOLD,
    COOLDOWN_SECONDS,
    WINDOW_THRESHOLD,
    ParseAttemptCircuitBreaker,
)


class _ManualClock:
    def __init__(self) -> None:
        self.t = 0.0

    def __call__(self) -> float:
        return self.t

    def advance(self, seconds: float) -> None:
        self.t += seconds


@pytest.mark.asyncio
async def test_burst_threshold_opens_circuit() -> None:
    clock = _ManualClock()
    breaker = ParseAttemptCircuitBreaker(clock=clock)
    states: list[str] = []
    for _ in range(BURST_THRESHOLD + 2):
        states.append(await breaker.attempt(user_id="u1"))
    assert "open" in states


@pytest.mark.asyncio
async def test_window_threshold_opens_circuit() -> None:
    clock = _ManualClock()
    breaker = ParseAttemptCircuitBreaker(clock=clock)
    # 65 attempts spaced ~1s apart — below burst threshold but exceeds window.
    last_state = "closed"
    for _ in range(WINDOW_THRESHOLD + 5):
        clock.advance(1.0)
        last_state = await breaker.attempt(user_id="u1")
    assert last_state == "open"


@pytest.mark.asyncio
async def test_half_open_after_cooldown_then_success_closes() -> None:
    clock = _ManualClock()
    breaker = ParseAttemptCircuitBreaker(clock=clock)
    for _ in range(BURST_THRESHOLD + 2):
        await breaker.attempt(user_id="u1")
    # Trip the breaker.
    state = await breaker.attempt(user_id="u1")
    assert state == "open"
    # Wait out the cooldown.
    clock.advance(COOLDOWN_SECONDS + 0.1)
    state = await breaker.attempt(user_id="u1")
    assert state == "half_open"
    # While half-open the next attempt is blocked.
    state = await breaker.attempt(user_id="u1")
    assert state == "open"
    # Success on the half-open probe closes the breaker.
    await breaker.record_success("u1")
    state = await breaker.attempt(user_id="u1")
    assert state == "closed"
