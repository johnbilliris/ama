"""Contract tests: Circuit breaker state transitions (US3).

Verifies:
- CLOSED → OPEN after failure_threshold consecutive failures
- OPEN → HALF_OPEN after recovery_timeout
- HALF_OPEN → CLOSED on probe success
- HALF_OPEN → OPEN on probe failure
- Thread safety under concurrent access
- Injectable clock for deterministic testing
"""

from __future__ import annotations

import threading

from apps.agents.common.circuit_breaker import CircuitBreaker, CircuitState


class TestCircuitBreakerTransitions:
    """Verify circuit breaker state machine transitions."""

    def test_initial_state_is_closed(self) -> None:
        cb = CircuitBreaker(failure_threshold=3, recovery_timeout=30.0)
        assert cb.state is CircuitState.CLOSED
        assert cb.can_execute() is True

    def test_closed_to_open_after_threshold(self) -> None:
        cb = CircuitBreaker(failure_threshold=3, recovery_timeout=30.0)
        for _ in range(3):
            cb.record_failure()
        assert cb.state is CircuitState.OPEN
        assert cb.can_execute() is False

    def test_stays_closed_below_threshold(self) -> None:
        cb = CircuitBreaker(failure_threshold=3, recovery_timeout=30.0)
        cb.record_failure()
        cb.record_failure()
        assert cb.state is CircuitState.CLOSED
        assert cb.can_execute() is True

    def test_open_to_half_open_after_recovery_timeout(self) -> None:
        current_time = 0.0

        def clock() -> float:
            return current_time

        cb = CircuitBreaker(failure_threshold=3, recovery_timeout=30.0, clock=clock)

        # Trip the breaker
        for _ in range(3):
            cb.record_failure()
        assert cb.state is CircuitState.OPEN

        # Advance clock past recovery timeout
        current_time = 31.0
        assert cb.state is CircuitState.HALF_OPEN
        assert cb.can_execute() is True

    def test_half_open_to_closed_on_success(self) -> None:
        current_time = 0.0

        def clock() -> float:
            return current_time

        cb = CircuitBreaker(failure_threshold=3, recovery_timeout=30.0, clock=clock)

        # Trip the breaker
        for _ in range(3):
            cb.record_failure()

        # Advance to half-open
        current_time = 31.0
        assert cb.state is CircuitState.HALF_OPEN

        # Successful probe
        cb.record_success()
        assert cb.state is CircuitState.CLOSED

    def test_half_open_to_open_on_failure(self) -> None:
        current_time = 0.0

        def clock() -> float:
            return current_time

        cb = CircuitBreaker(failure_threshold=3, recovery_timeout=30.0, clock=clock)

        # Trip the breaker
        for _ in range(3):
            cb.record_failure()

        # Advance to half-open
        current_time = 31.0
        assert cb.state is CircuitState.HALF_OPEN

        # Failed probe
        cb.record_failure()
        assert cb.state is CircuitState.OPEN

    def test_success_resets_failure_count(self) -> None:
        cb = CircuitBreaker(failure_threshold=3, recovery_timeout=30.0)
        cb.record_failure()
        cb.record_failure()
        cb.record_success()
        # After reset, 3 more failures needed
        cb.record_failure()
        cb.record_failure()
        assert cb.state is CircuitState.CLOSED

    def test_thread_safety_concurrent_failures(self) -> None:
        cb = CircuitBreaker(failure_threshold=100, recovery_timeout=30.0)
        threads = []
        for _ in range(100):
            t = threading.Thread(target=cb.record_failure)
            threads.append(t)
            t.start()
        for t in threads:
            t.join()
        # After 100 concurrent failures with threshold=100, should be OPEN
        assert cb.state is CircuitState.OPEN

    def test_injectable_clock(self) -> None:
        times = [0.0, 10.0, 20.0, 31.0]
        idx = 0

        def clock() -> float:
            nonlocal idx
            t = times[min(idx, len(times) - 1)]
            idx += 1
            return t

        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=30.0, clock=clock)
        cb.record_failure()  # Uses clock() for last_failure_time
        assert cb.state is CircuitState.OPEN
