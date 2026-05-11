"""Real Planning sub-agent adapter (T-B03 / FR-001 / FR-060)."""

from __future__ import annotations

import httpx

from app.services.simulation.sub_agent_invoker import SubAgentReply
from app.services.simulation.sub_agents._base import call_agent


async def invoke(
    tenant_id: str, question: str, *, http_client: httpx.AsyncClient
) -> SubAgentReply:
    """Invoke the Planning agent over HTTP.

    Sources AIIMS Incident Action Plan templates and sim audit history.
    """
    return await call_agent(
        role="planning",
        endpoint_path="/planning/invoke",
        tenant_id=tenant_id,
        question=question,
        http_client=http_client,
    )
