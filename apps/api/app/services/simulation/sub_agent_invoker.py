"""Bridge from the Controller's ``query_sub_agent`` tool to the existing services."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Awaitable, Callable

logger = logging.getLogger(__name__)


@dataclass
class SubAgentReply:
    sub_agent: str
    summary: str
    citations: list[str]
    degraded: bool = False
    error: str | None = None


SubAgentFn = Callable[[str, str], Awaitable[SubAgentReply]]


class SubAgentInvoker:
    def __init__(self) -> None:
        self._adapters: dict[str, SubAgentFn] = {}

    def register(self, name: str, fn: SubAgentFn) -> None:
        self._adapters[name] = fn

    def available(self) -> list[str]:
        return sorted(self._adapters.keys())

    async def invoke(
        self, sub_agent: str, question: str, *, tenant_id: str, timeout_s: float = 30.0
    ) -> SubAgentReply:
        fn = self._adapters.get(sub_agent)
        if fn is None:
            return SubAgentReply(
                sub_agent=sub_agent,
                summary=f"Unknown sub-agent '{sub_agent}'.",
                citations=[],
                degraded=True,
                error="unknown_sub_agent",
            )
        try:
            return await asyncio.wait_for(fn(tenant_id, question), timeout=timeout_s)
        except asyncio.TimeoutError:
            logger.warning("sub_agent.timeout sub_agent=%s tenant=%s", sub_agent, tenant_id)
            return SubAgentReply(
                sub_agent=sub_agent,
                summary=f"Sub-agent '{sub_agent}' did not respond within {timeout_s:.0f}s.",
                citations=[],
                degraded=True,
                error="timeout",
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("sub_agent.error sub_agent=%s", sub_agent)
            return SubAgentReply(
                sub_agent=sub_agent,
                summary=f"Sub-agent '{sub_agent}' errored: {exc}",
                citations=[],
                degraded=True,
                error="error",
            )


def default_invoker() -> SubAgentInvoker:
    invoker = SubAgentInvoker()

    async def _stub(agent: str, prefix: str) -> SubAgentReply:
        return SubAgentReply(
            sub_agent=agent,
            summary=f"{prefix}: simulated reply (no data source wired in this environment).",
            citations=[],
        )

    async def monitoring(tenant_id: str, q: str) -> SubAgentReply:
        return await _stub("monitoring", f"Monitoring[{tenant_id}] → '{q[:60]}'")

    async def planning(tenant_id: str, q: str) -> SubAgentReply:
        return await _stub("planning", f"Planning[{tenant_id}] → '{q[:60]}'")

    async def resource_allocation(tenant_id: str, q: str) -> SubAgentReply:
        return await _stub("resource_allocation", f"Resources[{tenant_id}] → '{q[:60]}'")

    async def communication(tenant_id: str, q: str) -> SubAgentReply:
        return await _stub("communication", f"Comms[{tenant_id}] → '{q[:60]}'")

    async def evacuation(tenant_id: str, q: str) -> SubAgentReply:
        return await _stub("evacuation", f"Evacuation[{tenant_id}] → '{q[:60]}'")

    async def risk_assessment(tenant_id: str, q: str) -> SubAgentReply:
        return await _stub("risk_assessment", f"Risk[{tenant_id}] → '{q[:60]}'")

    invoker.register("monitoring", monitoring)
    invoker.register("planning", planning)
    invoker.register("resource_allocation", resource_allocation)
    invoker.register("communication", communication)
    invoker.register("evacuation", evacuation)
    invoker.register("risk_assessment", risk_assessment)
    return invoker
