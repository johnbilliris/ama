"""Audit-outcome OpenTelemetry span helper (spec-035 T078).

Provides ``record_audit_outcome(outcome, *, attributes=None)`` which sets the
``ama.audit.outcome`` attribute (plus optional context) on the *current*
OpenTelemetry span. Callers in audit-emitting code paths invoke this as the
audit row is appended so trace search in Application Insights surfaces every
new audit ``outcome`` directly.

The helper is a no-op when OTel is not initialised, so import-time wiring is
safe in test/dev where the Azure Monitor distro is absent.
"""

from __future__ import annotations

from collections.abc import Mapping

_AUDIT_OUTCOME_ATTRIBUTE = "ama.audit.outcome"


def record_audit_outcome(
    outcome: str,
    *,
    attributes: Mapping[str, str | int | float | bool] | None = None,
) -> None:
    """Tag the current span with the audit outcome (and optional attributes).

    The function silently returns if either the OpenTelemetry SDK is not
    installed or no active span is present (e.g. CLI scripts).
    """

    try:
        from opentelemetry import trace
    except ImportError:
        return

    span = trace.get_current_span()
    if span is None or not span.is_recording():
        return

    span.set_attribute(_AUDIT_OUTCOME_ATTRIBUTE, outcome)
    if attributes:
        for key, value in attributes.items():
            span.set_attribute(key, value)


__all__ = ["record_audit_outcome"]
