"""T-D07 — controller post-turn cascade hook (FR-043).

Provides :func:`evaluate_post_turn_cascade` — a small async helper that
drives :func:`cascade_orchestrator.fan_out` on every synthetic signal
emitted during a controller turn. The hook is intentionally separate
from :class:`SimulationControllerService` so it can be unit-tested
without spinning up the full streaming machinery.

Wiring contract per T-D07:

* Triggered after each sub-agent reply.
* Awaits only the **audit-write barrier** of the orchestrator (so the
  caller is unblocked < 200 ms — the orchestrator's own dispatcher runs
  asynchronously).
* Returns the list of :class:`CascadeFanOutResult` so the controller can
  persist them in the audit envelope as ``cascade.dispatched`` entries.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Iterable
from typing import Any

from app.services.simulation.cascade_orchestrator import (
    CascadeFanOutResult,
    fan_out,
)

logger = logging.getLogger(__name__)


async def evaluate_post_turn_cascade(
    *,
    signals: Iterable[Any],
    dispatcher: Any,
    audit_writer: Any | None = None,
    parent_origin_cascade_id: str | None = None,
    timeout_seconds: float = 0.2,
) -> list[CascadeFanOutResult]:
    """Run fan-out for every signal; await only the audit-write barrier.

    The hook bounds wall-time at ``timeout_seconds`` (default 200 ms)
    so the controller turn is not blocked. Any pending fan-out beyond
    that budget is detached as a background task — its dispatcher
    coroutines continue, and the audit-write barrier has already flushed.
    """
    coros = [
        fan_out(
            trigger_signal=sig,
            dispatcher=dispatcher,
            parent_origin_cascade_id=parent_origin_cascade_id,
            audit_writer=audit_writer,
        )
        for sig in signals
    ]
    if not coros:
        return []

    done, pending = await asyncio.wait(
        [asyncio.ensure_future(c) for c in coros],
        timeout=timeout_seconds,
        return_when=asyncio.ALL_COMPLETED,
    )
    results: list[CascadeFanOutResult] = []
    for fut in done:
        try:
            results.append(fut.result())
        except Exception:  # noqa: BLE001
            logger.exception("post_turn_cascade.fan_out_failed")

    # Pending tasks are intentionally NOT awaited — but we attach a
    # done-callback so unhandled exceptions are logged (see warning re:
    # asyncio orphan tasks).
    for fut in pending:
        fut.add_done_callback(_log_pending_result)

    return results


def _log_pending_result(fut: asyncio.Future[CascadeFanOutResult]) -> None:
    try:
        fut.result()
    except Exception:  # noqa: BLE001
        logger.exception("post_turn_cascade.background_fanout_failed")


__all__ = ["evaluate_post_turn_cascade"]
