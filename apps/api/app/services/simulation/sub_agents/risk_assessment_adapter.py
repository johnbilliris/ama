"""Real Risk-Assessment sub-agent adapter (T-B04 / FR-001 / FR-060)."""

from __future__ import annotations

import httpx

from app.services.simulation.sub_agent_invoker import SubAgentReply
from app.services.simulation.sub_agents._base import call_agent


async def invoke(
    tenant_id: str,
    question: str,
    *,
    http_client: httpx.AsyncClient,
    triggering_signal_id: str | None = None,
) -> SubAgentReply:
    """Invoke the Risk-Assessment agent (gpt-4o)."""
    extra: dict[str, str] = {}
    if triggering_signal_id is not None:
        extra["triggering_signal_id"] = triggering_signal_id
    return await call_agent(
        role="risk-assessment",
        endpoint_path="/risk-assessment/invoke",
        tenant_id=tenant_id,
        question=question,
        http_client=http_client,
        extra_payload=extra or None,
    )
