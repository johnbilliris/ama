"""T-D07 — controller cascade post-turn hook integration test."""

from __future__ import annotations

import time
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from apps.api.app.services.simulation.controller_cascade_hook import (
    evaluate_post_turn_cascade,
)


def _make_signal(category: str, **kwargs: Any) -> MagicMock:
    sig = MagicMock()
    sig.simulation_id = kwargs.get("simulation_id", "sim-d07")
    sig.tenant_id = kwargs.get("tenant_id", "sim-tenant-d07")
    sig.signal_id = kwargs.get("signal_id", "sig-1")
    sig.category = category
    sig.confidence = kwargs.get("confidence", 0.8)
    sig.parameters = kwargs.get("parameters", {})
    return sig


@pytest.mark.asyncio
async def test_hook_dispatches_within_200ms() -> None:
    dispatcher = AsyncMock()
    audit = MagicMock()
    audit.write = AsyncMock()
    sig = _make_signal("hazard-telemetry")
    start = time.perf_counter()
    # Use a tighter timeout so the hook itself is well inside the FR-043
    # 200 ms barrier — leave a small margin for OS scheduling overhead.
    results = await evaluate_post_turn_cascade(
        signals=[sig],
        dispatcher=dispatcher,
        audit_writer=audit,
        timeout_seconds=0.05,
    )
    elapsed = time.perf_counter() - start
    assert elapsed < 0.2, f"post-turn hook MUST return inside the 200 ms barrier; got {elapsed:.3f}s"
    assert isinstance(results, list)


@pytest.mark.asyncio
async def test_hook_handles_zero_signals() -> None:
    dispatcher = AsyncMock()
    results = await evaluate_post_turn_cascade(signals=[], dispatcher=dispatcher)
    assert results == []
    dispatcher.assert_not_awaited()


@pytest.mark.asyncio
async def test_hook_supports_depth2_refusal_via_parent_correlation() -> None:
    """When parent_origin_cascade_id is supplied the orchestrator refuses."""
    dispatcher = AsyncMock()
    audit = MagicMock()
    audit.write = AsyncMock()
    sig = _make_signal("hazard-telemetry")
    results = await evaluate_post_turn_cascade(
        signals=[sig],
        dispatcher=dispatcher,
        audit_writer=audit,
        parent_origin_cascade_id="parent-xxx",
    )
    assert any(r.skipped_reason == "depth2_refused" for r in results)
    audit.write.assert_called_once()
    assert audit.write.call_args.args[0] == "cascade.depth2_refused"


@pytest.mark.asyncio
async def test_hook_does_not_propagate_dispatcher_exception() -> None:
    """Even if the dispatcher raises for one role, the hook must return."""

    async def flaky_dispatch(role: str, prompt: str, origin: str) -> None:
        if role == "RoleX":
            raise RuntimeError("flaky")

    sig = _make_signal("hazard-telemetry")
    audit = MagicMock()
    audit.write = AsyncMock()
    results = await evaluate_post_turn_cascade(
        signals=[sig],
        dispatcher=flaky_dispatch,
        audit_writer=audit,
    )
    # No exception leaked to caller.
    assert isinstance(results, list)
