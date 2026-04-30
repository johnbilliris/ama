"""pybreaker-backed CircuitBreaker adapter (spec 032 ADR-034, FR-P03).

Adapts the third-party ``pybreaker`` library to the existing
``common.circuit_breaker.CircuitBreaker`` Protocol so call-sites can opt in
without changing their interface. State-change listeners emit App Insights
customMetrics ``circuitbreaker.state`` and ``circuitbreaker.transitions_total``.

Falls back to the hand-rolled CircuitBreaker if pybreaker isn't installed yet
(import-time ``ImportError`` produces a working but un-wrapped breaker so existing
code keeps running during migration).
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

from common.circuit_breaker import CircuitBreaker as LegacyCircuitBreaker
from common.circuit_breaker import CircuitState

logger = logging.getLogger(__name__)


def _emit_state_metric(name: str, state: str) -> None:
    """Emit a circuitbreaker.state customMetric to App Insights when OTel is wired (Stream 5)."""
    try:
        # Lazy import to avoid coupling the resilience layer to OTel hard.
        from apps.api.app.observability.metrics import emit_gauge

        emit_gauge("circuitbreaker.state", _state_to_int(state), {"name": name})
    except Exception:
        # Telemetry is best-effort; never let it break call paths.
        logger.debug("circuitbreaker telemetry skipped", exc_info=True)


def _emit_transition_metric(name: str, from_state: str, to_state: str) -> None:
    try:
        from apps.api.app.observability.metrics import emit_counter

        emit_counter(
            "circuitbreaker.transitions_total",
            1,
            {"name": name, "from_state": from_state, "to_state": to_state},
        )
    except Exception:
        logger.debug("circuitbreaker telemetry skipped", exc_info=True)


def _state_to_int(state: str) -> int:
    return {"closed": 0, "half_open": 1, "open": 2}.get(state, -1)


class PyBreakerCircuitBreaker:
    """pybreaker-backed circuit breaker honouring the legacy CircuitBreaker shape.

    Attributes are the same as :class:`common.circuit_breaker.CircuitBreaker`.
    Call sites can swap import via:
        ``from common.resilience import PyBreakerCircuitBreaker as CircuitBreaker``
    """

    def __init__(
        self,
        failure_threshold: int = 3,
        recovery_timeout: float = 30.0,
        name: str = "default",
        clock: Callable[[], float] | None = None,
    ) -> None:
        self._name = name
        self._failure_threshold = failure_threshold
        self._recovery_timeout = recovery_timeout

        self._impl: Any  # pybreaker.CircuitBreaker | LegacyCircuitBreaker
        try:
            import pybreaker

            class _Listener(pybreaker.CircuitBreakerListener):  # type: ignore[no-untyped-call,misc]
                def __init__(self, owner: PyBreakerCircuitBreaker) -> None:
                    self._owner = owner

                def state_change(self, cb: Any, old_state: Any, new_state: Any) -> None:
                    old_name = getattr(old_state, "name", str(old_state)).lower()
                    new_name = getattr(new_state, "name", str(new_state)).lower()
                    logger.info(
                        "circuitbreaker '%s' transition %s -> %s",
                        self._owner._name,
                        old_name,
                        new_name,
                    )
                    _emit_state_metric(self._owner._name, new_name)
                    _emit_transition_metric(self._owner._name, old_name, new_name)

            self._impl = pybreaker.CircuitBreaker(
                fail_max=failure_threshold,
                reset_timeout=recovery_timeout,
                listeners=[_Listener(self)],
                name=name,
            )
            self._using_pybreaker = True
        except ImportError:
            logger.warning("pybreaker not installed; falling back to legacy CircuitBreaker for '%s'", name)
            self._impl = LegacyCircuitBreaker(
                failure_threshold=failure_threshold,
                recovery_timeout=recovery_timeout,
                clock=clock,
            )
            self._using_pybreaker = False

    @property
    def state(self) -> CircuitState:
        if self._using_pybreaker:
            mapping = {
                "closed": CircuitState.CLOSED,
                "open": CircuitState.OPEN,
                "half-open": CircuitState.HALF_OPEN,
                "half_open": CircuitState.HALF_OPEN,
            }
            current = str(self._impl.current_state).lower()
            return mapping.get(current, CircuitState.CLOSED)
        return self._impl.state  # type: ignore[no-any-return]

    def can_execute(self) -> bool:
        return self.state in (CircuitState.CLOSED, CircuitState.HALF_OPEN)

    def record_success(self) -> None:
        if self._using_pybreaker:
            # pybreaker tracks success implicitly via call(); for compatibility
            # with the legacy interface, manually invoke a no-op success.
            try:
                self._impl.call(lambda: None)
            except Exception:
                pass
        else:
            self._impl.record_success()

    def record_failure(self) -> None:
        if self._using_pybreaker:

            def _raise() -> None:
                raise RuntimeError("recorded failure")

            try:
                self._impl.call(_raise)
            except Exception:
                pass
        else:
            self._impl.record_failure()
