"""Wave B / T-AA13 — hybrid OTel propagation (pass-2 Q3).

Asserts:

1. Parent ``trace_id`` is the 16-byte hex form of
   ``UUID(injection_correlation_id).bytes`` (data-model §11.3 step 2).
2. Each subscriber's child ``span_id`` is the 8-byte hex form of
   ``UUID(per_subscriber_correlation_id).bytes[:8]`` (data-model §11.3
   step 3).
3. Both surface as ``customDimensions["injection_correlation_id"]`` and
   ``customDimensions["correlation_id"]`` on every published event
   (data-model §11.3 step 4).

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from uuid import UUID, uuid4

from apps.api.app.services.simulation.audit_writer import (
    AuditWriter,
    reset_audit_writer_for_tests,
)
from apps.api.app.services.simulation.signal_pipeline_orchestrator import (
    SignalPipelineOrchestrator,
)
from packages.domain.src.domain.models.synthetic_signal import SyntheticSignal


class _StubSignalsRepo:
    async def persist(self, signal: SyntheticSignal) -> None:
        return None


class _StubPublisher:
    def __init__(self) -> None:
        self.events: list = []

    async def publish(self, event) -> None:
        self.events.append(event)


def _build_signal() -> SyntheticSignal:
    return SyntheticSignal(
        signal_id=str(uuid4()),
        simulation_id="sim-aa13",
        tenant_id="tenant-aa13",
        category="weather",
        confidence="high",
        parameters={"intensity": "moderate"},
        observed_at=datetime.now(UTC).isoformat(),
        freshness_window_seconds=600,
    )


def test_parent_trace_id_derived_from_injection_correlation_id() -> None:
    reset_audit_writer_for_tests()
    repo = _StubSignalsRepo()
    pub = _StubPublisher()
    audit = AuditWriter(cosmos_container=None)
    orch = SignalPipelineOrchestrator(
        signals_repository=repo,
        event_hub_publisher=pub,
        audit_writer=audit,
    )

    parent_corr = "00000000-0000-0000-0000-0000000000ab"
    signal = _build_signal()
    result = asyncio.run(orch.dispatch(signal, correlation_id=parent_corr))

    expected_trace_id = UUID(parent_corr).bytes.hex()
    assert result.otel_trace_id == expected_trace_id
    assert len(result.otel_trace_id) == 32  # 16-byte hex


def test_child_span_ids_derived_from_subscriber_correlation_ids() -> None:
    reset_audit_writer_for_tests()
    repo = _StubSignalsRepo()
    pub = _StubPublisher()
    audit = AuditWriter(cosmos_container=None)
    orch = SignalPipelineOrchestrator(
        signals_repository=repo,
        event_hub_publisher=pub,
        audit_writer=audit,
    )

    signal = _build_signal()
    result = asyncio.run(orch.dispatch(signal, correlation_id=str(uuid4())))

    assert result.otel_span_ids
    for subscriber, span_id in result.otel_span_ids.items():
        assert len(span_id) == 16  # 8-byte hex
        sub_corr = result.per_subscriber_correlations[subscriber]
        expected = sub_corr.bytes[:8].hex()
        assert span_id == expected


def test_published_events_carry_injection_and_per_subscriber_correlation_ids() -> None:
    reset_audit_writer_for_tests()
    repo = _StubSignalsRepo()
    pub = _StubPublisher()
    audit = AuditWriter(cosmos_container=None)
    orch = SignalPipelineOrchestrator(
        signals_repository=repo,
        event_hub_publisher=pub,
        audit_writer=audit,
    )

    parent_corr = str(uuid4())
    signal = _build_signal()
    asyncio.run(orch.dispatch(signal, correlation_id=parent_corr))

    fanout_events = [e for e in pub.events if e.kind == "signal.fanned_out"]
    assert fanout_events, "Expected at least one signal.fanned_out event"

    for event in fanout_events:
        assert event.metadata["injection_correlation_id"] == parent_corr
        # Per-subscriber correlation_id MUST also be present and a valid UUID.
        sub_corr = UUID(event.metadata["correlation_id"])
        assert sub_corr != UUID(parent_corr)
        # OTel propagation customDimensions present.
        assert "otel_trace_id" in event.metadata
        assert "otel_span_id" in event.metadata
