"""T-B08 / T-B12 / T-B14 sub_agent_invoker unit tests.

Post T-B14: ``default_invoker`` returns an empty invoker (the trip-wire
stub block has been deleted). Production adapters are exercised via
:func:`production_invoker` with a mocked httpx client in
``apps/api/tests/test_sub_agent_invoker_production.py``.
"""

from __future__ import annotations

import asyncio

import pytest

from apps.api.app.services.simulation.sub_agent_invoker import (
    SubAgentInvoker,
    SubAgentReply,
    default_invoker,
)


@pytest.mark.asyncio
async def test_default_invoker_is_empty_after_t_b14() -> None:
    """T-B14 removed the stub registrations from ``default_invoker``."""
    inv = default_invoker()
    available = inv.available()
    assert available == [] or available == ()


@pytest.mark.asyncio
async def test_unknown_sub_agent_returns_degraded() -> None:
    inv = default_invoker()
    reply = await inv.invoke("does-not-exist", "q", tenant_id="sim-tenant-a")
    assert reply.degraded is True
    assert reply.error == "unknown_sub_agent"


@pytest.mark.asyncio
async def test_hard_timeout_returns_degraded() -> None:
    inv = SubAgentInvoker(soft_ack_seconds=0.05, hard_timeout_seconds=0.1)

    async def slow(_t: str, _q: str) -> SubAgentReply:
        await asyncio.sleep(2.0)
        return SubAgentReply(sub_agent="x", summary="never", citations=[])

    inv.register("slow-agent", slow)
    reply = await inv.invoke("slow-agent", "q", tenant_id="sim-tenant-a")
    assert reply.degraded is True
    assert reply.error == "timeout"


@pytest.mark.asyncio
async def test_soft_ack_callback_fires() -> None:
    fired: list[str] = []

    async def cb(name: str) -> None:
        fired.append(name)

    inv = SubAgentInvoker(soft_ack_callback=cb, soft_ack_seconds=0.02, hard_timeout_seconds=2.0)

    async def slow(_t: str, _q: str) -> SubAgentReply:
        await asyncio.sleep(0.1)
        return SubAgentReply(sub_agent="x", summary="ok", citations=[])

    inv.register("x", slow)
    reply = await inv.invoke("x", "q", tenant_id="sim-tenant-a")
    assert reply.degraded is False
    assert fired == ["x"]
