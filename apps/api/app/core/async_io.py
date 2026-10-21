"""Bounded offloading of blocking storage I/O away from the shared API event loop.

The simulation repositories and services use the synchronous Azure Cosmos / Blob
SDKs. Calling them directly inside ``async def`` handlers blocks the single
shared event loop that also serves live ingestion traffic. Every such call is
routed through :func:`run_blocking`, which runs the callable in a worker thread
(``asyncio.to_thread`` copies the current ``contextvars`` context, so tenant
scoping is preserved) while a per-loop semaphore caps how many simulation
storage calls may occupy threads at once.
"""

from __future__ import annotations

import asyncio
import os
from collections.abc import Awaitable, Callable, Sequence
from typing import Any, TypeVar
from weakref import WeakKeyDictionary

T = TypeVar("T")

DEFAULT_STORAGE_IO_WORKERS = 8
_ENV_VAR = "SIMULATION_STORAGE_IO_WORKERS"

_semaphores: WeakKeyDictionary[asyncio.AbstractEventLoop, tuple[int, asyncio.Semaphore]] = WeakKeyDictionary()


def storage_io_limit() -> int:
    """Maximum simulation storage calls allowed in worker threads concurrently."""
    raw = os.environ.get(_ENV_VAR, "")
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return DEFAULT_STORAGE_IO_WORKERS
    return value if value > 0 else DEFAULT_STORAGE_IO_WORKERS


def _loop_semaphore() -> asyncio.Semaphore:
    loop = asyncio.get_running_loop()
    limit = storage_io_limit()
    cached = _semaphores.get(loop)
    if cached is None or cached[0] != limit:
        cached = (limit, asyncio.Semaphore(limit))
        _semaphores[loop] = cached
    return cached[1]


async def run_blocking[T](func: Callable[..., T], /, *args: Any, **kwargs: Any) -> T:
    """Run a blocking storage call off the event loop under the shared bound."""
    async with _loop_semaphore():
        return await asyncio.to_thread(func, *args, **kwargs)


async def gather_bounded[T](
    awaitables: Sequence[Awaitable[T]],
    *,
    limit: int | None = None,
) -> list[T]:
    """Await work in fixed-size batches so inline bulk jobs cannot fan out unbounded."""
    batch_size = limit if limit and limit > 0 else storage_io_limit()
    results: list[T] = []
    for start in range(0, len(awaitables), batch_size):
        results.extend(await asyncio.gather(*awaitables[start : start + batch_size]))
    return results
