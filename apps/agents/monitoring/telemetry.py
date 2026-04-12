"""OpenTelemetry metrics for the Monitoring Agent.

Includes LLM-specific telemetry instruments (spec-014).
All instrumentation is opt-in: no-op stubs when opentelemetry is absent.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

_OTEL_AVAILABLE = False

try:
    from opentelemetry.metrics import get_meter

    _OTEL_AVAILABLE = True
except ImportError:
    pass


_SERVICE_NAME = "monitoring-agent"


class _NoOpMetric:
    """Drop-in stub for any metric type."""

    def add(self, value: Any = 1, attributes: dict | None = None) -> None:
        pass

    def record(self, value: Any = 0, attributes: dict | None = None) -> None:
        pass


def _get_meter() -> Any:
    if _OTEL_AVAILABLE:
        return get_meter(_SERVICE_NAME)
    return _NoOpMeter()


class _NoOpMeter:
    def create_counter(self, name: str, **kwargs: Any) -> _NoOpMetric:
        return _NoOpMetric()

    def create_histogram(self, name: str, **kwargs: Any) -> _NoOpMetric:
        return _NoOpMetric()

    def create_up_down_counter(self, name: str, **kwargs: Any) -> _NoOpMetric:
        return _NoOpMetric()


_meter = _get_meter()

# LLM metrics (spec-014)
llm_call_count = _meter.create_counter(
    "llm.call.count", description="Total LLM API calls", unit="calls",
)
llm_call_duration = _meter.create_histogram(
    "llm.call.duration_ms", description="LLM call latency", unit="ms",
)
llm_tokens_input = _meter.create_counter(
    "llm.tokens.input", description="Cumulative input tokens consumed", unit="tokens",
)
llm_tokens_output = _meter.create_counter(
    "llm.tokens.output", description="Cumulative output tokens consumed", unit="tokens",
)
llm_fallback_count = _meter.create_counter(
    "llm.fallback.count", description="LLM fallback events", unit="events",
)
llm_error_count = _meter.create_counter(
    "llm.error.count", description="LLM error events", unit="events",
)
llm_circuit_breaker_state_change = _meter.create_counter(
    "llm.circuit_breaker.state_change", description="Circuit breaker state transitions", unit="events",
)
llm_budget_exceeded = _meter.create_counter(
    "llm.budget.exceeded", description="Monthly budget threshold breaches", unit="events",
)
llm_confidence_below_threshold = _meter.create_counter(
    "llm.confidence.below_threshold", description="Outputs flagged for human review", unit="events",
)
