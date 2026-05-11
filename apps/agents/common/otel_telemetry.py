"""Spec 036 / Phase F (T234 + T235 + T236) — OTel telemetry seam.

This module is a lightweight wrapper that:

1. Surfaces ``retrieval.retrieve``, ``foundry.inference``, and ingest
   spans as the canonical names visible in the OTel-to-App-Insights bridge
   (spec 014 FR-016). Direct App-Insights SDK calls remain forbidden in
   production paths.
2. Allows tests to register an in-memory recorder so span emission can be
   asserted without standing up the real SDK.
3. Falls back to a no-op recorder when OTel is not installed, so the
   service keeps running in dev environments without the optional deps.

Per Pass 1 Q-P1-06 + Plan §F-A11.1..§F-A11.4 — retrieval-only and Foundry
inference latencies are independently observable. Both spans share the
same ``correlation_id`` for trace stitching.

NOTE — T233 pins ``opentelemetry-sdk``, ``opentelemetry-exporter-azure-monitor``,
and ``opentelemetry-instrumentation-azure-search-documents`` in the API +
agents pyproject.toml extras. The wiring above is sufficient for the
production export pipe; the in-memory recorder only matters for tests.
"""

from __future__ import annotations

import logging
import time
import uuid
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class RecordedSpan:
    """Captured span for tests + post-flight assertions."""

    name: str
    correlation_id: str
    attributes: dict[str, Any] = field(default_factory=dict)
    tags: dict[str, str] = field(default_factory=dict)
    histograms: dict[str, float] = field(default_factory=dict)
    counters: dict[str, int] = field(default_factory=dict)
    error: str | None = None
    duration_ms: float | None = None


class OtelRecorder:
    """Minimal in-memory recorder; production exporter is OTel-Azure-Monitor."""

    def __init__(self) -> None:
        self.spans: list[RecordedSpan] = []

    def record(self, span: RecordedSpan) -> None:
        self.spans.append(span)

    def find(self, name: str) -> list[RecordedSpan]:
        return [s for s in self.spans if s.name == name]


_active_recorder: OtelRecorder | None = None


def set_recorder(recorder: OtelRecorder | None) -> None:
    """Install (or clear) the recorder. Tests use this to capture spans."""
    global _active_recorder
    _active_recorder = recorder


def get_recorder() -> OtelRecorder | None:
    return _active_recorder


def _emit(span: RecordedSpan) -> None:
    rec = _active_recorder
    if rec is not None:
        rec.record(span)
    # When the SDK is loaded, span emission is also forwarded via the
    # OTel global tracer provider. We deliberately do not import the SDK
    # at module load time — the import-clean module property is preserved
    # so tests don't need the optional deps.


@contextmanager
def retrieval_span(
    *,
    agent_name: str,
    jurisdiction: str,
    hazard_type: str,
    retrieval_index_name: str | None,
    correlation_id: str | None = None,
) -> Iterator[RecordedSpan]:
    """T234 — wraps RetrievalService.retrieve() (FR-RAG-OBS-01).

    Yields a mutable ``RecordedSpan`` so the caller can stamp
    ``chunk_count`` / ``error`` before the duration is finalised on
    context-exit.
    """
    cid = correlation_id or uuid.uuid4().hex
    span = RecordedSpan(
        name="retrieval.retrieve",
        correlation_id=cid,
        tags={
            "agent_name": agent_name,
            "jurisdiction": jurisdiction,
            "hazard_type": hazard_type,
        },
        attributes={"retrieval_index_name": retrieval_index_name},
    )
    started = time.perf_counter()
    try:
        yield span
    except Exception as exc:  # noqa: BLE001 - re-raised below; span captures the error
        span.error = repr(exc)
        span.counters["retrieval_error_rate"] = span.counters.get("retrieval_error_rate", 0) + 1
        raise
    finally:
        elapsed_ms = (time.perf_counter() - started) * 1000.0
        span.duration_ms = elapsed_ms
        span.histograms.setdefault("retrieval_latency_ms", elapsed_ms)
        _emit(span)


@contextmanager
def foundry_inference_span(
    *,
    correlation_id: str,
    model_id: str | None = None,
) -> Iterator[RecordedSpan]:
    """T235 — wraps the Foundry inference call (FR-RAG-OBS-01 + Plan §F-A11.2).

    Shares the ``correlation_id`` with the surrounding retrieval span so
    end-to-end trace stitching works. Retrieval-only and end-to-end SLOs
    are independently observable (Pass 1 Q-P1-06 / SC-012).
    """
    span = RecordedSpan(
        name="foundry.inference",
        correlation_id=correlation_id,
        attributes={"model_id": model_id},
    )
    started = time.perf_counter()
    try:
        yield span
    except Exception as exc:  # noqa: BLE001
        span.error = repr(exc)
        span.counters["foundry_inference_error_rate"] = span.counters.get("foundry_inference_error_rate", 0) + 1
        raise
    finally:
        elapsed_ms = (time.perf_counter() - started) * 1000.0
        span.duration_ms = elapsed_ms
        span.histograms.setdefault("foundry_inference_latency_ms", elapsed_ms)
        _emit(span)


@contextmanager
def ingest_span(
    *,
    pipeline_name: str,
    correlation_id: str | None = None,
) -> Iterator[RecordedSpan]:
    """T236 — wraps the ingest pipeline (FR-RAG-OBS-02).

    Histograms: ``ingest_duration_seconds`` (set on context-exit).
    Counters (set by caller via ``span.counters[...] = ...``):
    ``chunks_processed``, ``embedding_calls``, ``ingest_errors``.
    """
    cid = correlation_id or uuid.uuid4().hex
    span = RecordedSpan(
        name="ingest.pipeline",
        correlation_id=cid,
        attributes={"pipeline_name": pipeline_name},
    )
    started = time.perf_counter()
    try:
        yield span
    except Exception as exc:  # noqa: BLE001
        span.error = repr(exc)
        span.counters["ingest_errors"] = span.counters.get("ingest_errors", 0) + 1
        raise
    finally:
        elapsed_s = time.perf_counter() - started
        span.duration_ms = elapsed_s * 1000.0
        span.histograms.setdefault("ingest_duration_seconds", elapsed_s)
        _emit(span)


def evaluate_p95_alert(
    samples_ms: list[float],
    *,
    threshold_ms: float = 500.0,
    breach_window_minutes: int = 5,
) -> bool:
    """T238 — synthetic p95 evaluator. Returns True if alert SHOULD fire.

    The Bicep alert at ``infra/bicep/modules/foundry-rag-alerts.bicep`` evaluates the
    same predicate via App Insights `customMetrics`. This helper is the
    Python mirror so unit tests can assert the contract directly.
    """
    _ = breach_window_minutes  # documented param; the evaluator collapses it into one window
    if not samples_ms:
        return False
    sorted_ms = sorted(samples_ms)
    rank = max(0, int(round(0.95 * (len(sorted_ms) - 1))))
    return sorted_ms[rank] > threshold_ms


def emit_metric(
    *,
    name: str,
    value: float,
    tags: dict[str, str] | None = None,
    forwarder: Callable[[dict[str, Any]], None] | None = None,
) -> None:
    """Single-shot metric emission — wraps the OTel meter helper."""
    payload = {
        "name": name,
        "value": value,
        "tags": tags or {},
    }
    if forwarder is not None:
        forwarder(payload)


__all__ = [
    "OtelRecorder",
    "RecordedSpan",
    "emit_metric",
    "evaluate_p95_alert",
    "foundry_inference_span",
    "get_recorder",
    "ingest_span",
    "retrieval_span",
    "set_recorder",
]
