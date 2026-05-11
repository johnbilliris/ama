"""Shared adapter helpers — HTTP request + reply parsing (T-B02..T-B07)."""

from __future__ import annotations

import logging
import os
from typing import Any

import httpx

from app.services.simulation.sub_agent_invoker import SubAgentReply
from app.services.simulation.sub_agents.citation_filter import (
    filter_citations,
)

logger = logging.getLogger(__name__)

# Default base URL for the agent Container Apps. Container Apps DI reaches
# them at this DNS name in the AU East environment; tests supply their own
# transport via the ``http_client`` parameter.
AGENTS_BASE_URL = os.getenv("AGENTS_BASE_URL", "http://agents.internal")

# Default model deployment per adapter (FR-060). The values must remain in
# lock-step with the Foundry carve-out registry under
# ``data/governance/foundry_carveout_registry.json``.
MODEL_DEPLOYMENT_BY_ROLE: dict[str, str] = {
    "monitoring": "gpt-4o-mini-australiaeast",
    "planning": "gpt-4o-mini-australiaeast",
    "risk-assessment": "gpt-4o-australiaeast",
    "communication": "gpt-4o-mini-australiaeast",
    "evacuation": "gpt-4o-australiaeast",
    "resource-allocation": "gpt-4o-mini-australiaeast",
}


async def call_agent(
    *,
    role: str,
    endpoint_path: str,
    tenant_id: str,
    question: str,
    http_client: httpx.AsyncClient,
    extra_payload: dict[str, Any] | None = None,
    read_timeout_s: float = 120.0,
) -> SubAgentReply:
    """Issue the HTTP call and translate the response into a SubAgentReply.

    Translates ``httpx.TimeoutException`` to ``asyncio.TimeoutError`` so the
    SubAgentInvoker timeout-wrapper writes the canonical ``sub_agent.timeout``
    audit entry.
    """
    body: dict[str, Any] = {
        "tenant_id": tenant_id,
        "question": question,
    }
    if extra_payload:
        body.update(extra_payload)

    try:
        resp = await http_client.post(
            f"{AGENTS_BASE_URL}{endpoint_path}",
            json=body,
            timeout=httpx.Timeout(connect=5.0, read=read_timeout_s, write=5.0, pool=5.0),
            headers={
                "X-Sim-Tenant-Context": tenant_id,
                "Content-Type": "application/json",
            },
        )
    except httpx.TimeoutException as exc:
        raise TimeoutError() from exc
    except httpx.HTTPError as exc:
        logger.warning("sub_agent.http_error role=%s err=%s", role, exc)
        return SubAgentReply(
            sub_agent=role,
            summary="",
            citations=[],
            degraded=True,
            error="service_unavailable",
            model_deployment=MODEL_DEPLOYMENT_BY_ROLE.get(role),
        )

    if resp.status_code == 503:
        return SubAgentReply(
            sub_agent=role,
            summary="",
            citations=[],
            degraded=True,
            error="service_unavailable",
            model_deployment=MODEL_DEPLOYMENT_BY_ROLE.get(role),
        )
    if resp.status_code == 429:
        return SubAgentReply(
            sub_agent=role,
            summary="",
            citations=[],
            degraded=True,
            error="rate_limit_exhausted",
            model_deployment=MODEL_DEPLOYMENT_BY_ROLE.get(role),
        )
    if resp.status_code >= 400:
        logger.warning("sub_agent.bad_status role=%s status=%s", role, resp.status_code)
        return SubAgentReply(
            sub_agent=role,
            summary="",
            citations=[],
            degraded=True,
            error=f"http_{resp.status_code}",
            model_deployment=MODEL_DEPLOYMENT_BY_ROLE.get(role),
        )

    payload = resp.json()
    raw_citations = list(payload.get("citations", []))
    safe, bad = filter_citations(raw_citations, tenant_id=tenant_id)
    summary = str(payload.get("summary", "")).strip()
    prompt_hash = payload.get("prompt_hash")
    model_deployment = payload.get("model_deployment", MODEL_DEPLOYMENT_BY_ROLE.get(role))
    invocation_id = payload.get("invocation_id") or payload.get("sub_agent_invocation_id")

    if bad:
        # FR-007: never return live-tenant citations. Audit emission lives
        # in the SubAgentInvoker timeout-wrapper / controller_service so
        # that all citation-violation cases share a single writer site.
        logger.warning(
            "sub_agent.citation_filter role=%s tenant=%s blocked=%s",
            role,
            tenant_id,
            bad,
        )
        return SubAgentReply(
            sub_agent=role,
            summary=summary,
            citations=safe,
            degraded=True,
            error="tenant_isolation_violation_filtered",
            prompt_hash=prompt_hash,
            model_deployment=model_deployment,
            sub_agent_invocation_id=invocation_id,
        )

    return SubAgentReply(
        sub_agent=role,
        summary=summary,
        citations=safe,
        prompt_hash=prompt_hash,
        model_deployment=model_deployment,
        sub_agent_invocation_id=invocation_id,
    )
