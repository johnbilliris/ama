"""Spec-036 Wave 4 — T-Q06 property-based thread-cap test.

Per FR-052: at most 5 hazard threads may be active per simulation;
attempts beyond the cap MUST be denied (no silent drop). Annotation
threads are EXCLUDED from the cap (they are absorbed into existing
hazard threads via the affinity ladder).

This module asserts:

1. For any N ≤ 20 hazard ``try_acquire`` calls, the first 5 succeed and
   the remaining N-5 are denied (FR-052 cap).
2. Annotation ``try_acquire`` calls NEVER count against the cap (Q8).
3. Releasing a granted thread frees a slot for the next hazard request.
"""

from __future__ import annotations

import asyncio

from hypothesis import given, settings
from hypothesis import strategies as st

from apps.api.app.services.simulation.thread_cap_service import (
    THREAD_CAP,
    AcquireDenied,
    AcquireGranted,
    ThreadCapService,
)

SIM_ID = "11111111-2222-3333-4444-555555555555"


def _run(coro):
    return asyncio.new_event_loop().run_until_complete(coro)


@given(n_attempts=st.integers(min_value=1, max_value=20))
@settings(max_examples=100, deadline=None)
def test_property_cap_denies_after_five_grants(n_attempts: int) -> None:
    """For any N≤20 hazard try_acquire calls, exactly min(N, 5) succeed."""

    svc = ThreadCapService()

    async def _scenario() -> tuple[int, int]:
        granted = denied = 0
        for _ in range(n_attempts):
            res = await svc.try_acquire(SIM_ID, thread_kind="hazard")
            if isinstance(res, AcquireGranted):
                granted += 1
            elif isinstance(res, AcquireDenied):
                denied += 1
        return granted, denied

    granted, denied = _run(_scenario())
    assert granted == min(n_attempts, THREAD_CAP)
    assert denied == max(0, n_attempts - THREAD_CAP)


@given(n_annotations=st.integers(min_value=0, max_value=20))
@settings(max_examples=50, deadline=None)
def test_property_annotation_threads_dont_count_against_cap(n_annotations: int) -> None:
    """Annotation threads MUST NOT consume hazard slots (per Q8)."""

    svc = ThreadCapService()

    async def _scenario() -> int:
        # Issue all annotation acquires first.
        for _ in range(n_annotations):
            await svc.try_acquire(SIM_ID, thread_kind="annotation")
        # Then request 5 hazards — all 5 must succeed regardless of
        # how many annotation threads were created beforehand.
        granted = 0
        for _ in range(THREAD_CAP):
            res = await svc.try_acquire(SIM_ID, thread_kind="hazard")
            if isinstance(res, AcquireGranted):
                granted += 1
        return granted

    granted = _run(_scenario())
    assert granted == THREAD_CAP


def test_release_frees_a_slot() -> None:
    """Releasing a hazard thread MUST allow a new try_acquire to succeed."""

    svc = ThreadCapService()

    async def _scenario():
        first_thread_id = None
        # Fill the cap.
        for _ in range(THREAD_CAP):
            res = await svc.try_acquire(SIM_ID, thread_kind="hazard")
            assert isinstance(res, AcquireGranted)
            if first_thread_id is None:
                first_thread_id = res.thread_id
        # Next attempt fails.
        denied = await svc.try_acquire(SIM_ID, thread_kind="hazard")
        assert isinstance(denied, AcquireDenied)
        # Release one slot; next attempt should succeed.
        await svc.release(SIM_ID, first_thread_id)
        granted = await svc.try_acquire(SIM_ID, thread_kind="hazard")
        assert isinstance(granted, AcquireGranted)

    _run(_scenario())
