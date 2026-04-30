"""OpenTelemetry distributed tracing, metrics, and custom events.

Implements contracts/telemetry.md:
- Span hierarchy for 11-stage pipeline
- 23 metrics (processing, approval, delivery, quality, operational, degradation)
- 17 custom events

All instrumentation is opt-in: when ``opentelemetry`` is not installed, the
module exports no-op stubs so production code runs without instrumentation overhead.
"""

from __future__ import annotations

import logging
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Detect OpenTelemetry availability
# ---------------------------------------------------------------------------

_OTEL_AVAILABLE = False

try:
    from opentelemetry import trace
    from opentelemetry.metrics import get_meter

    _OTEL_AVAILABLE = True
except ImportError:
    pass


# ---------------------------------------------------------------------------
# Tracer singleton
# ---------------------------------------------------------------------------

_SERVICE_NAME = "communication-agent"


def _get_tracer() -> Any:
    """Return an OTel tracer or a no-op stub."""
    if _OTEL_AVAILABLE:
        return trace.get_tracer(_SERVICE_NAME)
    return _NoOpTracer()


class _NoOpSpan:
    """Minimal stand-in when OTel is absent."""

    def set_attribute(self, key: str, value: Any) -> None:
        pass

    def set_status(self, status: Any, description: str | None = None) -> None:
        pass

    def record_exception(self, exc: BaseException) -> None:
        pass

    def add_event(self, name: str, attributes: dict | None = None) -> None:
        pass

    def __enter__(self) -> _NoOpSpan:
        return self

    def __exit__(self, *args: Any) -> None:
        pass


class _NoOpTracer:
    """Stub tracer that yields _NoOpSpan."""

    def start_as_current_span(self, name: str, **kwargs: Any) -> _NoOpSpan:
        return _NoOpSpan()


# ---------------------------------------------------------------------------
# Meter (metrics) singleton
# ---------------------------------------------------------------------------


class _NoOpCounter:
    def add(self, amount: int | float, attributes: dict | None = None) -> None:
        pass


class _NoOpHistogram:
    def record(self, amount: int | float, attributes: dict | None = None) -> None:
        pass


class _NoOpGauge:
    def set(self, amount: int | float, attributes: dict | None = None) -> None:
        pass


class _NoOpMeter:
    def create_counter(self, name: str, **kwargs: Any) -> _NoOpCounter:
        return _NoOpCounter()

    def create_histogram(self, name: str, **kwargs: Any) -> _NoOpHistogram:
        return _NoOpHistogram()

    def create_up_down_counter(self, name: str, **kwargs: Any) -> _NoOpCounter:
        return _NoOpCounter()


def _get_meter() -> Any:
    """Return an OTel meter or a no-op stub."""
    if _OTEL_AVAILABLE:
        return get_meter(_SERVICE_NAME)
    return _NoOpMeter()


# ---------------------------------------------------------------------------
# Metrics instances (23 metrics per contracts/telemetry.md)
# ---------------------------------------------------------------------------

_meter = _get_meter()

# Processing metrics
alert_draft_latency = _meter.create_histogram(
    "communication.alert_draft_latency",
    unit="ms",
    description="Time to draft alert in all languages",
)
translation_latency = _meter.create_histogram(
    "communication.translation_latency",
    unit="ms",
    description="Time per language translation",
)
content_safety_check_latency = _meter.create_histogram(
    "communication.content_safety_check_latency",
    unit="ms",
    description="Time for content safety validation",
)
pipeline_total_latency = _meter.create_histogram(
    "communication.pipeline_total_latency",
    unit="ms",
    description="Total pipeline processing time",
)
end_to_end_latency = _meter.create_histogram(
    "communication.end_to_end_latency",
    unit="ms",
    description="End-to-end latency from handoff to delivery",
)

# Approval metrics
approval_wait_time = _meter.create_histogram(
    "communication.approval_wait_time",
    unit="s",
    description="Time waiting for commander approval",
)
approval_notification_latency = _meter.create_histogram(
    "communication.approval_notification_latency",
    unit="ms",
    description="Time to send approval notification",
)
escalation_count = _meter.create_counter(
    "communication.escalation_count",
    description="Number of escalations triggered",
)

# Delivery metrics
delivery_latency_per_channel = _meter.create_histogram(
    "communication.delivery_latency",
    unit="ms",
    description="Per-channel delivery latency",
)
delivery_success_rate = _meter.create_counter(
    "communication.delivery_success_count",
    description="Successful deliveries per channel",
)
delivery_failure_count = _meter.create_counter(
    "communication.delivery_failure_count",
    description="Failed deliveries per channel",
)
sms_segment_count = _meter.create_histogram(
    "communication.sms_segment_count",
    description="Number of SMS segments per message",
)

# Quality metrics
back_translation_quality = _meter.create_histogram(
    "communication.back_translation_quality",
    description="Back-translation cosine similarity score",
)
template_fallback_rate = _meter.create_counter(
    "communication.template_fallback_count",
    description="Number of template fallbacks used",
)
content_safety_failure_rate = _meter.create_counter(
    "communication.content_safety_failure_count",
    description="Number of content safety failures",
)

# Operational metrics
active_alerts_count = _meter.create_up_down_counter(
    "communication.active_alerts",
    description="Currently active alerts",
)
audience_segment_count = _meter.create_histogram(
    "communication.audience_segment_count",
    description="Number of audience segments per alert",
)
pending_approvals = _meter.create_up_down_counter(
    "communication.pending_approvals",
    description="Alerts awaiting commander approval",
)
processing_queue_depth = _meter.create_histogram(
    "communication.processing_queue_depth",
    description="Queue depth at processing time",
)

# Degradation metrics
llm_fallback_active = _meter.create_up_down_counter(
    "communication.llm_fallback_active",
    description="Whether LLM fallback is currently active",
)
channel_degraded = _meter.create_up_down_counter(
    "communication.channel_degraded",
    description="Number of degraded delivery channels",
)
audit_tier_gauge = _meter.create_up_down_counter(
    "communication.audit_tier",
    description="Current audit storage tier (1=cosmos, 2=memory, 3=file)",
)
embedding_service_available = _meter.create_up_down_counter(
    "communication.embedding_service_available",
    description="Whether embedding service is available",
)

# LLM metrics (spec-014)
llm_call_count = _meter.create_counter("llm.call.count", description="Total LLM API calls", unit="calls")
llm_call_duration = _meter.create_histogram("llm.call.duration_ms", description="LLM call latency", unit="ms")
llm_tokens_input = _meter.create_counter(
    "llm.tokens.input",
    description="Cumulative input tokens consumed",
    unit="tokens",
)
llm_tokens_output = _meter.create_counter(
    "llm.tokens.output",
    description="Cumulative output tokens consumed",
    unit="tokens",
)
llm_fallback_count = _meter.create_counter("llm.fallback.count", description="LLM fallback events", unit="events")
llm_error_count = _meter.create_counter("llm.error.count", description="LLM error events", unit="events")
llm_circuit_breaker_state_change = _meter.create_counter(
    "llm.circuit_breaker.state_change",
    description="Circuit breaker state transitions",
    unit="events",
)
llm_budget_exceeded = _meter.create_counter(
    "llm.budget.exceeded",
    description="Monthly budget threshold breaches",
    unit="events",
)
llm_confidence_below_threshold = _meter.create_counter(
    "llm.confidence.below_threshold",
    description="Outputs flagged for human review",
    unit="events",
)


# ---------------------------------------------------------------------------
# Convenience: metrics namespace
# ---------------------------------------------------------------------------


class metrics:
    """Namespace for all Communication Agent metrics."""

    alert_draft_latency = alert_draft_latency
    translation_latency = translation_latency
    content_safety_check_latency = content_safety_check_latency
    pipeline_total_latency = pipeline_total_latency
    end_to_end_latency = end_to_end_latency
    approval_wait_time = approval_wait_time
    approval_notification_latency = approval_notification_latency
    escalation_count = escalation_count
    delivery_latency_per_channel = delivery_latency_per_channel
    delivery_success_rate = delivery_success_rate
    delivery_failure_count = delivery_failure_count
    sms_segment_count = sms_segment_count
    back_translation_quality = back_translation_quality
    template_fallback_rate = template_fallback_rate
    content_safety_failure_rate = content_safety_failure_rate
    active_alerts_count = active_alerts_count
    audience_segment_count = audience_segment_count
    pending_approvals = pending_approvals
    processing_queue_depth = processing_queue_depth
    llm_fallback_active = llm_fallback_active
    channel_degraded = channel_degraded
    audit_tier_gauge = audit_tier_gauge
    embedding_service_available = embedding_service_available
    llm_call_count = llm_call_count
    llm_call_duration = llm_call_duration
    llm_tokens_input = llm_tokens_input
    llm_tokens_output = llm_tokens_output
    llm_fallback_count = llm_fallback_count
    llm_error_count = llm_error_count
    llm_circuit_breaker_state_change = llm_circuit_breaker_state_change
    llm_budget_exceeded = llm_budget_exceeded
    llm_confidence_below_threshold = llm_confidence_below_threshold


# ---------------------------------------------------------------------------
# Span helper
# ---------------------------------------------------------------------------


@contextmanager
def pipeline_span(name: str, attributes: dict[str, Any] | None = None) -> Generator[Any, None, None]:
    """Context manager for pipeline stage spans."""
    tracer = _get_tracer()
    with tracer.start_as_current_span(name) as span:
        if attributes:
            for k, v in attributes.items():
                span.set_attribute(k, v)
        yield span


# ---------------------------------------------------------------------------
# Custom Event Emitter (17 events per contracts/telemetry.md)
# ---------------------------------------------------------------------------


class CustomEventEmitter:
    """Emit custom events via span events or logging."""

    @staticmethod
    def emit(event_name: str, attributes: dict[str, Any] | None = None) -> None:
        """Emit a custom event."""
        if _OTEL_AVAILABLE:
            span = trace.get_current_span()
            if span and hasattr(span, "add_event"):
                span.add_event(event_name, attributes=attributes or {})
        logger.info("CustomEvent: %s %s", event_name, attributes or {})

    # Convenience methods for all 17 custom events
    @staticmethod
    def handoff_received(handoff_id: str, incident_id: str, **kwargs: Any) -> None:
        CustomEventEmitter.emit("HandoffReceived", {"handoff_id": handoff_id, "incident_id": incident_id, **kwargs})

    @staticmethod
    def handoff_rejected(handoff_id: str, reason: str, **kwargs: Any) -> None:
        CustomEventEmitter.emit("HandoffRejected", {"handoff_id": handoff_id, "reason": reason, **kwargs})

    @staticmethod
    def duplicate_discarded(handoff_id: str, **kwargs: Any) -> None:
        CustomEventEmitter.emit("DuplicateDiscarded", {"handoff_id": handoff_id, **kwargs})

    @staticmethod
    def alert_drafted(alert_id: str, languages: int, **kwargs: Any) -> None:
        CustomEventEmitter.emit("AlertDrafted", {"alert_id": alert_id, "language_count": languages, **kwargs})

    @staticmethod
    def back_translation_flagged(alert_id: str, language: str, score: float, **kwargs: Any) -> None:
        CustomEventEmitter.emit(
            "BackTranslationFlagged", {"alert_id": alert_id, "language": language, "score": score, **kwargs}
        )

    @staticmethod
    def content_safety_failed(alert_id: str, language: str, reason: str, **kwargs: Any) -> None:
        CustomEventEmitter.emit(
            "ContentSafetyFailed", {"alert_id": alert_id, "language": language, "reason": reason, **kwargs}
        )

    @staticmethod
    def alert_version_created(alert_id: str, version: int, change_type: str, **kwargs: Any) -> None:
        CustomEventEmitter.emit(
            "AlertVersionCreated", {"alert_id": alert_id, "version": version, "change_type": change_type, **kwargs}
        )

    @staticmethod
    def approval_requested(alert_id: str, **kwargs: Any) -> None:
        CustomEventEmitter.emit("ApprovalRequested", {"alert_id": alert_id, **kwargs})

    @staticmethod
    def escalation_triggered(alert_id: str, level: int, **kwargs: Any) -> None:
        CustomEventEmitter.emit("EscalationTriggered", {"alert_id": alert_id, "level": level, **kwargs})

    @staticmethod
    def escalation_exhausted(alert_id: str, **kwargs: Any) -> None:
        CustomEventEmitter.emit("EscalationExhausted", {"alert_id": alert_id, **kwargs})

    @staticmethod
    def delivery_started(alert_id: str, channel: str, **kwargs: Any) -> None:
        CustomEventEmitter.emit("DeliveryStarted", {"alert_id": alert_id, "channel": channel, **kwargs})

    @staticmethod
    def delivery_completed(alert_id: str, channel: str, **kwargs: Any) -> None:
        CustomEventEmitter.emit("DeliveryCompleted", {"alert_id": alert_id, "channel": channel, **kwargs})

    @staticmethod
    def delivery_failed(alert_id: str, channel: str, reason: str, **kwargs: Any) -> None:
        CustomEventEmitter.emit(
            "DeliveryFailed", {"alert_id": alert_id, "channel": channel, "reason": reason, **kwargs}
        )

    @staticmethod
    def delivery_deduplicated(alert_id: str, segment_id: str, winner_id: str, **kwargs: Any) -> None:
        CustomEventEmitter.emit(
            "DeliveryDeduplicated", {"alert_id": alert_id, "segment_id": segment_id, "winner_id": winner_id, **kwargs}
        )

    @staticmethod
    def degradation_detected(service: str, fallback: str, **kwargs: Any) -> None:
        CustomEventEmitter.emit("DegradationDetected", {"service": service, "fallback": fallback, **kwargs})

    @staticmethod
    def degradation_recovered(service: str, downtime_ms: int = 0, **kwargs: Any) -> None:
        CustomEventEmitter.emit("DegradationRecovered", {"service": service, "downtime_ms": downtime_ms, **kwargs})

    @staticmethod
    def template_file_missing(language: str, hazard_type: str, **kwargs: Any) -> None:
        CustomEventEmitter.emit("TemplateFileMissing", {"language": language, "hazard_type": hazard_type, **kwargs})
