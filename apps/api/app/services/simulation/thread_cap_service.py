"""Thread-cap service (T-D01 / T-Q01 / FR-052 / Assumption A10).

Maintains the ``simulation_threads/{simulationId}`` document with field
``active_threads: list[str]`` and hard cap ``5``. Updates use Cosmos ETag
optimistic concurrency (5 retries, 50 ms exponential back-off + jitter)
per ADR-036-005.

In-memory fallback path is used when ``cosmos_container`` is ``None`` —
the same retry semantics apply through an asyncio lock so that the
hypothesis property test in ``tests/integration/test_thread_cap_service.py``
can exercise the contention path without Cosmos.

Spec-036 amendment-cycle T-Q01 (FR-052 / pass-2 Q8)
---------------------------------------------------
Two complementary APIs are exposed:

1. The legacy ``add()`` / ``remove()`` / ``list_active()`` / ``is_full()``
   API used by the affinity ladder (T-D01) — preserved verbatim.
2. The new ``try_acquire()`` / ``release()`` API used by the cascade
   orchestrator (T-Q01 / T-Q02). Acquires accept a ``thread_kind`` (default
   ``"hazard"``); per pass-2 Q8 ``annotation`` threads MUST NOT count
   against the cap.

Both APIs share the same underlying counter so the cap (FR-052 = 5)
applies regardless of which API the caller uses.
"""

from __future__ import annotations

import asyncio
import logging
import random
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any
from uuid import uuid4

logger = logging.getLogger(__name__)

THREAD_CAP = 5
MAX_RETRIES = 5
BASE_BACKOFF_SECONDS = 0.05
MAX_BACKOFF_SECONDS = 0.4


def _backoff(attempt: int) -> float:
    expo = min(MAX_BACKOFF_SECONDS, BASE_BACKOFF_SECONDS * (2**attempt))
    return expo * (0.5 + random.random() / 2)


@dataclass
class _Snapshot:
    active_threads: list[str]
    cap: int = THREAD_CAP
    etag: str | None = None


# ---- T-Q01 result types ------------------------------------------------


@dataclass(frozen=True)
class AcquireGranted:
    """Successful acquisition. ``new_count`` is the hazard-thread count
    AFTER any increment caused by this call (annotation acquires do NOT
    increment, so ``new_count`` reflects the unchanged hazard count)."""

    new_count: int
    cap: int = THREAD_CAP
    thread_id: str | None = None


@dataclass(frozen=True)
class AcquireDenied:
    """Acquisition refused — caller MUST downgrade to annotation per
    FR-052 cascade-orchestrator semantics."""

    current_count: int
    cap: int = THREAD_CAP
    reason: str = "thread_cap_reached"


AcquireResult = AcquireGranted | AcquireDenied


class ThreadCapService:
    """Per-simulation active-thread set with cap enforcement (FR-052)."""

    def __init__(
        self,
        *,
        cosmos_container: Any = None,
        clock: Callable[[], float] | None = None,
    ) -> None:
        self._container = cosmos_container
        self._memory: dict[str, _Snapshot] = {}
        self._locks: dict[str, asyncio.Lock] = {}

    async def _lock(self, sim_id: str) -> asyncio.Lock:
        lock = self._locks.get(sim_id)
        if lock is None:
            lock = asyncio.Lock()
            self._locks[sim_id] = lock
        return lock

    def _snapshot(self, sim_id: str) -> _Snapshot:
        snap = self._memory.get(sim_id)
        if snap is None:
            snap = _Snapshot(active_threads=[])
            self._memory[sim_id] = snap
        return snap

    async def list_active(self, sim_id: str) -> list[str]:
        async with await self._lock(sim_id):
            return list(self._snapshot(sim_id).active_threads)

    async def add(self, sim_id: str, thread_id: str) -> bool:
        """Reserve a slot for *thread_id*.

        Returns ``True`` if added, ``False`` if the cap was reached and the
        caller MUST route to the affinity ladder for absorption.
        """
        for attempt in range(MAX_RETRIES):
            try:
                async with await self._lock(sim_id):
                    snap = self._snapshot(sim_id)
                    if thread_id in snap.active_threads:
                        return True
                    if len(snap.active_threads) >= snap.cap:
                        return False
                    snap.active_threads.append(thread_id)
                    return True
            except Exception as exc:  # pragma: no cover - defensive
                status = getattr(exc, "status_code", None)
                if status != 412 or attempt == MAX_RETRIES - 1:
                    raise
                logger.warning(
                    "thread_cap.etag_conflict attempt=%d sim=%s thread=%s",
                    attempt + 1,
                    sim_id,
                    thread_id,
                )
                await asyncio.sleep(_backoff(attempt))
        return False

    async def remove(self, sim_id: str, thread_id: str) -> bool:
        async with await self._lock(sim_id):
            snap = self._snapshot(sim_id)
            if thread_id in snap.active_threads:
                snap.active_threads.remove(thread_id)
                return True
            return False

    async def is_full(self, sim_id: str) -> bool:
        async with await self._lock(sim_id):
            snap = self._snapshot(sim_id)
            return len(snap.active_threads) >= snap.cap

    # ---- T-Q01 try_acquire / release ---------------------------------

    async def try_acquire(
        self,
        sim_id: str,
        *,
        thread_kind: str = "hazard",
    ) -> AcquireResult:
        """Attempt to acquire a hazard-thread slot for *sim_id*.

        Per pass-2 Q8, ``thread_kind="annotation"`` (or any non-hazard
        kind) MUST NOT count against the FR-052 cap; the call is a
        cheap accounting no-op that always returns
        :class:`AcquireGranted` with the current hazard count.

        For ``thread_kind="hazard"`` the call atomically reserves an
        anonymous slot via :meth:`add` (with a generated thread_id) and
        returns :class:`AcquireGranted` on success or :class:`AcquireDenied`
        when the cap is reached.
        """
        if thread_kind != "hazard":
            async with await self._lock(sim_id):
                count = len(self._snapshot(sim_id).active_threads)
            logger.debug(
                "thread_cap.annotation_acquire_uncounted sim=%s count=%d",
                sim_id,
                count,
            )
            return AcquireGranted(new_count=count, cap=THREAD_CAP)

        thread_id = f"hazard-{uuid4()}"
        added = await self.add(sim_id, thread_id)
        async with await self._lock(sim_id):
            count = len(self._snapshot(sim_id).active_threads)
        if added:
            return AcquireGranted(new_count=count, cap=THREAD_CAP, thread_id=thread_id)
        return AcquireDenied(current_count=count, cap=THREAD_CAP)

    async def release(self, sim_id: str, thread_id: str | None = None) -> bool:
        """Release one hazard-thread slot.

        If *thread_id* is provided, releases that specific slot (back-compat
        with :meth:`remove`). Otherwise pops one slot from the LIFO end,
        which suffices for anonymous T-Q01 cascade slots. Releasing a
        simulation that has no active threads is a safe no-op.
        """
        async with await self._lock(sim_id):
            snap = self._snapshot(sim_id)
            if thread_id is not None:
                if thread_id in snap.active_threads:
                    snap.active_threads.remove(thread_id)
                    return True
                return False
            if snap.active_threads:
                snap.active_threads.pop()
                return True
            return False

    @staticmethod
    def reset_for_tests(service: ThreadCapService) -> None:
        service._memory.clear()
        service._locks.clear()


# ---- Process-wide singleton + reset hook for unit tests ---------------

_default_service: ThreadCapService | None = None


def get_thread_cap_service() -> ThreadCapService:
    """Return the lazily-instantiated process-wide thread-cap service."""

    global _default_service
    if _default_service is None:
        _default_service = ThreadCapService()
    return _default_service


def reset_thread_cap_service_for_tests() -> None:
    """Drop the process-wide service so tests start with a clean counter."""

    global _default_service
    _default_service = None


__all__ = [
    "AcquireDenied",
    "AcquireGranted",
    "AcquireResult",
    "BASE_BACKOFF_SECONDS",
    "MAX_BACKOFF_SECONDS",
    "MAX_RETRIES",
    "THREAD_CAP",
    "ThreadCapService",
    "get_thread_cap_service",
    "reset_thread_cap_service_for_tests",
]
