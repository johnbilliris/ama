"""Tests for spec-036 T-N03 / T-N04 — audit_writer wired to the
distributed sequence allocator with fail-closed DLQ on exhaustion.

Acceptance per tasks.md (Phase N):

* ``AuditWriter.write`` no longer increments a process-local
  ``_sequence_counters`` dict — it delegates allocation to a
  :class:`SimulationSequenceRepository` (T-N02 / ADR-036-007).
* On :class:`SequenceAllocationExhausted` the writer fails closed by
  writing a DLQ envelope (``sequence_number=-1``) and re-raising
  :class:`SequenceAllocationExhausted` so the route handler can surface
  HTTP 503 + ``Retry-After: 5`` (T-N04 / FR-048).
* Concurrent writes to the same simulation produce a strictly monotonic
  zero-gap sequence (the allocator's invariant flows through the writer).
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime

import pytest

from apps.api.app.repositories.simulation_sequence_repository import (
    DLQ_SEQUENCE_NUMBER,
    SequenceAllocationExhausted,
    SimulationSequenceRepository,
)
from apps.api.app.services.simulation.audit_writer import (
    AuditDLQEntry,
    AuditWriter,
    get_audit_dlq_buffer,
    reset_audit_writer_for_tests,
)


@pytest.fixture(autouse=True)
def _isolate_audit_state() -> None:
    reset_audit_writer_for_tests()
    yield
    reset_audit_writer_for_tests()


@pytest.mark.asyncio
async def test_audit_writer_uses_injected_sequence_repository() -> None:
    """The writer takes its sequence number from the injected repository."""

    repo = SimulationSequenceRepository()
    writer = AuditWriter(sequence_repository=repo)
    env = await writer.write(
        "lifecycle.paused",
        simulation_id="sim-W3-N03",
        details={"attempted_action": "chat_turn"},
    )
    assert env.sequence_number == 1

    env2 = await writer.write(
        "lifecycle.resumed",
        simulation_id="sim-W3-N03",
        details={
            "coordinator_user_id": "coord-1",
            "previous_paused_duration_seconds": 5,
        },
    )
    assert env2.sequence_number == 2


@pytest.mark.asyncio
async def test_audit_writer_concurrent_writes_remain_gap_free() -> None:
    """100 concurrent ``write`` calls → sequence_numbers == range(1, 101)."""

    repo = SimulationSequenceRepository()
    writer = AuditWriter(sequence_repository=repo)

    async def _one_write(_i: int) -> int:
        env = await writer.write(
            "lifecycle.paused",
            simulation_id="sim-conc-N03",
            details={"attempted_action": "chat_turn"},
        )
        return env.sequence_number

    seqs = await asyncio.gather(*[_one_write(i) for i in range(100)])
    assert sorted(seqs) == list(range(1, 101))
    assert len(set(seqs)) == 100


@pytest.mark.asyncio
async def test_audit_writer_fail_closed_writes_dlq_on_exhaustion() -> None:
    """Sequence allocator exhaustion → DLQ entry written + raised."""

    repo = SimulationSequenceRepository()

    async def _always_exhausted(simulation_id: str) -> int:
        raise SequenceAllocationExhausted(f"forced exhaustion for {simulation_id}")

    repo.allocate = _always_exhausted  # type: ignore[method-assign]
    writer = AuditWriter(sequence_repository=repo)

    with pytest.raises(SequenceAllocationExhausted):
        await writer.write(
            "lifecycle.paused",
            simulation_id="sim-DLQ",
            details={"attempted_action": "chat_turn"},
        )

    dlq = get_audit_dlq_buffer()
    assert len(dlq) == 1
    entry = dlq[0]
    assert isinstance(entry, AuditDLQEntry)
    assert entry.simulation_id == "sim-DLQ"
    assert entry.sequence_number == DLQ_SEQUENCE_NUMBER
    assert entry.entry_type == "lifecycle.paused"
    assert entry.dlq_reason == "sequence_allocator_exhausted"
    # Carries the ISO-formatted attempted timestamp.
    assert isinstance(entry.attempted_at, datetime)


@pytest.mark.asyncio
async def test_audit_writer_default_singleton_initialises_repository() -> None:
    """The default ``get_audit_writer`` provisions a sequence repo on first use."""

    from apps.api.app.services.simulation.audit_writer import get_audit_writer

    writer = get_audit_writer()
    env = await writer.write(
        "lifecycle.aborted",
        simulation_id="sim-singleton",
        details={
            "coordinator_user_id": "coord-x",
            "cancelled_invocations": 0,
            "abort_timestamp": datetime.now(UTC),
        },
    )
    assert env.sequence_number == 1
