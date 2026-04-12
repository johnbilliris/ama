"""Circuit breaker for LLM availability recovery.

Implements a three-state circuit breaker (CLOSED → OPEN → HALF_OPEN) to prevent
retry storms when Azure OpenAI is unavailable.  Thread-safe via threading.Lock.
"""

from __future__ import annotations

import logging
import threading
import time
from collections.abc import Callable
from enum import Enum

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    """Thread-safe circuit breaker with injectable clock for testing.

    Args:
        failure_threshold: Consecutive failures before CLOSED → OPEN.
        recovery_timeout: Seconds before OPEN → HALF_OPEN.
        clock: Callable returning monotonic time (default: ``time.monotonic``).
    """

    def __init__(
        self,
        failure_threshold: int = 3,
        recovery_timeout: float = 30.0,
        clock: Callable[[], float] | None = None,
    ) -> None:
        self._failure_threshold = failure_threshold
        self._recovery_timeout = recovery_timeout
        self._clock = clock or time.monotonic

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time: float = 0.0
        self._lock = threading.Lock()

    @property
    def state(self) -> CircuitState:
        """Return the current circuit state, transitioning OPEN → HALF_OPEN if recovery timeout elapsed."""
        with self._lock:
            if self._state is CircuitState.OPEN:
                elapsed = self._clock() - self._last_failure_time
                if elapsed >= self._recovery_timeout:
                    logger.info(
                        "Circuit breaker transition: %s → %s (recovery timeout elapsed)",
                        CircuitState.OPEN.value,
                        CircuitState.HALF_OPEN.value,
                    )
                    self._state = CircuitState.HALF_OPEN
            return self._state

    def can_execute(self) -> bool:
        """Return True if a call is allowed (CLOSED or HALF_OPEN)."""
        return self.state in (CircuitState.CLOSED, CircuitState.HALF_OPEN)

    def record_success(self) -> None:
        """Record a successful call — reset failures, HALF_OPEN → CLOSED."""
        with self._lock:
            if self._state is CircuitState.HALF_OPEN:
                logger.info(
                    "Circuit breaker transition: %s → %s (probe succeeded)",
                    CircuitState.HALF_OPEN.value,
                    CircuitState.CLOSED.value,
                )
                self._state = CircuitState.CLOSED
            self._failure_count = 0

    def record_failure(self) -> None:
        """Record a failed call — increment counter, transition if threshold exceeded."""
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = self._clock()

            if self._state is CircuitState.HALF_OPEN:
                logger.warning(
                    "Circuit breaker transition: %s → %s (probe failed)",
                    CircuitState.HALF_OPEN.value,
                    CircuitState.OPEN.value,
                )
                self._state = CircuitState.OPEN
            elif self._state is CircuitState.CLOSED and self._failure_count >= self._failure_threshold:
                logger.warning(
                    "Circuit breaker transition: %s → %s (failure threshold %d exceeded)",
                    CircuitState.CLOSED.value,
                    CircuitState.OPEN.value,
                    self._failure_threshold,
                )
                self._state = CircuitState.OPEN
