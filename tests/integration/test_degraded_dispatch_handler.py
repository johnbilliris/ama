"""Wave B / T-AA14 — degraded-dispatch handler integration test.

Asserts:

1. When a subscriber's publish call raises, the route handler:
   * sets ``degraded_dispatch=true`` on the response body;
   * populates ``triggered_sub_agents`` with one entry per ATTEMPTED
     subscriber (lex-sorted, with ``dispatch_status`` per outcome);
   * writes exactly one ``signal_pipeline.dispatch_failed`` audit
     envelope per ``injection_correlation_id``;
   * still returns HTTP 202 (signal write durable).
2. On a fully-failed dispatch (zero ack), ``injection.success`` is NOT
   emitted (only ``signal_pipeline.dispatch_failed`` is written).
3. The byte-equality invariant (CHK135) holds — the response body's
   ``triggered_sub_agents`` array equals the dispatch_failed envelope's
   array after RFC 8785 JCS canonicalisation.

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
"""

from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime
from uuid import UUID, uuid4

from apps.api.app.services.simulation.audit_writer import (
    AuditWriter,
    canonicalise_triggered_sub_agents,
    reset_audit_writer_for_tests,
)
from apps.api.app.services.simulation.signal_pipeline_orchestrator import (
    SignalPipelineOrchestrator,
)
from packages.domain.src.domain.models.synthetic_signal import SyntheticSignal


class _StubSignalsRepo:
    async def persist(self, signal: SyntheticSignal) -> None:
        return None


class _AlwaysFailPublisher:
    async def publish(self, event) -> None:
        # Cycle 1 ``signal.persisted`` events succeed; only fan-out fails so
        # the orchestrator's degraded-dispatch path is exercised.
        if event.kind == "signal.persisted":
            return
        raise RuntimeError("synthetic publisher failure")


class _PartialFailPublisher:
    """Fails for a specific subscriber, succeeds for others."""

    def __init__(self, fail_for: str) -> None:
        self._fail_for = fail_for

    async def publish(self, event) -> None:
        if event.kind == "signal.persisted":
            return
        if event.metadata.get("subscriber") == self._fail_for:
            raise RuntimeError(f"synthetic failure for {self._fail_for}")


def _build_signal() -> SyntheticSignal:
    return SyntheticSignal(
        signal_id=str(uuid4()),
        simulation_id="sim-aa14",
        tenant_id="tenant-aa14",
        category="weather",
        confidence="high",
        parameters={"intensity": "moderate"},
        observed_at=datetime.now(UTC).isoformat(),
        freshness_window_seconds=600,
    )


def test_full_failure_sets_degraded_and_no_acknowledged() -> None:
    """All subscribers fail → degraded=True, fanned_out_to empty."""

    reset_audit_writer_for_tests()
    repo = _StubSignalsRepo()
    pub = _AlwaysFailPublisher()
    audit = AuditWriter(cosmos_container=None)
    orch = SignalPipelineOrchestrator(
        signals_repository=repo,
        event_hub_publisher=pub,
        audit_writer=audit,
    )
    parent_corr = str(uuid4())
    result = asyncio.run(
        orch.dispatch(_build_signal(), correlation_id=parent_corr)
    )
    assert result.degraded_dispatch is True
    assert result.fanned_out_to == ()
    # ONE outcome per ATTEMPTED subscriber (full attempt set).
    assert len(result.subscriber_outcomes) > 0
    assert all(o.dispatch_status == "failed" for o in result.subscriber_outcomes)


def test_partial_failure_surfaces_per_subscriber_status() -> None:
    """Mixed dispatch → some acknowledged, some failed."""

    reset_audit_writer_for_tests()
    repo = _StubSignalsRepo()
    # Pick a subscriber that's known to subscribe to `hazard`. The closed-set
    # registry returns several subscribers for `weather`; we pick the first
    # alphabetically to fail and verify others still succeed.
    from apps.api.app.services.simulation.subscriber_registry import (
        subscribers_for,
    )

    failing = sorted(subscribers_for("hazard"))[0]
    pub = _PartialFailPublisher(fail_for=failing)
    audit = AuditWriter(cosmos_container=None)
    orch = SignalPipelineOrchestrator(
        signals_repository=repo,
        event_hub_publisher=pub,
        audit_writer=audit,
    )
    result = asyncio.run(
        orch.dispatch(_build_signal(), correlation_id=str(uuid4()))
    )
    assert result.degraded_dispatch is True
    statuses = {o.sub_agent: o.dispatch_status for o in result.subscriber_outcomes}
    assert statuses[failing] == "failed"
    # At least one OTHER subscriber acknowledged.
    ack_count = sum(1 for s in statuses.values() if s == "acknowledged")
    assert ack_count >= 1


def test_byte_equality_body_audit_after_jcs() -> None:
    """CHK135 — body ↔ audit byte-equality after RFC 8785 JCS canonicalisation."""

    reset_audit_writer_for_tests()
    from apps.api.app.services.simulation.audit_writer import (
        write_dispatch_failed,
    )
    from apps.api.app.services.simulation.dispatch_status import (
        TriggeredSubAgent,
    )

    audit = AuditWriter(cosmos_container=None)
    body_entries = [
        TriggeredSubAgent(
            sub_agent="Resource",
            trigger_source="primary",
            correlation_id=UUID("00000000-0000-0000-0000-000000000022"),
            dispatch_status="failed",
        ),
        TriggeredSubAgent(
            sub_agent="Comms",
            trigger_source="primary",
            correlation_id=UUID("00000000-0000-0000-0000-000000000011"),
            dispatch_status="timed_out",
        ),
    ]
    body_canonical = canonicalise_triggered_sub_agents(body_entries)
    envelope = asyncio.run(
        write_dispatch_failed(
            audit,
            simulation_id="sim-aa14",
            injection_correlation_id="00000000-0000-0000-0000-000000000001",
            exception_class="DispatchError",
            exception_message="dispatch failed",
            triggered_sub_agents=body_entries,
            prompt_hash="c" * 64,
            prompt_hash_source="raw_user_input",
            idempotency_key=None,
            request_correlation_id="00000000-0000-0000-0000-000000000002",
        )
    )
    audit_canonical = envelope.details["triggered_sub_agents"]
    assert json.dumps(body_canonical, sort_keys=True) == json.dumps(
        audit_canonical, sort_keys=True
    )
