"""Real Monitoring sub-agent adapter (T-B02 / FR-001 / FR-060)."""

from __future__ import annotations

import httpx

from app.services.simulation.sub_agent_invoker import SubAgentReply
from app.services.simulation.sub_agents._base import call_agent


async def invoke(
    tenant_id: str, question: str, *, http_client: httpx.AsyncClient
) -> SubAgentReply:
    """Invoke the Monitoring agent over HTTP.

    Reads sim-tenant signal pipeline state and returns observations.
    """
    return await call_agent(
        role="monitoring",
        endpoint_path="/monitoring/invoke",
        tenant_id=tenant_id,
        question=question,
        http_client=http_client,
    )
