"""OpenTelemetry distributed tracing, metrics, and custom events for Resource Allocation Agent.

Implements contracts/telemetry.md:
- Span hierarchy for 9-stage pipeline
- Processing, matching, cross-incident, override, degradation, lifecycle metrics
- Custom events (HandoffReceived, PlanGenerated, ShortfallDetected, etc.)

All instrumentation is opt-in: when ``opentelemetry`` is not installed, the
module exports no-op stubs so production code runs without instrumentation
overhead.
"""

from __future__ import annotations

import logging
from typing import Any

from common.telemetry_types import Attributes

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Detect OpenTelemetry availability
# ---------------------------------------------------------------------------

_OTEL_AVAILABLE = False

try:
    from opentelemetry import trace
    from opentelemetry.metrics import get_meter
    from opentelemetry.trace import StatusCode  # noqa: F401

    _OTEL_AVAILABLE = True
except ImportError:
    pass


# ---------------------------------------------------------------------------
# Tracer singleton
# ---------------------------------------------------------------------------

_SERVICE_NAME = "resource-allocation-agent"


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

    def add_event(self, name: str, attributes: Attributes | None = None) -> None:  # noqa: D102
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
# Public tracer access
# ---------------------------------------------------------------------------

tracer = _get_tracer()


# ---------------------------------------------------------------------------
# Metrics singleton
# ---------------------------------------------------------------------------


class ResourceAllocationMetrics:
    """Central metrics registry per contracts/telemetry.md."""

    def __init__(self) -> None:
        if _OTEL_AVAILABLE:
            meter = get_meter(_SERVICE_NAME)

            # Processing metrics
            self.allocation_latency = meter.create_histogram(
                "resource_allocation.allocation_latency",
                unit="ms",
                description="End-to-end processing time per handoff",
            )
            self.plan_count = meter.create_counter(
                "resource_allocation.plan_count",
                description="Total plans generated",
            )
            self.handoff_intake_count = meter.create_counter(
                "resource_allocation.handoff_intake_count",
                description="Total handoffs received",
            )
            self.handoff_rejected_count = meter.create_counter(
                "resource_allocation.handoff_rejected_count",
                description="Handoffs rejected",
            )
            self.duplicate_discard_count = meter.create_counter(
                "resource_allocation.duplicate_discard_count",
                description="Duplicate handoffs discarded",
            )
            self.sla_breach_count = meter.create_counter(
                "resource_allocation.sla_breach_count",
                description="Plans exceeding 15-second SLA",
            )
            self.status_update_latency = meter.create_histogram(
                "resource_allocation.status_update_latency",
                unit="ms",
                description="Status update processing time",
            )

            # Matching metrics
            self.resource_matching_time = meter.create_histogram(
                "resource_allocation.resource_matching_time",
                unit="ms",
                description="Time spent matching resources to demands",
            )
            self.demand_fulfilment_rate = meter.create_histogram(
                "resource_allocation.demand_fulfilment_rate",
                unit="ratio",
                description="Ratio of fulfilled demands to total demands",
            )
            self.shortfall_count = meter.create_counter(
                "resource_allocation.shortfall_count",
                description="Total shortfall items generated",
            )
            self.resource_utilization_rate = meter.create_histogram(
                "resource_allocation.resource_utilization_rate",
                unit="ratio",
                description="Resource utilization ratio",
            )
            self.unmet_demand_count = meter.create_counter(
                "resource_allocation.unmet_demand_count",
                description="Total unmet demands",
            )

            # Cross-incident metrics
            self.cross_incident_conflicts = meter.create_counter(
                "resource_allocation.cross_incident_conflicts",
                description="Cross-incident resource contention events",
            )
            self.cross_incident_reallocation_count = meter.create_counter(
                "resource_allocation.cross_incident_reallocation_count",
                description="Reallocation recommendations generated",
            )
            self.cross_incident_analysis_latency = meter.create_histogram(
                "resource_allocation.cross_incident_analysis_latency",
                unit="ms",
                description="Cross-incident analysis processing time",
            )

            # Override metrics
            self.override_count = meter.create_counter(
                "resource_allocation.override_count",
                description="Total commander overrides applied",
            )
            self.override_rate = meter.create_histogram(
                "resource_allocation.override_rate",
                unit="ratio",
                description="Ratio of overridden plans to total plans",
            )
            self.plan_approval_latency = meter.create_histogram(
                "resource_allocation.plan_approval_latency",
                unit="ms",
                description="Time from plan generation to approval",
            )

            # Degradation metrics
            self.fallback_mode_activations = meter.create_counter(
                "resource_allocation.fallback_mode_activations",
                description="Template fallback activations",
            )
            self.content_safety_failures = meter.create_counter(
                "resource_allocation.content_safety_failures",
                description="LLM outputs failing content safety",
            )
            self.audit_buffer_depth = meter.create_up_down_counter(
                "resource_allocation.audit_buffer_depth",
                description="Current in-memory audit buffer depth",
            )
            self.audit_tier = meter.create_up_down_counter(
                "resource_allocation.audit_tier",
                description="Current audit write tier (1=cosmos, 2=memory, 3=file)",
            )
            self.degradation_events = meter.create_counter(
                "resource_allocation.degradation_events",
                description="Total degradation events detected",
            )

            # Lifecycle metrics
            self.plan_versions_per_incident = meter.create_up_down_counter(
                "resource_allocation.plan_versions_per_incident",
                description="Plan versions per incident",
            )
            self.version_conflict_retries = meter.create_counter(
                "resource_allocation.version_conflict_retries",
                description="Optimistic concurrency retries",
            )
            self.active_plans_gauge = meter.create_up_down_counter(
                "resource_allocation.active_plans_gauge",
                description="Current active (non-expired, non-rejected) plans",
            )
            self.plan_expired_count = meter.create_counter(
                "resource_allocation.plan_expired_count",
                description="Total plans expired",
            )
            self.transport_dispatch_latency = meter.create_histogram(
                "resource_allocation.transport_dispatch_latency",
                unit="ms",
                description="Transport dispatch processing time",
            )
            self.handoff_success_rate = meter.create_up_down_counter(
                "resource_allocation.handoff_success_rate",
                description="Delivered vs dead-lettered handoff ratio",
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
                "allocation_latency",
                "plan_count",
                "handoff_intake_count",
                "handoff_rejected_count",
                "duplicate_discard_count",
                "sla_breach_count",
                "status_update_latency",
                "resource_matching_time",
                "demand_fulfilment_rate",
                "shortfall_count",
                "resource_utilization_rate",
                "unmet_demand_count",
                "cross_incident_conflicts",
                "cross_incident_reallocation_count",
                "cross_incident_analysis_latency",
                "override_count",
                "override_rate",
                "plan_approval_latency",
                "fallback_mode_activations",
                "content_safety_failures",
                "audit_buffer_depth",
                "audit_tier",
                "degradation_events",
                "plan_versions_per_incident",
                "version_conflict_retries",
                "active_plans_gauge",
                "plan_expired_count",
                "transport_dispatch_latency",
                "handoff_success_rate",
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

    def record_allocation_latency(self, latency_ms: float) -> None:
        """Record end-to-end processing latency."""
        self.allocation_latency.record(latency_ms)

    def inc_plan_count(self) -> None:
        self.plan_count.add(1)

    def inc_handoff_intake(self) -> None:
        self.handoff_intake_count.add(1)

    def inc_handoff_rejected(self) -> None:
        self.handoff_rejected_count.add(1)

    def inc_duplicate_discard(self) -> None:
        self.duplicate_discard_count.add(1)

    def inc_sla_breach(self) -> None:
        self.sla_breach_count.add(1)

    def inc_fallback(self) -> None:
        self.fallback_mode_activations.add(1)

    def inc_content_safety_failure(self) -> None:
        self.content_safety_failures.add(1)

    def inc_version_conflict_retry(self) -> None:
        self.version_conflict_retries.add(1)

    def inc_override(self) -> None:
        self.override_count.add(1)

    def inc_shortfall(self) -> None:
        self.shortfall_count.add(1)

    def inc_cross_incident_conflict(self) -> None:
        self.cross_incident_conflicts.add(1)

    def inc_degradation_event(self) -> None:
        self.degradation_events.add(1)

    def inc_plan_expired(self) -> None:
        self.plan_expired_count.add(1)

    def record_confidence(self, score: float) -> None:
        self.demand_fulfilment_rate.record(score)


class _NoOpMetric:
    """Drop-in stub for any metric type."""

    def add(self, value: Any = 1, attributes: Attributes | None = None) -> None:  # noqa: D102
        pass

    def record(self, value: Any = 0, attributes: Attributes | None = None) -> None:  # noqa: D102
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
        cls,
        handoff_id: str,
        incident_id: str,
        tenant_id: str,
    ) -> None:
        cls._emit(
            "HandoffReceived",
            {
                "handoff_id": handoff_id,
                "incident_id": incident_id,
                "tenant_id": tenant_id,
            },
        )

    @classmethod
    def plan_generated(
        cls,
        plan_id: str,
        confidence: float,
        generation_method: str,
        assignment_count: int,
        shortfall_count: int,
    ) -> None:
        cls._emit(
            "PlanGenerated",
            {
                "plan_id": plan_id,
                "confidence": confidence,
                "generation_method": generation_method,
                "assignment_count": assignment_count,
                "shortfall_count": shortfall_count,
            },
        )

    @classmethod
    def shortfall_detected(
        cls,
        plan_id: str,
        demand_id: str,
        resource_type: str,
        quantity_unmet: int,
    ) -> None:
        cls._emit(
            "ShortfallDetected",
            {
                "plan_id": plan_id,
                "demand_id": demand_id,
                "resource_type": resource_type,
                "quantity_unmet": quantity_unmet,
            },
        )

    @classmethod
    def cross_incident_conflict(
        cls,
        resource_id: str,
        incident_ids: list[str],
    ) -> None:
        cls._emit(
            "CrossIncidentConflict",
            {
                "resource_id": resource_id,
                "incident_ids": ",".join(incident_ids),
            },
        )

    @classmethod
    def reallocation_recommended(
        cls,
        plan_id: str,
        from_incident: str,
        to_incident: str,
        resource_id: str,
    ) -> None:
        cls._emit(
            "ReallocationRecommended",
            {
                "plan_id": plan_id,
                "from_incident": from_incident,
                "to_incident": to_incident,
                "resource_id": resource_id,
            },
        )

    @classmethod
    def override_applied(
        cls,
        plan_id: str,
        action: str,
        user_id: str,
        role: str,
    ) -> None:
        cls._emit(
            "OverrideApplied",
            {
                "plan_id": plan_id,
                "action": action,
                "user_id": user_id,
                "role": role,
            },
        )

    @classmethod
    def plan_expired(cls, plan_id: str, incident_id: str) -> None:
        cls._emit(
            "PlanExpired",
            {
                "plan_id": plan_id,
                "incident_id": incident_id,
            },
        )

    @classmethod
    def degradation_event(
        cls,
        component: str,
        fallback: str,
        reason: str,
    ) -> None:
        cls._emit(
            "DegradationEvent",
            {
                "component": component,
                "fallback": fallback,
                "reason": reason,
            },
        )

    @classmethod
    def sla_breach(
        cls,
        handoff_id: str,
        processing_time_ms: float,
        sla_threshold_ms: float = 15000,
    ) -> None:
        cls._emit(
            "SLABreach",
            {
                "handoff_id": handoff_id,
                "processing_time_ms": processing_time_ms,
                "sla_threshold_ms": sla_threshold_ms,
            },
        )

    @classmethod
    def version_conflict(
        cls,
        incident_id: str,
        retry_count: int,
    ) -> None:
        cls._emit(
            "VersionConflict",
            {
                "incident_id": incident_id,
                "retry_count": retry_count,
            },
        )


# ---------------------------------------------------------------------------
# Module-level singletons
# ---------------------------------------------------------------------------

metrics = ResourceAllocationMetrics()
events = CustomEventEmitter
