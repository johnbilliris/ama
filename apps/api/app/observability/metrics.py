"""Custom metrics emitter (spec 032 FR-O02 + FR-O03 + FR-O07).

Provides a thin wrapper over the OpenTelemetry meter API so call sites can
emit metrics without depending on the OTel SDK directly. When the OTel SDK
isn't initialised yet (e.g. during unit tests or on first import), the
emitter no-ops silently — call sites are never on a critical path with
respect to telemetry.

Call sites:
  - circuitbreaker.* — apps/agents/common/resilience/pybreaker_adapter.py
  - llm.cost.aud_micros, llm.tokens.total — apps/agents/common/llm_mixin.py
  - agent.killswitch.lag_seconds — apps/agents/common/lifecycle/heartbeat.py
  - rag.retrieval.lag_milliseconds — apps/api/app/services/rag_service.py
  - agent.handoff.* — apps/agents/common/handoffs.py

Catalogue source of truth: docs/observability/metrics-catalogue.md.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

# Lazy OTel meter; populated on first use. Tests may inject a fake.
_METER: Any = None


def _get_meter() -> Any:
    global _METER
    if _METER is not None:
        return _METER
    try:
        from opentelemetry import metrics as otel_metrics

        _METER = otel_metrics.get_meter("ama.observability")
        return _METER
    except Exception:  # noqa: BLE001
        logger.debug("OpenTelemetry not initialised; metric emit will no-op")
        return None


# Per-name instrument cache so repeated emits don't re-create instruments.
_INSTRUMENTS: dict[tuple[str, str], Any] = {}


def _get_counter(name: str, unit: str = "1") -> Any:
    meter = _get_meter()
    if meter is None:
        return None
    key = ("counter", name)
    inst = _INSTRUMENTS.get(key)
    if inst is None:
        inst = meter.create_counter(name, unit=unit)
        _INSTRUMENTS[key] = inst
    return inst


def _get_histogram(name: str, unit: str = "1") -> Any:
    meter = _get_meter()
    if meter is None:
        return None
    key = ("histogram", name)
    inst = _INSTRUMENTS.get(key)
    if inst is None:
        inst = meter.create_histogram(name, unit=unit)
        _INSTRUMENTS[key] = inst
    return inst


def _get_gauge(name: str, unit: str = "1") -> Any:
    meter = _get_meter()
    if meter is None:
        return None
    key = ("gauge", name)
    inst = _INSTRUMENTS.get(key)
    if inst is None:
        # OTel Python supports gauges via observable callbacks; for a simple
        # synchronous gauge we use up_down_counter as the closest analogue.
        inst = meter.create_up_down_counter(name, unit=unit)
        _INSTRUMENTS[key] = inst
    return inst


def emit_counter(name: str, value: int = 1, attributes: dict[str, Any] | None = None, *, unit: str = "1") -> None:
    inst = _get_counter(name, unit)
    if inst is None:
        return
    try:
        inst.add(value, attributes or {})
    except Exception:  # noqa: BLE001
        logger.debug("counter %s emit failed", name, exc_info=True)


def emit_histogram(name: str, value: float, attributes: dict[str, Any] | None = None, *, unit: str = "1") -> None:
    inst = _get_histogram(name, unit)
    if inst is None:
        return
    try:
        inst.record(value, attributes or {})
    except Exception:  # noqa: BLE001
        logger.debug("histogram %s emit failed", name, exc_info=True)


def emit_gauge(name: str, value: float, attributes: dict[str, Any] | None = None, *, unit: str = "1") -> None:
    inst = _get_gauge(name, unit)
    if inst is None:
        return
    try:
        # up_down_counter accepts deltas; for a true "set" gauge we approximate
        # by recording the delta from the prior value (kept per name+attributes).
        prior_key = (name, tuple(sorted((attributes or {}).items())))
        prior = _PRIOR_GAUGE.get(prior_key, 0.0)
        delta = value - prior
        inst.add(delta, attributes or {})
        _PRIOR_GAUGE[prior_key] = value
    except Exception:  # noqa: BLE001
        logger.debug("gauge %s emit failed", name, exc_info=True)


_PRIOR_GAUGE: dict[tuple[str, tuple[tuple[str, Any], ...]], float] = {}


def reset_for_tests() -> None:
    """Clear the in-process meter cache; for unit tests only."""
    global _METER
    _METER = None
    _INSTRUMENTS.clear()
    _PRIOR_GAUGE.clear()
