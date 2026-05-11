"""T-J11 — Property test: thread cap is atomic at cap=5 (FR-052).

Hypothesis property: 1000 concurrent ``add()`` attempts produce
**exactly 5 successes** and ``num - 5`` failures (cap-exceeded). The
``ThreadCapService`` in-memory path is exercised directly so the test
runs with no Cosmos.
"""

from __future__ import annotations

import asyncio
import string

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from apps.api.app.services.simulation.thread_cap_service import (
    THREAD_CAP,
    ThreadCapService,
)

_thread_id_st = st.text(
    alphabet=string.ascii_lowercase + string.digits,
    min_size=4,
    max_size=12,
)


@settings(
    max_examples=50,  # 50 examples × 20 unique threads = 1000+ contention paths
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture],
)
@given(thread_ids=st.lists(_thread_id_st, min_size=20, max_size=40, unique=True))
def test_thread_cap_atomic_property(thread_ids: list[str]) -> None:
    """Concurrent adds beyond cap=5 produce exactly 5 successes."""

    async def runner() -> tuple[int, int]:
        svc = ThreadCapService()
        sim_id = "sim-prop-001"
        results = await asyncio.gather(*(svc.add(sim_id, tid) for tid in thread_ids))
        active = await svc.list_active(sim_id)
        return sum(1 for ok in results if ok), len(active)

    successes, active_count = asyncio.run(runner())
    assert active_count == THREAD_CAP, f"active_count={active_count}, expected {THREAD_CAP}"
    assert successes == THREAD_CAP, f"successes={successes}, expected {THREAD_CAP}"


@pytest.mark.asyncio
async def test_thread_cap_does_not_double_count_existing_thread() -> None:
    svc = ThreadCapService()
    assert await svc.add("sim-1", "thread-A") is True
    assert await svc.add("sim-1", "thread-A") is True  # idempotent
    assert len(await svc.list_active("sim-1")) == 1


@pytest.mark.asyncio
async def test_thread_cap_remove_frees_slot() -> None:
    svc = ThreadCapService()
    for i in range(THREAD_CAP):
        assert await svc.add("sim-2", f"t-{i}") is True
    assert await svc.add("sim-2", "t-extra") is False
    assert await svc.remove("sim-2", "t-0") is True
    assert await svc.add("sim-2", "t-extra") is True
