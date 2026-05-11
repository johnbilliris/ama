"""Real Communication sub-agent adapter (T-B05 / FR-001 / FR-039 / FR-060)."""

from __future__ import annotations

import httpx

from app.services.simulation.sub_agent_invoker import SubAgentReply
from app.services.simulation.sub_agents._base import call_agent


async def invoke(
    tenant_id: str, question: str, *, http_client: httpx.AsyncClient
) -> SubAgentReply:
    """Invoke the Communication agent.

    Generates AWS warning drafts that are watermarked with
    "SIMULATION — DO NOT DISTRIBUTE" before being persisted (FR-039).
    """
    return await call_agent(
        role="communication",
        endpoint_path="/communication/invoke",
        tenant_id=tenant_id,
        question=question,
        http_client=http_client,
    )
