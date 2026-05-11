"""Cancellation scope for simulation aborts/pauses (T-E05 / FR-059).

Tracks in-flight ``asyncio.Task`` handles per simulation so that
``POST /api/simulations/{simId}/abort`` can:

1. Cancel every in-flight task within ~1 s.
2. Emit one ``sub_agent.cancel`` audit entry per cancelled invocation.
3. Honour the FR-059 cancelled-invocations contract on the abort response.

The scope is process-local — production wiring expects a Redis-backed
shared cancellation set when scaled across container apps; the in-memory
mapping below is sufficient for the single-replica test surface and the
chaos-test harness.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class _Tracked:
    task: asyncio.Task[Any]
    sub_agent: str
    correlation_id: str | None


_REGISTRY: dict[str, list[_Tracked]] = {}
_LOCK = asyncio.Lock()


async def register(
    *,
    simulation_id: str,
    task: asyncio.Task[Any],
    sub_agent: str,
    correlation_id: str | None = None,
) -> None:
    """Track *task* against *simulation_id* for later cancellation."""
    async with _LOCK:
        _REGISTRY.setdefault(simulation_id, []).append(
            _Tracked(task=task, sub_agent=sub_agent, correlation_id=correlation_id)
        )


async def deregister(*, simulation_id: str, task: asyncio.Task[Any]) -> None:
    async with _LOCK:
        items = _REGISTRY.get(simulation_id, [])
        _REGISTRY[simulation_id] = [t for t in items if t.task is not task]


async def cancel_all(
    *,
    simulation_id: str,
    reason: str = "aborted",
    on_cancel: Callable[[str, str | None, str], Awaitable[None]] | None = None,
) -> int:
    """Cancel every in-flight task for *simulation_id*.

    *on_cancel* is invoked once per cancelled task with
    ``(sub_agent, correlation_id, reason)`` so the caller can write
    ``sub_agent.cancel`` audit entries.

    Returns the count of cancelled invocations (FR-059).
    """
    async with _LOCK:
        tracked = _REGISTRY.pop(simulation_id, [])

    cancelled = 0
    for t in tracked:
        if t.task.done():
            continue
        t.task.cancel()
        cancelled += 1
        if on_cancel is not None:
            try:
                await on_cancel(t.sub_agent, t.correlation_id, reason)
            except Exception:  # pragma: no cover - defensive
                logger.exception(
                    "cancellation.on_cancel_callback_failed sim=%s sub_agent=%s",
                    simulation_id,
                    t.sub_agent,
                )
    if cancelled and tracked:
        await asyncio.sleep(0)  # yield once so cancellation propagates
    return cancelled


def list_in_flight(simulation_id: str) -> list[str]:
    """Test/inspection helper — returns sub_agent names of in-flight tasks."""
    return [t.sub_agent for t in _REGISTRY.get(simulation_id, [])]


def reset_for_tests() -> None:
    _REGISTRY.clear()


__all__ = [
    "cancel_all",
    "deregister",
    "list_in_flight",
    "register",
    "reset_for_tests",
]
