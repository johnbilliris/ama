"""Wave B / T-AA13 — per-subscriber correlation_id (pass-1 Q4).

Asserts:

1. Each subscriber gets a fresh ``uuid4()`` distinct from the parent
   ``correlation_id`` (pass-1 Q4 invariant).
2. ``DispatchResult.per_subscriber_correlations`` maps each fanned-out
   subscriber to its UUID.
3. UUIDs are unique across subscribers in a single dispatch.

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
    def __init__(self) -> None:
        self.persisted: list[SyntheticSignal] = []

    async def persist(self, signal: SyntheticSignal) -> None:
        self.persisted.append(signal)


class _StubPublisher:
    def __init__(self) -> None:
        self.events: list = []

    async def publish(self, event) -> None:
        self.events.append(event)


def _build_signal(category: str = "weather") -> SyntheticSignal:
    return SyntheticSignal(
        signal_id=str(uuid4()),
        simulation_id="sim-aa13",
        tenant_id="tenant-aa13",
        category=category,
        confidence="high",
        parameters={"intensity": "moderate"},
        observed_at=datetime.now(UTC).isoformat(),
        freshness_window_seconds=600,
    )


def test_per_subscriber_correlations_are_fresh_uuids() -> None:
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
    signal = _build_signal(category="weather")
    result = asyncio.run(orch.dispatch(signal, correlation_id=parent_corr))

    assert result.fanned_out_to, "Expected non-empty fan-out for `weather` category"
    assert len(result.per_subscriber_correlations) == len(result.fanned_out_to)

    # All per-subscriber correlation_ids are valid UUIDs distinct from parent.
    seen: set[UUID] = set()
    parent_uuid = UUID(parent_corr)
    for subscriber in result.fanned_out_to:
        sub_corr = result.per_subscriber_correlations[subscriber]
        assert isinstance(sub_corr, UUID)
        assert sub_corr != parent_uuid
        assert sub_corr not in seen, "Per-subscriber correlation_ids MUST be unique"
        seen.add(sub_corr)


def test_no_subscribers_path_returns_empty_correlations() -> None:
    reset_audit_writer_for_tests()
    repo = _StubSignalsRepo()
    pub = _StubPublisher()
    audit = AuditWriter(cosmos_container=None)
    orch = SignalPipelineOrchestrator(
        signals_repository=repo,
        event_hub_publisher=pub,
        audit_writer=audit,
    )

    # `transport` has no SignalKind → empty fan-out.
    signal = _build_signal(category="transport")
    result = asyncio.run(orch.dispatch(signal, correlation_id=str(uuid4())))

    assert result.fanned_out_to == ()
    assert result.per_subscriber_correlations == {}
    assert result.skipped_reason == "no_subscribers_for_category"
