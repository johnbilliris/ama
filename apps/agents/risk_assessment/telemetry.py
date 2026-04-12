"""OpenTelemetry distributed tracing, metrics, and custom events.

Implements contracts/telemetry.md:
- Span hierarchy for 8-stage pipeline
- 20 metrics (processing, escalation, quality, degradation, version)
- 7 custom events

All instrumentation is opt-in: when ``opentelemetry`` is not installed, the
module exports no-op stubs so production code runs without instrumentation
overhead.
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

_SERVICE_NAME = "risk-assessment-agent"


def _get_tracer() -> Any:
    """Return an OTel tracer or a no-op stub."""
    if _OTEL_AVAILABLE:
        return trace.get_tracer(_SERVICE_NAME)
    return _NoOpTracer()


class _NoOpSpan:
    """Minimal stand-in when OTel is absent."""

    def set_attribute(self, key: str, value: Any) -> None:  # noqa: D102
        pass

    def set_status(self, status: Any, description: str | None = None) -> None:  # noqa: D102
        pass

    def record_exception(self, exc: BaseException) -> None:  # noqa: D102
        pass

    def add_event(self, name: str, attributes: dict | None = None) -> None:  # noqa: D102
        pass

    def __enter__(self) -> _NoOpSpan:  # noqa: D105
        return self

    def __exit__(self, *args: Any) -> None:  # noqa: D105
        pass


class _NoOpTracer:
    """Stub tracer that yields :class:`_NoOpSpan`."""

    def start_as_current_span(self, name: str, **kwargs: Any) -> _NoOpSpan:  # noqa: D102
        return _NoOpSpan()


# ---------------------------------------------------------------------------
# Metrics singleton
# ---------------------------------------------------------------------------


class RiskAssessmentMetrics:
    """Central metrics registry per contracts/telemetry.md."""

    def __init__(self) -> None:
        if _OTEL_AVAILABLE:
            meter = get_meter(_SERVICE_NAME)

            # Processing metrics
            self.assessment_latency = meter.create_histogram(
                "risk_assessment.assessment_latency",
                unit="ms",
                description="End-to-end processing time per handoff",
            )
            self.assessment_count = meter.create_counter(
                "risk_assessment.assessment_count",
                description="Total assessments generated",
            )
            self.handoff_intake_count = meter.create_counter(
                "risk_assessment.handoff_intake_count",
                description="Total handoffs received",
            )
            self.handoff_rejected_count = meter.create_counter(
                "risk_assessment.handoff_rejected_count",
                description="Handoffs rejected",
            )
            self.duplicate_discard_count = meter.create_counter(
                "risk_assessment.duplicate_discard_count",
                description="Duplicate handoffs discarded",
            )
            self.sla_breach_count = meter.create_counter(
                "risk_assessment.sla_breach_count",
                description="Assessments exceeding 10-second SLA",
            )

            # Escalation metrics
            self.escalation_rate_by_type = meter.create_counter(
                "risk_assessment.escalation_rate_by_type",
                description="Downstream handoffs created, tagged by target_agent",
            )
            self.handoff_success_rate = meter.create_up_down_counter(
                "risk_assessment.handoff_success_rate",
                description="Delivered vs dead-lettered handoff ratio",
            )
            self.dead_letter_count = meter.create_counter(
                "risk_assessment.dead_letter_count",
                description="Handoffs permanently failed",
            )

            # Quality metrics
            self.contradiction_detection_rate = meter.create_up_down_counter(
                "risk_assessment.contradiction_detection_rate",
                description="Percentage of assessments with contradictions",
            )
            self.confidence_distribution = meter.create_histogram(
                "risk_assessment.confidence_distribution",
                unit="score",
                description="Distribution of final adjusted confidence scores",
            )
            self.severity_distribution = meter.create_counter(
                "risk_assessment.severity_distribution",
                description="Assessments by severity level",
            )
            self.stale_signal_rate = meter.create_up_down_counter(
                "risk_assessment.stale_signal_rate",
                description="Percentage of signals below freshness threshold",
            )

            # Degradation metrics
            self.fallback_mode_activations = meter.create_counter(
                "risk_assessment.fallback_mode_activations",
                description="Template fallback activations",
            )
            self.content_safety_failures = meter.create_counter(
                "risk_assessment.content_safety_failures",
                description="LLM outputs failing content safety",
            )
            self.audit_buffer_depth = meter.create_up_down_counter(
                "risk_assessment.audit_buffer_depth",
                description="Current in-memory audit buffer depth",
            )
            self.audit_tier = meter.create_up_down_counter(
                "risk_assessment.audit_tier",
                description="Current audit write tier (1=cosmos, 2=memory, 3=file)",
            )

            # Version metrics
            self.version_count_per_incident = meter.create_up_down_counter(
                "risk_assessment.version_count_per_incident",
                description="Assessment versions per incident",
            )
            self.version_conflict_retries = meter.create_counter(
                "risk_assessment.version_conflict_retries",
                description="Optimistic concurrency retries",
            )

            # LLM metrics (spec-014)
            self.llm_call_count = meter.create_counter(
                "llm.call.count",
                description="Total LLM API calls",
                unit="calls",
            )
            self.llm_call_duration = meter.create_histogram(
                "llm.call.duration_ms",
                description="LLM call latency",
                unit="ms",
            )
            self.llm_tokens_input = meter.create_counter(
                "llm.tokens.input",
                description="Cumulative input tokens consumed",
                unit="tokens",
            )
            self.llm_tokens_output = meter.create_counter(
                "llm.tokens.output",
                description="Cumulative output tokens consumed",
                unit="tokens",
            )
            self.llm_fallback_count = meter.create_counter(
                "llm.fallback.count",
                description="LLM fallback events",
                unit="events",
            )
            self.llm_error_count = meter.create_counter(
                "llm.error.count",
                description="LLM error events",
                unit="events",
            )
            self.llm_circuit_breaker_state_change = meter.create_counter(
                "llm.circuit_breaker.state_change",
                description="Circuit breaker state transitions",
                unit="events",
            )
            self.llm_budget_exceeded = meter.create_counter(
                "llm.budget.exceeded",
                description="Monthly budget threshold breaches",
                unit="events",
            )
            self.llm_confidence_below_threshold = meter.create_counter(
                "llm.confidence.below_threshold",
                description="Outputs flagged for human review",
                unit="events",
            )
        else:
            # Assign no-op attributes so callers never need to guard
            for attr in (
                "assessment_latency",
                "assessment_count",
                "handoff_intake_count",
                "handoff_rejected_count",
                "duplicate_discard_count",
                "sla_breach_count",
                "escalation_rate_by_type",
                "handoff_success_rate",
                "dead_letter_count",
                "contradiction_detection_rate",
                "confidence_distribution",
                "severity_distribution",
                "stale_signal_rate",
                "fallback_mode_activations",
                "content_safety_failures",
                "audit_buffer_depth",
                "audit_tier",
                "version_count_per_incident",
                "version_conflict_retries",
                "llm_call_count",
                "llm_call_duration",
                "llm_tokens_input",
                "llm_tokens_output",
                "llm_fallback_count",
                "llm_error_count",
                "llm_circuit_breaker_state_change",
                "llm_budget_exceeded",
                "llm_confidence_below_threshold",
            ):
                setattr(self, attr, _NoOpMetric())

    # Convenience helpers -------------------------------------------------

    def record_assessment_latency(self, latency_ms: float) -> None:
        """Record end-to-end processing latency."""
        self.assessment_latency.record(latency_ms)

    def inc_assessment_count(self) -> None:
        self.assessment_count.add(1)

    def inc_handoff_intake(self) -> None:
        self.handoff_intake_count.add(1)

    def inc_handoff_rejected(self) -> None:
        self.handoff_rejected_count.add(1)

    def inc_duplicate_discard(self) -> None:
        self.duplicate_discard_count.add(1)

    def inc_sla_breach(self) -> None:
        self.sla_breach_count.add(1)

    def inc_escalation(self, target_agent: str) -> None:
        self.escalation_rate_by_type.add(1, {"target_agent": target_agent})

    def inc_dead_letter(self) -> None:
        self.dead_letter_count.add(1)

    def inc_fallback(self) -> None:
        self.fallback_mode_activations.add(1)

    def inc_content_safety_failure(self) -> None:
        self.content_safety_failures.add(1)

    def inc_version_conflict_retry(self) -> None:
        self.version_conflict_retries.add(1)

    def record_confidence(self, score: float) -> None:
        self.confidence_distribution.record(score)

    def record_severity(self, level: str) -> None:
        self.severity_distribution.add(1, {"severity_level": level})


class _NoOpMetric:
    """Drop-in stub for any metric type."""

    def add(self, value: Any = 1, attributes: dict | None = None) -> None:  # noqa: D102
        pass

    def record(self, value: Any = 0, attributes: dict | None = None) -> None:  # noqa: D102
        pass


# ---------------------------------------------------------------------------
# Custom Events
# ---------------------------------------------------------------------------


class CustomEventEmitter:
    """Emit custom events per contracts/telemetry.md §Custom Events.

    When OTel is available, events are added to the current span.
    Otherwise they are logged at INFO level.
    """

    @staticmethod
    def _emit(event_name: str, attributes: dict[str, Any]) -> None:
        if _OTEL_AVAILABLE:
            span = trace.get_current_span()
            if span and hasattr(span, "add_event"):
                span.add_event(event_name, attributes=attributes)
        else:
            logger.info("CustomEvent[%s]: %s", event_name, attributes)

    @classmethod
    def handoff_received(
        cls, handoff_id: str, incident_id: str, tenant_id: str,
    ) -> None:
        cls._emit("HandoffReceived", {
            "handoff_id": handoff_id,
            "incident_id": incident_id,
            "tenant_id": tenant_id,
        })

    @classmethod
    def assessment_generated(
        cls,
        assessment_id: str,
        confidence: float,
        severity: str,
        generation_method: str,
    ) -> None:
        cls._emit("AssessmentGenerated", {
            "assessment_id": assessment_id,
            "confidence": confidence,
            "severity": severity,
            "generation_method": generation_method,
        })

    @classmethod
    def contradiction_detected(
        cls,
        signal_ids: list[str],
        source_names: list[str],
        confidence_reduction: float,
    ) -> None:
        cls._emit("ContradictionDetected", {
            "signal_ids": ",".join(signal_ids),
            "source_names": ",".join(source_names),
            "confidence_reduction": confidence_reduction,
        })

    @classmethod
    def escalation_triggered(
        cls, target_agent: str, recommendation_id: str, confidence: float,
    ) -> None:
        cls._emit("EscalationTriggered", {
            "target_agent": target_agent,
            "recommendation_id": recommendation_id,
            "confidence": confidence,
        })

    @classmethod
    def degradation_event(cls, component: str, tier: int | str) -> None:
        cls._emit("DegradationEvent", {
            "component": component,
            "tier": str(tier),
        })

    @classmethod
    def sla_breach(cls, handoff_id: str, actual_duration_ms: float) -> None:
        cls._emit("SLABreach", {
            "handoff_id": handoff_id,
            "actual_duration_ms": actual_duration_ms,
        })

    @classmethod
    def version_conflict(
        cls, incident_id: str, assessment_type: str, retry_count: int,
    ) -> None:
        cls._emit("VersionConflict", {
            "incident_id": incident_id,
            "assessment_type": assessment_type,
            "retry_count": retry_count,
        })


# ---------------------------------------------------------------------------
# Span helpers (context managers)
# ---------------------------------------------------------------------------


@contextmanager
def pipeline_span(name: str, handoff_id: str = "") -> Generator[Any, None, None]:
    """Open a child span under the current trace context.

    Usage::

        with pipeline_span("risk_assessment.validate_handoff", hid):
            ...
    """
    tracer = _get_tracer()
    span = tracer.start_as_current_span(name)
    with span as s:
        if handoff_id:
            s.set_attribute("handoff_id", handoff_id)
        yield s


# Module-level singletons
metrics = RiskAssessmentMetrics()
events = CustomEventEmitter
