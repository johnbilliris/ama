"""Unit tests for spec-036 T-P01 — simulation lifecycle-state persistence.

Per tasks.md §9 (Phase P) and FR-059:

* Lifecycle state is one of ``active`` / ``paused`` / ``aborted``.
* Updates use ETag-conditional concurrency to prevent torn writes when
  pause / resume / abort fire concurrently.
* The repository augments the existing ``simulation`` container (no new
  container per the task's "Choose augment to avoid new container" note).
"""

from __future__ import annotations

import pytest

from apps.api.app.services.simulation.repositories.simulation_state import (
    ETagConflictError,
    SimulationStateRepository,
    UnknownSimulationError,
)


@pytest.mark.asyncio
async def test_default_state_is_active() -> None:
    repo = SimulationStateRepository()
    await repo.bootstrap("sim-1")

    record = await repo.read("sim-1")
    assert record.state == "active"


@pytest.mark.asyncio
async def test_pause_then_resume_round_trip() -> None:
    repo = SimulationStateRepository()
    await repo.bootstrap("sim-1")

    initial = await repo.read("sim-1")
    paused = await repo.update_state(
        simulation_id="sim-1",
        new_state="paused",
        expected_etag=initial.etag,
    )
    assert paused.state == "paused"
    assert paused.etag != initial.etag

    resumed = await repo.update_state(
        simulation_id="sim-1",
        new_state="active",
        expected_etag=paused.etag,
    )
    assert resumed.state == "active"


@pytest.mark.asyncio
async def test_abort_is_terminal_state() -> None:
    """``aborted`` is the terminal state — no further updates are accepted."""

    repo = SimulationStateRepository()
    await repo.bootstrap("sim-1")
    initial = await repo.read("sim-1")

    aborted = await repo.update_state("sim-1", "aborted", initial.etag)
    assert aborted.state == "aborted"

    with pytest.raises(ValueError):
        await repo.update_state("sim-1", "active", aborted.etag)


@pytest.mark.asyncio
async def test_etag_conflict_raises_when_stale() -> None:
    """A stale ``expected_etag`` triggers the constitution fail-closed path."""

    repo = SimulationStateRepository()
    await repo.bootstrap("sim-1")
    initial = await repo.read("sim-1")

    # First update wins.
    await repo.update_state("sim-1", "paused", initial.etag)

    # Second update presenting the original (now-stale) ETag must fail.
    with pytest.raises(ETagConflictError):
        await repo.update_state("sim-1", "aborted", initial.etag)


@pytest.mark.asyncio
async def test_read_unknown_sim_raises() -> None:
    repo = SimulationStateRepository()
    with pytest.raises(UnknownSimulationError):
        await repo.read("missing")


@pytest.mark.asyncio
async def test_update_unknown_sim_raises() -> None:
    repo = SimulationStateRepository()
    with pytest.raises(UnknownSimulationError):
        await repo.update_state("missing", "paused", expected_etag="anything")


@pytest.mark.asyncio
async def test_unknown_target_state_rejected() -> None:
    repo = SimulationStateRepository()
    await repo.bootstrap("sim-1")
    initial = await repo.read("sim-1")

    with pytest.raises(ValueError):
        await repo.update_state("sim-1", "running", initial.etag)  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_lifecycle_state_record_is_frozen() -> None:
    repo = SimulationStateRepository()
    await repo.bootstrap("sim-1")
    record = await repo.read("sim-1")

    with pytest.raises((TypeError, ValueError)):
        record.state = "paused"  # type: ignore[misc]


@pytest.mark.asyncio
async def test_paused_to_paused_no_op_still_advances_etag() -> None:
    """Idempotent re-pause is permitted but the ETag is refreshed."""

    repo = SimulationStateRepository()
    await repo.bootstrap("sim-1")
    initial = await repo.read("sim-1")

    paused = await repo.update_state("sim-1", "paused", initial.etag)
    second = await repo.update_state("sim-1", "paused", paused.etag)
    assert second.state == "paused"
    assert second.etag != paused.etag
