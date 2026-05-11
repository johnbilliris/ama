"""T167 — Integration test for the blue-green index-rollback orchestrator
(FR-RAG-IDX-09; SC-019; ADR-16; Plan §F-A7.3..§F-A7.4).

Asserts:

* Service Bus ``index_rollback`` events emitted at every state transition
  (requested → approved → completed).
* Manual Release Manager approval is mandatory (no Service Principal slip).
* 5-minute SLO timer measured from request to completed_at.
* Terminal audit append carries ``{old_index_name, new_index_name,
  parity_gate_failure_reason, release_manager_id, completed_at}``.
* SLO breach (>5min) tagged ``slo_breached: true`` but rollback still completes.
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest

orch_module = pytest.importorskip("app.services.index_rollback")


def _make_orchestrator(*, clock: list[datetime], approve: str = "rm-1") -> tuple[Any, list, list, list]:
    bus_events: list[tuple[str, dict[str, Any]]] = []
    audit_records: list[dict[str, Any]] = []
    flips: list[tuple[str, str]] = []

    async def publish(topic: str, payload: dict[str, Any]) -> None:
        bus_events.append((topic, payload))

    async def audit(record: dict[str, Any]) -> None:
        audit_records.append(record)

    async def approval(_req: Any) -> str:
        return approve

    async def flip(old: str, new: str) -> None:
        flips.append((old, new))

    def now_fn() -> datetime:
        # Pop in order so each call advances the clock deterministically.
        return clock.pop(0) if clock else datetime.now(tz=UTC)

    orch = orch_module.IndexRollbackOrchestrator(
        service_bus_publisher=publish,
        audit_writer=audit,
        approval_oracle=approval,
        alias_flipper=flip,
        now_fn=now_fn,
    )
    return orch, bus_events, audit_records, flips


def _make_request() -> Any:
    return orch_module.IndexRollbackRequest(
        old_index_name="corpus-v3",
        new_index_name="corpus-v4",
        parity_gate_failure_reason="recall@10-regression-22pct",
        correlation_id="cor-rollback-1",
    )


def test_happy_path_emits_3_events_and_audit() -> None:
    base = datetime(2025, 11, 18, 12, 0, 0, tzinfo=UTC)
    # Orchestrator calls now_fn() 3x: timer_started, approved.timestamp, completed_at.
    clock = [base, base, base + timedelta(seconds=120)]
    orch, bus, audit, flips = _make_orchestrator(clock=clock)

    final = asyncio.run(orch.trigger(_make_request()))

    assert final.state == "completed"
    states = [payload["state"] for _topic, payload in bus]
    assert states == ["requested", "approved", "completed"]
    assert flips == [("corpus-v3", "corpus-v4")]
    assert len(audit) == 1
    rec = audit[0]
    for k in (
        "old_index_name",
        "new_index_name",
        "parity_gate_failure_reason",
        "release_manager_id",
        "completed_at",
    ):
        assert k in rec, f"audit record missing required key: {k}"
    assert rec["release_manager_id"] == "rm-1"
    assert rec["slo_breached"] is False


def test_slo_breach_tags_audit_and_continues() -> None:
    base = datetime(2025, 11, 18, 12, 0, 0, tzinfo=UTC)
    # Orchestrator calls now_fn() 3x: timer_started, approved.timestamp, completed_at.
    # Push completed_at to +6 min — exceeds the 5-min SLO budget.
    clock = [base, base, base + timedelta(seconds=360)]
    orch, _bus, audit, _flips = _make_orchestrator(clock=clock)

    final = asyncio.run(orch.trigger(_make_request()))

    assert final.state == "slo_breach"
    assert audit[0]["slo_breached"] is True
    assert audit[0]["elapsed_seconds"] == pytest.approx(360.0)


def test_missing_approval_aborts() -> None:
    base = datetime(2025, 11, 18, 12, 0, 0, tzinfo=UTC)
    clock = [base, base, base]
    orch, _bus, audit, flips = _make_orchestrator(clock=clock, approve="")

    with pytest.raises(orch_module.IndexRollbackError, match=r"not approved"):
        asyncio.run(orch.trigger(_make_request()))
    assert flips == [], "alias MUST NOT flip without RM approval"
    assert audit == [], "no audit append on aborted rollback"


def test_slo_deadline_helper_returns_5min_offset() -> None:
    base = datetime(2025, 11, 18, 12, 0, 0, tzinfo=UTC)
    deadline = orch_module.slo_deadline(base)
    assert (deadline - base).total_seconds() == pytest.approx(300.0)
