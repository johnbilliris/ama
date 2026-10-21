"""Content safety circuit breaker for Azure AI Content Safety (FR-009).

Wraps Azure AI Content Safety calls with circuit breaker pattern:
CLOSED → (3 failures) → OPEN → (60s) → HALF_OPEN → (probe success) → CLOSED
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from datetime import UTC, datetime

logger = logging.getLogger(__name__)


class ContentSafetyCircuitBreaker:
    """Circuit breaker for Azure AI Content Safety calls."""

    def __init__(
        self,
        trip_threshold: int = 3,
        cooldown_seconds: float = 60.0,
        clock: Callable[[], float] | None = None,
    ) -> None:
        self.state: str = "closed"
        self.failure_count: int = 0
        self.trip_threshold: int = trip_threshold
        self.cooldown_seconds: float = cooldown_seconds
        self.last_failure_at: datetime | None = None
        self.fallback_message_count: int = 0
        self._clock = clock or time.monotonic
        self._last_failure_monotonic: float = 0.0
        self._opened_at_monotonic: float = 0.0

    @property
    def is_open(self) -> bool:
        """Check if circuit is open (should use fallback)."""
        if self.state == "open":
            elapsed = self._clock() - self._opened_at_monotonic
            if elapsed >= self.cooldown_seconds:
                self.state = "half_open"
                logger.info("content_safety_probe_attempted")
                return False
            return True
        return False

    @property
    def should_use_fallback(self) -> bool:
        """True when in OPEN state (not yet in cooldown window for probe)."""
        return self.state in ("open", "half_open")

    def record_success(self) -> None:
        """Record a successful Azure AI call."""
        if self.state == "half_open":
            open_duration = self._clock() - self._opened_at_monotonic
            logger.info(
                "content_safety_circuit_closed",
                extra={"open_duration_seconds": round(open_duration, 1)},
            )
            # Report fallback summary
            if self.fallback_message_count > 0:
                logger.info(
                    "content_safety_fallback_summary",
                    extra={"fallback_message_count": self.fallback_message_count},
                )
        self.state = "closed"
        self.failure_count = 0
        self.fallback_message_count = 0

    def record_failure(self) -> None:
        """Record a failed Azure AI call."""
        self.failure_count += 1
        self.last_failure_at = datetime.now(UTC)
        self._last_failure_monotonic = self._clock()

        if self.state == "half_open":
            self.state = "open"
            self._opened_at_monotonic = self._clock()
            logger.warning(
                "content_safety_probe_failed",
                extra={"next_probe_seconds": self.cooldown_seconds},
            )
        elif self.state == "closed" and self.failure_count >= self.trip_threshold:
            self.state = "open"
            self._opened_at_monotonic = self._clock()
            logger.warning(
                "content_safety_circuit_opened",
                extra={
                    "consecutive_failures": self.failure_count,
                    "cooldown_seconds": self.cooldown_seconds,
                },
            )

    def record_fallback_usage(self) -> None:
        """Track a message validated via keyword fallback."""
        self.fallback_message_count += 1
