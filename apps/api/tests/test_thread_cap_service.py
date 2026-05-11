"""Phase D — thread-cap service tests (T-D01 / FR-052)."""

from __future__ import annotations

import asyncio

import pytest

from apps.api.app.services.simulation.thread_cap_service import (
    THREAD_CAP,
    ThreadCapService,
)

pytestmark = pytest.mark.asyncio


async def test_add_returns_true_until_cap_reached() -> None:
    svc = ThreadCapService()
    sim_id = "sim-001"
    for i in range(THREAD_CAP):
        assert await svc.add(sim_id, f"thread-{i}") is True
    assert await svc.add(sim_id, "thread-overflow") is False
    assert await svc.is_full(sim_id) is True


async def test_add_idempotent_on_existing_thread() -> None:
    svc = ThreadCapService()
    sim_id = "sim-002"
    assert await svc.add(sim_id, "thread-A") is True
    assert await svc.add(sim_id, "thread-A") is True
    assert len(await svc.list_active(sim_id)) == 1


async def test_remove_releases_slot_and_allows_new_thread() -> None:
    svc = ThreadCapService()
    sim_id = "sim-003"
    for i in range(THREAD_CAP):
        await svc.add(sim_id, f"thread-{i}")
    assert await svc.add(sim_id, "thread-overflow") is False
    assert await svc.remove(sim_id, "thread-0") is True
    assert await svc.add(sim_id, "thread-overflow") is True


async def test_concurrent_adds_never_exceed_cap() -> None:
    """50 concurrent adders — never exceed cap of 5 (FR-052)."""
    svc = ThreadCapService()
    sim_id = "sim-concurrent"

    async def attempt(thread_id: str) -> bool:
        return await svc.add(sim_id, thread_id)

    results = await asyncio.gather(*[attempt(f"thread-{i}") for i in range(50)])
    assert sum(1 for r in results if r) == THREAD_CAP
    assert len(await svc.list_active(sim_id)) == THREAD_CAP
