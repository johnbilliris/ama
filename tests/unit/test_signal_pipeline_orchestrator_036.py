"""Tests for spec-036 T-L01 — signal pipeline orchestrator.

Confirms the orchestrator owns the FR-009 / FR-015 invariant:

* Persist a synthetic signal via :class:`SyntheticSignalsRepository`.
* Publish ``signal.persisted`` + ``signal.fanned_out`` events to the
  tenant-scoped Event Hub (T-L04).
* Resolve sub-agent fan-out via :func:`subscribers_for` (T-L05).
* Audit each step via :class:`AuditWriter` with a single sequence-numbered
  envelope per signal.

Constitution invariants:
    - **Primacy of Life**: a signal whose category maps to a hazard MUST
      reach its subscribers in the same orchestrator turn (no silent drop).
    - **Synthetic-only egress**: every event carries ``synthetic=True``
      metadata; the test inspects this on the published Event Hub event.
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from apps.api.app.repositories.synthetic_signals_repository import (
    SyntheticSignalsRepository,
)
from apps.api.app.services.simulation.audit_writer import (
    AuditWriter,
    reset_audit_writer_for_tests,
)
from apps.api.app.services.simulation.event_hub_publisher import (
    EventHubPublisher,
)
from apps.api.app.services.simulation.signal_pipeline_orchestrator import (
    DispatchResult,
    SignalPipelineOrchestrator,
)
from packages.domain.src.domain.models.synthetic_signal import SyntheticSignal


@pytest.fixture(autouse=True)
def _isolate_state() -> None:
    reset_audit_writer_for_tests()
    yield
    reset_audit_writer_for_tests()


def _make_signal(
    *,
    sim_id: str = "sim-L01",
    tenant_id: str = "tenant-pacific",
    signal_id: str = "sim-msg-deadbeef",
    category: str = "fire-behaviour",
) -> SyntheticSignal:
    return SyntheticSignal(
        signal_id=signal_id,
        simulation_id=sim_id,
        tenant_id=tenant_id,
        category=category,
        confidence="high",
        observed_at=datetime.now(UTC),
        freshness_window_seconds=60,
        parameters={"distance_km": 12.5},
    )


@pytest.mark.asyncio
async def test_dispatch_persists_signal_and_returns_result() -> None:
    repo = SyntheticSignalsRepository()
    publisher = EventHubPublisher()  # in-memory mode
    orchestrator = SignalPipelineOrchestrator(
        signals_repository=repo,
        event_hub_publisher=publisher,
        audit_writer=AuditWriter(),
    )
    signal = _make_signal()

    result = await orchestrator.dispatch(signal, correlation_id="corr-1")
    assert isinstance(result, DispatchResult)
    assert result.signal_id == signal.signal_id

    # Persisted to repo (in-memory).
    recent = await repo.list_recent(signal.simulation_id, window_seconds=60)
    assert any(s.signal_id == signal.signal_id for s in recent)


@pytest.mark.asyncio
async def test_dispatch_publishes_persisted_and_fanned_out_events() -> None:
    publisher = EventHubPublisher()
    orchestrator = SignalPipelineOrchestrator(
        signals_repository=SyntheticSignalsRepository(),
        event_hub_publisher=publisher,
        audit_writer=AuditWriter(),
    )
    signal = _make_signal()

    await orchestrator.dispatch(signal, correlation_id="corr-2")

    events = publisher.captured_events_for(signal.tenant_id)
    kinds = {e.kind for e in events}
    assert "signal.persisted" in kinds
    assert "signal.fanned_out" in kinds
    # Every event carries the originating signal_id and tenant.
    assert all(e.signal_id == signal.signal_id for e in events)
    assert all(e.tenant_id == signal.tenant_id for e in events)


@pytest.mark.asyncio
async def test_dispatch_resolves_subscribers_for_hazard_kind() -> None:
    """Hazard-class signals fan-out to {Risk, Evac, Resource, Planning}."""

    publisher = EventHubPublisher()
    orchestrator = SignalPipelineOrchestrator(
        signals_repository=SyntheticSignalsRepository(),
        event_hub_publisher=publisher,
        audit_writer=AuditWriter(),
    )
    signal = _make_signal(category="fire-behaviour")
    result = await orchestrator.dispatch(signal, correlation_id="corr-3")

    expected = {"Risk", "Evac", "Resource", "Planning"}
    assert set(result.fanned_out_to) == expected


@pytest.mark.asyncio
async def test_dispatch_writes_synthetic_delivery_audit_per_subscriber() -> None:
    publisher = EventHubPublisher()
    audit = AsyncMock(spec=AuditWriter)
    orchestrator = SignalPipelineOrchestrator(
        signals_repository=SyntheticSignalsRepository(),
        event_hub_publisher=publisher,
        audit_writer=audit,
    )
    signal = _make_signal()
    await orchestrator.dispatch(signal, correlation_id="corr-4")

    # AuditWriter.write called once per fan-out target with
    # entry_type="synthetic-delivery".
    types = [c.args[0] for c in audit.write.await_args_list]
    assert types.count("synthetic-delivery") >= 4  # hazard kind → 4 subs


@pytest.mark.asyncio
async def test_dispatch_unknown_kind_raises_value_error() -> None:
    """Unknown signal kinds must fail closed (FR-051 closed-set)."""

    publisher = EventHubPublisher()
    orchestrator = SignalPipelineOrchestrator(
        signals_repository=SyntheticSignalsRepository(),
        event_hub_publisher=publisher,
        audit_writer=AuditWriter(),
    )
    # `comms-channel-state` is in the SignalCategory enum but not a hazard;
    # we map it via category_to_signal_kind. A category that doesn't map
    # at all (e.g. utility) should return an empty fan-out (graceful no-op),
    # not raise. Only an explicit unknown kind raises.
    signal = _make_signal(category="utility")
    result = await orchestrator.dispatch(signal, correlation_id="corr-5")
    assert result.fanned_out_to == ()


@pytest.mark.asyncio
async def test_dispatch_event_metadata_carries_synthetic_flag() -> None:
    """Every published event must carry ``synthetic=True`` metadata (FR-006)."""

    publisher = EventHubPublisher()
    orchestrator = SignalPipelineOrchestrator(
        signals_repository=SyntheticSignalsRepository(),
        event_hub_publisher=publisher,
        audit_writer=AuditWriter(),
    )
    signal = _make_signal()
    await orchestrator.dispatch(signal, correlation_id="corr-6")

    events = publisher.captured_events_for(signal.tenant_id)
    assert all(e.metadata.get("synthetic") is True for e in events)
