"""Unit tests for the spec-036 sequence-allocator repository (T-N02..T-N04).

The repository provides **gap-free monotonic** sequence numbers per
``simulation_id`` against the ``simulation_audit_sequence_counters``
container shipped in Wave 1 (`infra/bicep/modules/cosmos-simulation-containers.bicep`).

Behaviour invariants (per ADR-036-007):

* Cosmos optimistic concurrency via ``If-Match: <etag>`` on
  ``replace_item``; raise on 412 → bounded retry with exponential jitter.
* 5-retry budget (``MAX_RETRIES``); exhaustion raises
  :class:`SequenceAllocationExhausted` (T-N04 fail-closed surface).
* Auto-connect when ``COSMOS_ENDPOINT`` is set; in-memory fallback so
  tests run without infrastructure.
* In-memory fallback uses an ``asyncio.Lock`` per simulation to keep the
  contract under concurrent allocations.

These tests exercise the canonical code paths the audit_writer relies on
once T-N03 wires the allocator in.
"""

from __future__ import annotations

import asyncio

import pytest

from apps.api.app.repositories.simulation_sequence_repository import (
    SequenceAllocationExhausted,
    SimulationSequenceRepository,
)


@pytest.mark.asyncio
async def test_allocate_starts_at_one_for_unseen_simulation() -> None:
    repo = SimulationSequenceRepository()
    seq = await repo.allocate("sim-001")
    assert seq == 1


@pytest.mark.asyncio
async def test_allocate_is_monotonic_per_simulation() -> None:
    repo = SimulationSequenceRepository()
    seqs = [await repo.allocate("sim-002") for _ in range(5)]
    assert seqs == [1, 2, 3, 4, 5]


@pytest.mark.asyncio
async def test_allocate_isolates_across_simulations() -> None:
    repo = SimulationSequenceRepository()
    a = await repo.allocate("sim-A")
    b = await repo.allocate("sim-B")
    a2 = await repo.allocate("sim-A")
    assert (a, b, a2) == (1, 1, 2)


@pytest.mark.asyncio
async def test_concurrent_allocate_is_gap_free_and_unique() -> None:
    """100 concurrent allocations → set(values) == range(1, 101)."""

    repo = SimulationSequenceRepository()
    results = await asyncio.gather(
        *(repo.allocate("sim-conc") for _ in range(100))
    )
    assert sorted(results) == list(range(1, 101))
    assert len(set(results)) == 100


@pytest.mark.asyncio
async def test_etag_conflict_triggers_retry_then_succeeds() -> None:
    """A 412 ETag conflict on the first attempt is retried and succeeds."""

    repo = SimulationSequenceRepository()

    class _StubException(Exception):
        status_code = 412

    attempts = {"n": 0}

    async def _fake_replace(simulation_id: str, value: int, etag: str) -> str:
        attempts["n"] += 1
        if attempts["n"] == 1:
            raise _StubException("ETag mismatch")
        return f"new-etag-{value}"

    repo._replace_with_etag = _fake_replace  # type: ignore[attr-defined]
    seq = await repo.allocate("sim-retry")
    assert seq == 1
    assert attempts["n"] == 2  # retried once after the 412


@pytest.mark.asyncio
async def test_retry_exhaustion_raises_sequence_allocation_exhausted() -> None:
    """5 successive 412s → SequenceAllocationExhausted (T-N04 fail-closed)."""

    repo = SimulationSequenceRepository()

    class _StubException(Exception):
        status_code = 412

    async def _always_conflict(simulation_id: str, value: int, etag: str) -> str:
        raise _StubException("perpetual ETag mismatch")

    repo._replace_with_etag = _always_conflict  # type: ignore[attr-defined]
    with pytest.raises(SequenceAllocationExhausted) as exc:
        await repo.allocate("sim-exhaust")
    assert "sim-exhaust" in str(exc.value)


@pytest.mark.asyncio
async def test_non_412_error_is_not_retried() -> None:
    """A non-precondition error surfaces immediately (no silent retry)."""

    repo = SimulationSequenceRepository()
    attempts = {"n": 0}

    async def _fake_replace(simulation_id: str, value: int, etag: str) -> str:
        attempts["n"] += 1
        raise RuntimeError("infra failure")

    repo._replace_with_etag = _fake_replace  # type: ignore[attr-defined]
    with pytest.raises(RuntimeError):
        await repo.allocate("sim-other-error")
    assert attempts["n"] == 1


@pytest.mark.asyncio
async def test_reset_for_tests_clears_state() -> None:
    repo = SimulationSequenceRepository()
    await repo.allocate("sim-reset")
    repo.reset_for_tests()
    seq = await repo.allocate("sim-reset")
    assert seq == 1
