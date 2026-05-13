"""Circuit breaker state-transition benchmarks.

Measures the timing of CLOSED→OPEN, OPEN→HALF_OPEN, and full
recovery cycles using a short ``recovery_timeout`` (100 ms) to stay
within the 60 s benchmark wall-clock budget.
"""

from __future__ import annotations

import pytest
from benchmark_helpers import set_benchmark_metadata
from common.circuit_breaker import CircuitBreaker, CircuitState

RECOVERY_TIMEOUT: float = 0.1  # 100 ms — fast benchmarking


# ── State transition benchmarks ──────────────────────────────────────────────


@pytest.mark.benchmark(group="circuit-breaker")
def test_cb_closed_to_open(benchmark) -> None:
    """Measure time for 3 consecutive failures to trigger CLOSED → OPEN."""

    def closed_to_open():
        # Inject a stopped clock so a slow CI runner cannot let the 100 ms
        # recovery_timeout elapse between record_failure() and the state
        # check (would flake to HALF_OPEN). Mirrors the other CB benchmarks.
        now = [0.0]

        def clock():
            return now[0]

        cb = CircuitBreaker(failure_threshold=3, recovery_timeout=RECOVERY_TIMEOUT, clock=clock)
        for _ in range(3):
            cb.record_failure()
        assert cb.state == CircuitState.OPEN

    set_benchmark_metadata(
        benchmark,
        agent="shared",
        metric_type="circuit_breaker",
        slo_target_s=RECOVERY_TIMEOUT * 2,
    )
    benchmark(closed_to_open)


@pytest.mark.benchmark(group="circuit-breaker")
def test_cb_open_to_half_open(benchmark) -> None:
    """Measure OPEN → HALF_OPEN transition after recovery timeout elapses."""

    def open_to_half_open():
        now = [0.0]

        def clock():
            return now[0]

        cb = CircuitBreaker(failure_threshold=3, recovery_timeout=RECOVERY_TIMEOUT, clock=clock)
        # Drive to OPEN
        for _ in range(3):
            cb.record_failure()
        assert cb.state == CircuitState.OPEN
        # Advance clock past recovery timeout
        now[0] += RECOVERY_TIMEOUT + 0.001
        # Accessing state triggers the transition
        assert cb.state == CircuitState.HALF_OPEN

    set_benchmark_metadata(
        benchmark,
        agent="shared",
        metric_type="circuit_breaker",
        slo_target_s=RECOVERY_TIMEOUT * 2,
    )
    benchmark(open_to_half_open)


@pytest.mark.benchmark(group="circuit-breaker")
def test_cb_full_recovery(benchmark) -> None:
    """Measure complete CLOSED → OPEN → HALF_OPEN → CLOSED cycle."""

    def full_cycle():
        now = [0.0]

        def clock():
            return now[0]

        cb = CircuitBreaker(failure_threshold=3, recovery_timeout=RECOVERY_TIMEOUT, clock=clock)
        # CLOSED → OPEN: 3 failures
        for _ in range(3):
            cb.record_failure()
        assert cb.state == CircuitState.OPEN
        # OPEN → HALF_OPEN: advance clock past recovery
        now[0] += RECOVERY_TIMEOUT + 0.001
        assert cb.state == CircuitState.HALF_OPEN
        # HALF_OPEN → CLOSED: record success
        cb.record_success()
        assert cb.state == CircuitState.CLOSED

    set_benchmark_metadata(
        benchmark,
        agent="shared",
        metric_type="circuit_breaker",
        slo_target_s=RECOVERY_TIMEOUT * 2,
    )
    benchmark(full_cycle)
