"""Real Resource-Allocation sub-agent adapter (T-B07 / FR-001 / FR-060)."""

from __future__ import annotations

import httpx
from app.services.simulation.sub_agent_invoker import SubAgentReply
from app.services.simulation.sub_agents._base import call_agent


async def invoke(tenant_id: str, question: str, *, http_client: httpx.AsyncClient) -> SubAgentReply:
    """Invoke the Resource-Allocation agent."""
    return await call_agent(
        role="resource-allocation",
        endpoint_path="/resource-allocation/invoke",
        tenant_id=tenant_id,
        question=question,
        http_client=http_client,
    )
