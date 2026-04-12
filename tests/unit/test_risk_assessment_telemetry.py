"""Unit tests for apps/agents/risk_assessment/telemetry.py."""

from __future__ import annotations

import os
import sys

# Ensure the risk_assessment package is importable.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "apps", "agents"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from risk_assessment.telemetry import (  # noqa: E402
    CustomEventEmitter,
    RiskAssessmentMetrics,
    _NoOpMetric,
    _NoOpSpan,
    _NoOpTracer,
    events,
    metrics,
    pipeline_span,
)

# ---------------------------------------------------------------------------
# No-op stubs
# ---------------------------------------------------------------------------


def test_noop_metric_add():
    _NoOpMetric().add(1)


def test_noop_metric_record():
    _NoOpMetric().record(42)


def test_noop_span_context_manager():
    with _NoOpSpan() as s:
        s.set_attribute("key", "val")


def test_noop_span_set_status():
    _NoOpSpan().set_status("ok")


def test_noop_span_record_exception():
    _NoOpSpan().record_exception(Exception("boom"))


def test_noop_span_add_event():
    _NoOpSpan().add_event("test", {"k": "v"})


def test_noop_tracer_returns_noop_span():
    span = _NoOpTracer().start_as_current_span("x")
    assert isinstance(span, _NoOpSpan)


# ---------------------------------------------------------------------------
# Metrics singleton
# ---------------------------------------------------------------------------


def test_metrics_singleton_exists():
    assert isinstance(metrics, RiskAssessmentMetrics)


def test_metrics_convenience_methods_dont_raise():
    metrics.inc_assessment_count()
    metrics.inc_handoff_intake()
    metrics.inc_handoff_rejected()
    metrics.inc_duplicate_discard()
    metrics.inc_sla_breach()
    metrics.inc_escalation("communication")
    metrics.inc_dead_letter()
    metrics.inc_fallback()
    metrics.inc_content_safety_failure()
    metrics.inc_version_conflict_retry()
    metrics.record_confidence(0.85)
    metrics.record_severity("high")
    metrics.record_assessment_latency(1500.0)


# ---------------------------------------------------------------------------
# Custom events
# ---------------------------------------------------------------------------


def test_event_handoff_received():
    CustomEventEmitter.handoff_received("h1", "inc1", "live")


def test_event_assessment_generated():
    CustomEventEmitter.assessment_generated("a1", 0.9, "high", "llm")


def test_event_contradiction_detected():
    CustomEventEmitter.contradiction_detected(["s1"], ["src1"], 0.3)


def test_event_escalation_triggered():
    CustomEventEmitter.escalation_triggered("comm", "r1", 0.8)


def test_event_degradation():
    CustomEventEmitter.degradation_event("llm", 1)


def test_event_sla_breach():
    CustomEventEmitter.sla_breach("h1", 12000.0)


def test_event_version_conflict():
    CustomEventEmitter.version_conflict("inc1", "spread", 2)


# ---------------------------------------------------------------------------
# Pipeline span
# ---------------------------------------------------------------------------


def test_pipeline_span_context_manager():
    with pipeline_span("test.span", "hid") as s:
        assert s is not None
        s.set_attribute("test_key", "test_val")


def test_pipeline_span_without_handoff_id():
    with pipeline_span("test.span") as s:
        assert s is not None


# ---------------------------------------------------------------------------
# Events singleton
# ---------------------------------------------------------------------------


def test_events_is_custom_event_emitter():
    assert events is CustomEventEmitter
