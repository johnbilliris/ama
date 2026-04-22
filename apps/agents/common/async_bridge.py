"""Async-to-sync bridge for pipeline callers.

Allows synchronous pipeline stages to call async functions (assign_version,
deliver_handoff_with_retry, deliver_alert) without requiring full async
pipeline conversion.
"""

from __future__ import annotations

import asyncio
from collections.abc import Coroutine
from typing import Any


def run_async[T](coro: Coroutine[Any, Any, T]) -> T:
    """Run an async coroutine from synchronous code.

    - If no event loop is running: uses ``asyncio.run()``
    - If an event loop is running: creates a new thread to avoid nested loop errors
    """
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)

    # Already inside an event loop — run in a new thread
    import concurrent.futures

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(asyncio.run, coro)
        return future.result()
