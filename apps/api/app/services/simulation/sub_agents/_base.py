"""Shared adapter helpers — HTTP request + reply parsing (T-B02..T-B07)."""

from __future__ import annotations

import logging
import os
from typing import Any, Literal

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


def _nullable_string(payload: dict[str, Any], key: str) -> str | None:
    value = payload.get(key)
    if value is not None and not isinstance(value, str):
        raise ValueError(f"Invalid dispatcher {key}")
    return value


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
        )

    if resp.status_code == 503:
        return SubAgentReply(
            sub_agent=role,
            summary="",
            citations=[],
            degraded=True,
            error="service_unavailable",
        )
    if resp.status_code == 429:
        return SubAgentReply(
            sub_agent=role,
            summary="",
            citations=[],
            degraded=True,
            error="rate_limit_exhausted",
        )
    if resp.status_code >= 400:
        logger.warning("sub_agent.bad_status role=%s status=%s", role, resp.status_code)
        return SubAgentReply(
            sub_agent=role,
            summary="",
            citations=[],
            degraded=True,
            error=f"http_{resp.status_code}",
        )

    payload = resp.json()
    raw_citations = list(payload.get("citations", []))
    safe, bad = filter_citations(raw_citations, tenant_id=tenant_id)
    summary = str(payload.get("summary", "")).strip()
    prompt_hash = payload.get("prompt_hash")
    model_deployment = _nullable_string(payload, "model_deployment")
    invocation_id = payload.get("invocation_id") or payload.get("sub_agent_invocation_id")
    attempted = payload.get("inference_attempted")
    if attempted is not None and type(attempted) is not bool:
        raise ValueError("Invalid dispatcher inference_attempted")
    outcome: Literal["succeeded", "failed", "not_attempted", "unknown"] | None = payload.get(
        "inference_outcome", "unknown"
    )
    if outcome not in ("succeeded", "failed", "not_attempted", "unknown", None):
        raise ValueError("Invalid dispatcher inference_outcome")
    model_id = _nullable_string(payload, "model_id")
    model_version = _nullable_string(payload, "model_version")
    remote_error = _nullable_string(payload, "error")
    degraded = payload.get("degraded", False)
    if type(degraded) is not bool:
        raise ValueError("Invalid dispatcher degraded")
    if "inference_attempted" in payload and attempted is not True:
        model_deployment = model_id = model_version = None

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
            model_id=model_id,
            model_version=model_version,
            inference_attempted=attempted,
            inference_outcome=outcome,
        )

    return SubAgentReply(
        sub_agent=role,
        summary=summary,
        citations=safe,
        prompt_hash=prompt_hash,
        model_deployment=model_deployment,
        sub_agent_invocation_id=invocation_id,
        degraded=degraded,
        error=remote_error,
        model_id=model_id,
        model_version=model_version,
        inference_attempted=attempted,
        inference_outcome=outcome,
    )
