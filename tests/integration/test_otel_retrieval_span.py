"""T232 — F-A11 OTel retrieval span integration test.

Per FR-RAG-OBS-01 + Plan §F-A11.1 + §F-A11.2:

a. span name = ``retrieval.retrieve``
b. histogram ``retrieval_latency_ms``
c. histogram ``retrieval_chunk_count``
d. counter ``retrieval_error_rate`` (zero on happy path; 1 on raise)
e. tags ``agent_name``, ``jurisdiction``, ``hazard_type``
f. span attribute ``retrieval_index_name``
g. shared ``correlation_id`` with the Foundry inference span

Proves: T234 + T235 + T238.
"""

from __future__ import annotations

import pytest

from apps.agents.common.otel_telemetry import (
    OtelRecorder,
    evaluate_p95_alert,
    foundry_inference_span,
    retrieval_span,
    set_recorder,
)


@pytest.fixture(autouse=True)
def _recorder() -> OtelRecorder:
    rec = OtelRecorder()
    set_recorder(rec)
    yield rec
    set_recorder(None)


def test_retrieval_span_name_and_attributes(_recorder: OtelRecorder) -> None:
    with retrieval_span(
        agent_name="EvacuationAgent",
        jurisdiction="nsw",
        hazard_type="bushfire",
        retrieval_index_name="corpus-v3",
        correlation_id="cor-1",
    ) as span:
        span.histograms["retrieval_chunk_count"] = 6
    assert _recorder.find("retrieval.retrieve")
    rs = _recorder.find("retrieval.retrieve")[0]
    assert rs.tags == {
        "agent_name": "EvacuationAgent",
        "jurisdiction": "nsw",
        "hazard_type": "bushfire",
    }
    assert rs.attributes["retrieval_index_name"] == "corpus-v3"
    assert "retrieval_latency_ms" in rs.histograms
    assert rs.histograms["retrieval_chunk_count"] == 6


def test_retrieval_span_records_error_counter(_recorder: OtelRecorder) -> None:
    with pytest.raises(RuntimeError):
        with retrieval_span(
            agent_name="EvacuationAgent",
            jurisdiction="nsw",
            hazard_type="bushfire",
            retrieval_index_name="corpus-v3",
            correlation_id="cor-2",
        ):
            raise RuntimeError("simulated retrieval failure")
    rs = _recorder.find("retrieval.retrieve")[0]
    assert rs.error is not None
    assert rs.counters["retrieval_error_rate"] == 1


def test_retrieval_and_foundry_share_correlation_id(_recorder: OtelRecorder) -> None:
    """Trace stitching invariant — both spans MUST share correlation_id."""
    with retrieval_span(
        agent_name="EvacuationAgent",
        jurisdiction="nsw",
        hazard_type="bushfire",
        retrieval_index_name="corpus-v3",
        correlation_id="cor-stitched",
    ) as r_span:
        with foundry_inference_span(
            correlation_id=r_span.correlation_id,
            model_id="gpt-4.1",
        ) as f_span:
            f_span.histograms["foundry_inference_latency_ms"] = 1234.0

    r = _recorder.find("retrieval.retrieve")[0]
    f = _recorder.find("foundry.inference")[0]
    assert r.correlation_id == f.correlation_id == "cor-stitched"


def test_p95_alert_threshold(_recorder: OtelRecorder) -> None:
    """T238 — p95 evaluator fires when latency >500ms across the window."""
    # 10 samples above 500ms out of 100 → p95 = 600ms → alert.
    samples = [350.0] * 90 + [600.0] * 10
    assert evaluate_p95_alert(samples, threshold_ms=500.0) is True
    samples_ok = [350.0] * 100
    assert evaluate_p95_alert(samples_ok, threshold_ms=500.0) is False
    # Empty window does NOT alert (avoids false positives during cold-start).
    assert evaluate_p95_alert([], threshold_ms=500.0) is False
