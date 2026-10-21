"""Centralised OpenTelemetry instrumentation for the Evacuation Agent.

Provides:
- ``tracer`` — distributed-tracing tracer (span creation)
- All metric instruments defined in the telemetry contract
- Helper utilities for emitting custom span events

Design notes:
- Uses ``opentelemetry-api`` which provides **no-op** implementations when no
  SDK/exporter is configured.  This means the agent runs identically in tests
  and production — zero overhead when tracing is off.
- If the ``opentelemetry`` package is not installed at all, every public symbol
  in this module gracefully degrades to a lightweight no-op so that call-sites
  never need their own try/except guards.
"""

from __future__ import annotations

import logging
import os
from threading import Lock
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Graceful import — works with or without opentelemetry installed
# ---------------------------------------------------------------------------

try:
    from opentelemetry import metrics as otel_metrics
    from opentelemetry import trace

    _HAS_OTEL = True
except ImportError:  # pragma: no cover
    _HAS_OTEL = False
    trace = None  # type: ignore[assignment]
    otel_metrics = None  # type: ignore[assignment]

# ---------------------------------------------------------------------------
# Tracer & Meter
# ---------------------------------------------------------------------------

_SERVICE_NAME = "evacuation-agent"
_SERVICE_VERSION = "0.1.0"
_TELEMETRY_CONFIGURED = False
_TELEMETRY_CONFIGURATION_LOCK = Lock()


def configure_telemetry() -> bool:
    """Configure authenticated Azure Monitor export once when available."""
    global _TELEMETRY_CONFIGURED
    with _TELEMETRY_CONFIGURATION_LOCK:
        if _TELEMETRY_CONFIGURED:
            return True
        connection_string = os.environ.get(
            "APPLICATIONINSIGHTS_CONNECTION_STRING",
            "",
        )
        if not connection_string:
            return False
        try:
            from azure.identity import DefaultAzureCredential
            from azure.monitor.opentelemetry import configure_azure_monitor

            client_id = os.environ.get("AZURE_CLIENT_ID")
            credential = (
                DefaultAzureCredential(managed_identity_client_id=client_id) if client_id else DefaultAzureCredential()
            )
            configure_azure_monitor(
                connection_string=connection_string,
                credential=credential,
                resource_attributes={
                    "service.name": _SERVICE_NAME,
                    "service.version": _SERVICE_VERSION,
                },
            )
        except Exception:
            logger.exception("Evacuation telemetry exporter configuration failed")
            return False
        _TELEMETRY_CONFIGURED = True
        return True


if _HAS_OTEL:
    tracer = trace.get_tracer(_SERVICE_NAME, _SERVICE_VERSION)
    meter = otel_metrics.get_meter(_SERVICE_NAME, _SERVICE_VERSION)
else:  # pragma: no cover
    tracer = None  # type: ignore[assignment]
    meter = None  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# No-op helpers when OTel is absent
# ---------------------------------------------------------------------------


class _NoOpInstrument:
    """Silently swallows any call — stands in for Counter / Histogram / etc."""

    def add(self, *a: Any, **kw: Any) -> None:  # noqa: D401
        pass

    def record(self, *a: Any, **kw: Any) -> None:  # noqa: D401
        pass


_NOOP = _NoOpInstrument()


class _GaugeTracker:
    """Wrap an ``UpDownCounter`` to give set-value semantics.

    ``UpDownCounter`` only supports ``add(delta)``; this helper tracks the
    previous value so callers can simply ``gauge.set(new_value, attributes)``.
    """

    def __init__(self, counter: Any) -> None:
        self._counter = counter
        self._values: dict[str, float] = {}  # keyed by sorted-attributes string
        self._lock = Lock()

    # noinspection PyMethodMayBeStatic
    @staticmethod
    def _attr_key(attributes: dict[str, str] | None) -> str:
        if not attributes:
            return ""
        return str(sorted(attributes.items()))

    def set(self, value: float, attributes: dict[str, str] | None = None) -> None:
        key = self._attr_key(attributes)
        with self._lock:
            prev = self._values.get(key, 0.0)
            delta = value - prev
            self._values[key] = value
        self._counter.add(delta, attributes=attributes)

    def add(self, delta: float, attributes: dict[str, str] | None = None) -> None:
        key = self._attr_key(attributes)
        with self._lock:
            self._values[key] = self._values.get(key, 0.0) + delta
        self._counter.add(delta, attributes=attributes)


class _NoOpGauge:
    """No-op stand-in for ``_GaugeTracker``."""

    def set(self, *a: Any, **kw: Any) -> None:
        pass

    def add(self, *a: Any, **kw: Any) -> None:
        pass


# ---------------------------------------------------------------------------
# Metric factory helpers
# ---------------------------------------------------------------------------


def _counter(name: str, description: str, unit: str = "1") -> Any:
    if meter is not None:
        return meter.create_counter(name=name, description=description, unit=unit)
    return _NOOP


def _histogram(name: str, description: str, unit: str = "ms") -> Any:
    if meter is not None:
        return meter.create_histogram(name=name, description=description, unit=unit)
    return _NOOP


def _gauge(name: str, description: str, unit: str = "1") -> _GaugeTracker | _NoOpGauge:
    if meter is not None:
        udc = meter.create_up_down_counter(
            name=name,
            description=description,
            unit=unit,
        )
        return _GaugeTracker(udc)
    return _NoOpGauge()


# ===================================================================
# METRIC INSTRUMENTS  (names from specs/009 telemetry contract)
# ===================================================================

# --- Processing -----------------------------------------------------------
plan_generation_latency = _histogram(
    "evacuation.plan_generation_latency",
    "End-to-end time from handoff receipt to plan persisted",
    unit="ms",
)
route_computation_time = _histogram(
    "evacuation.route_computation_time",
    "Duration of Dijkstra's pathfinding per plan",
    unit="ms",
)
replan_count = _counter(
    "evacuation.replan_count",
    "Number of replans per incident",
)
replan_latency = _histogram(
    "evacuation.replan_latency",
    "Dynamic replanning time",
    unit="ms",
)
handoff_intake_count = _counter(
    "evacuation.handoff_intake_count",
    "Total handoffs received",
)
handoff_rejected_count = _counter(
    "evacuation.handoff_rejected_count",
    "Handoffs rejected (invalid, missing assessment)",
)
duplicate_discard_count = _counter(
    "evacuation.duplicate_discard_count",
    "Duplicate handoffs discarded",
)
sla_breach_count = _counter(
    "evacuation.sla_breach_count",
    "Plans exceeding 30-second SLA",
)
replan_sla_breach_count = _counter(
    "evacuation.replan_sla_breach_count",
    "Replans exceeding 15-second SLA",
)
handoff_acknowledgement_latency = _histogram(
    "evacuation.handoff_acknowledgement_latency",
    "Time from broker receive to validated handoff acknowledgement",
)

# --- Safety ---------------------------------------------------------------
shelter_in_place_count = _counter(
    "evacuation.shelter_in_place_count",
    "Shelter-in-place recommendations issued",
)
shelter_to_evacuation_recovery_count = _counter(
    "evacuation.shelter_to_evacuation_recovery_count",
    "Transitions from shelter-in-place back to evacuation",
)
emergency_escalation_count = _counter(
    "evacuation.emergency_escalation_count",
    "Emergency escalations (no route + immediate threat)",
)
time_deficit_flag_count = _counter(
    "evacuation.time_deficit_flag_count",
    "Plans where clearance time exceeds hazard arrival window",
)

# --- Transport ------------------------------------------------------------
transport_requests_generated = _counter(
    "evacuation.transport_requests_generated",
    "TransportRequirement records created",
)
transport_by_category = _counter(
    "evacuation.transport_by_category",
    "Transport requests by vulnerability category (tagged)",
)
transport_vehicles_estimated = _gauge(
    "evacuation.transport_vehicles_estimated",
    "Total estimated vehicles needed across active plans",
)

# --- Zone & Population ----------------------------------------------------
zone_population_covered = _gauge(
    "evacuation.zone_population_covered",
    "Population estimate per zone in active plans (tagged by zone)",
)
active_plans_gauge = _gauge(
    "evacuation.active_plans_gauge",
    "Current number of active non-superseded plans",
)
routes_per_plan = _histogram(
    "evacuation.routes_per_plan",
    "Number of evacuation routes per plan",
    unit="1",
)
congestion_risk_routes = _counter(
    "evacuation.congestion_risk_routes",
    "Routes flagged as congestion-risk (>80% utilisation)",
)

# --- Override & Dynamic Update --------------------------------------------
dynamic_update_rate = _gauge(
    "evacuation.dynamic_update_rate",
    "Plan versions per incident (tagged by incident_id)",
)
override_rate = _gauge(
    "evacuation.override_rate",
    "Percentage of plans modified by commanders",
    unit="ratio",
)
override_by_type = _counter(
    "evacuation.override_by_type",
    "Overrides by action type (tagged)",
)

# --- Degradation ----------------------------------------------------------
fallback_mode_activations = _counter(
    "evacuation.fallback_mode_activations",
    "Template fallback activations (LLM unavailable)",
)
content_safety_failures = _counter(
    "evacuation.content_safety_failures",
    "LLM outputs failing content safety",
)
audit_buffer_depth = _gauge(
    "evacuation.audit_buffer_depth",
    "Current in-memory audit buffer depth",
)
audit_tier = _gauge(
    "evacuation.audit_tier",
    "Current audit write tier (1=cosmos, 2=memory, 3=file)",
)
road_data_stale = _gauge(
    "evacuation.road_data_stale",
    "Whether road network data exceeds staleness window",
)
degradation_events = _counter(
    "evacuation.degradation_events",
    "Total degradation events per time window",
)

# --- Version --------------------------------------------------------------
version_count_per_incident = _gauge(
    "evacuation.version_count_per_incident",
    "Plan versions per incident (tagged by incident_id)",
)
version_conflict_retries = _counter(
    "evacuation.version_conflict_retries",
    "Optimistic concurrency retries",
)

# --- LLM metrics (spec-014) -----------------------------------------------
llm_call_count = _counter("llm.call.count", "Total LLM API calls", unit="calls")
llm_call_duration = _histogram("llm.call.duration_ms", "LLM call latency", unit="ms")
llm_tokens_input = _counter("llm.tokens.input", "Cumulative input tokens consumed", unit="tokens")
llm_tokens_output = _counter("llm.tokens.output", "Cumulative output tokens consumed", unit="tokens")
llm_fallback_count = _counter("llm.fallback.count", "LLM fallback events", unit="events")
llm_error_count = _counter("llm.error.count", "LLM error events", unit="events")
llm_circuit_breaker_state_change = _counter(
    "llm.circuit_breaker.state_change",
    "Circuit breaker state transitions",
    unit="events",
)
llm_budget_exceeded = _counter("llm.budget.exceeded", "Monthly budget threshold breaches", unit="events")
llm_confidence_below_threshold = _counter(
    "llm.confidence.below_threshold",
    "Outputs flagged for human review",
    unit="events",
)

# --- Handoff Success------------------------------------------------------
handoff_success_rate = _gauge(
    "evacuation.handoff_success_rate",
    "Successfully processed vs total handoffs received",
    unit="ratio",
)


# ===================================================================
# CUSTOM EVENT HELPERS
# ===================================================================


def _current_span() -> Any:
    """Return the current active span, or ``None``."""
    if not _HAS_OTEL:
        return None
    span = trace.get_current_span()
    if span is None or not span.is_recording():
        return None
    return span


def _emit_event(name: str, attributes: dict[str, Any]) -> None:
    span = _current_span()
    if span is not None:
        span.add_event(name, attributes=attributes)
        return
    if tracer is None:
        return
    with tracer.start_as_current_span(
        f"evacuation.event.{name}",
        attributes={"event.name": name},
    ) as event_span:
        event_span.add_event(name, attributes=attributes)


def emit_handoff_received(
    handoff_id: str,
    incident_id: str,
    tenant_id: str,
) -> None:
    _emit_event(
        "HandoffReceived",
        {
            "handoff_id": handoff_id,
            "incident_id": incident_id,
            "tenant_id": tenant_id,
        },
    )


def emit_plan_generated(
    plan_id: str,
    version: int,
    confidence: float,
    routes_count: int,
    generation_method: str,
) -> None:
    _emit_event(
        "PlanGenerated",
        {
            "plan_id": plan_id,
            "version": version,
            "confidence": confidence,
            "routes_count": routes_count,
            "generation_method": generation_method,
        },
    )


def emit_plan_updated(
    plan_id: str,
    version: int,
    triggers: list[str],
    change_summary: str,
) -> None:
    _emit_event(
        "PlanUpdated",
        {
            "plan_id": plan_id,
            "version": version,
            "triggers": str(triggers),
            "change_summary": change_summary or "",
        },
    )


def emit_shelter_in_place_recommended(
    incident_id: str,
    zone: str,
    population: int,
    hazard_type: str,
) -> None:
    _emit_event(
        "ShelterInPlaceRecommended",
        {
            "incident_id": incident_id,
            "zone": zone,
            "population": population,
            "hazard_type": hazard_type,
        },
    )


def emit_shelter_to_evacuation_recovery(
    plan_id: str,
    zone: str,
    new_route_id: str,
) -> None:
    _emit_event(
        "ShelterToEvacuationRecovery",
        {
            "plan_id": plan_id,
            "zone": zone,
            "new_route_id": new_route_id,
        },
    )


def emit_emergency_escalation(
    incident_id: str,
    zone: str,
    population: int,
) -> None:
    _emit_event(
        "EmergencyEscalation",
        {
            "incident_id": incident_id,
            "zone": zone,
            "population": population,
        },
    )


def emit_override_applied(
    plan_id: str,
    action: str,
    user_id: str,
    role: str,
    incident_id: str = "",
    tenant_id: str = "",
) -> None:
    _emit_event(
        "OverrideApplied",
        {
            "plan_id": plan_id,
            "action": action,
            "user_id": user_id,
            "role": role,
            "incident_id": incident_id,
            "tenant_id": tenant_id,
        },
    )


def emit_degradation_event(component: str, tier: int) -> None:
    _emit_event(
        "DegradationEvent",
        {"component": component, "tier": tier},
    )


def emit_sla_breach(
    handoff_id: str,
    actual_duration_ms: float,
    sla_type: str,
) -> None:
    _emit_event(
        "SLABreach",
        {
            "handoff_id": handoff_id,
            "actual_duration_ms": actual_duration_ms,
            "sla_type": sla_type,
        },
    )


def emit_version_conflict(incident_id: str, retry_count: int) -> None:
    _emit_event(
        "VersionConflict",
        {"incident_id": incident_id, "retry_count": retry_count},
    )


def emit_route_conflict(
    plan_id: str,
    route_id: str,
    utilisation_pct: float,
) -> None:
    _emit_event(
        "RouteConflict",
        {
            "plan_id": plan_id,
            "route_id": route_id,
            "utilisation_pct": utilisation_pct,
        },
    )


def emit_time_deficit_detected(
    plan_id: str,
    zone: str,
    deficit_minutes: float,
) -> None:
    _emit_event(
        "TimeDeficitDetected",
        {
            "plan_id": plan_id,
            "zone": zone,
            "deficit_minutes": deficit_minutes,
        },
    )


# ===================================================================
# SPAN CONTEXT MANAGER HELPER
# ===================================================================


class _NoOpContextManager:
    """Minimal context manager returned when OTel is absent."""

    def __enter__(self) -> _NoOpContextManager:
        return self

    def __exit__(self, *args: Any) -> None:
        pass

    def set_attribute(self, key: str, value: Any) -> None:
        pass

    def add_event(self, name: str, attributes: dict[str, Any] | None = None) -> None:
        pass

    def is_recording(self) -> bool:
        return False

    def set_status(self, *args: Any, **kwargs: Any) -> None:
        pass

    def record_exception(self, exception: BaseException) -> None:
        pass


_NOOP_CTX = _NoOpContextManager()


def start_span(name: str, attributes: dict[str, Any] | None = None) -> Any:
    """Start a new child span as a context manager.

    Usage::

        with start_span("evacuation.compute_zones") as span:
            span.set_attribute("zone.count", 3)
            ...

    When OTel is not installed this returns a lightweight no-op.
    """
    if tracer is not None:
        return tracer.start_as_current_span(name, attributes=attributes)
    return _NOOP_CTX
