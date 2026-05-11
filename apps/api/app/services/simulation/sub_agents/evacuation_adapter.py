"""Real Evacuation sub-agent adapter (T-B06 / FR-001 / FR-060)."""

from __future__ import annotations

import httpx

from app.services.simulation.sub_agent_invoker import SubAgentReply
from app.services.simulation.sub_agents._base import call_agent


async def invoke(
    tenant_id: str, question: str, *, http_client: httpx.AsyncClient
) -> SubAgentReply:
    """Invoke the Evacuation agent (gpt-4o)."""
    return await call_agent(
        role="evacuation",
        endpoint_path="/evacuation/invoke",
        tenant_id=tenant_id,
        question=question,
        http_client=http_client,
    )
