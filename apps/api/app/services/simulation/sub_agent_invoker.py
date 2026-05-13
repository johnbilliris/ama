"""Bridge from the Controller's ``query_sub_agent`` tool to the existing services.

Spec-036 / T-B08 / T-B12 / T-B14 (FR-002 migration step 4):

* :func:`production_invoker` is now the only adapter factory — it wires the
  real adapters under :mod:`apps.api.app.services.simulation.sub_agents`.
* The legacy ``default_invoker`` stub block has been **deleted** per T-B14
  (FR-002 migration step 4). The trip-wire literal documented in
  ``tools.simulation_stub_sweep.TRIP_WIRE`` no longer appears anywhere
  in the production code path.
* The ``invoke`` method applies a soft-ack at ``T+5 s`` (FR-006) and a
  hard timeout at ``T+120 s``, falling back to a degraded reply on timeout.
* Kebab-case role aliases (``risk-assessment``, ``resource-allocation``)
  coexist with the legacy snake-case names for one deprecation window.
"""

from __future__ import annotations

import asyncio
import logging
import os
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import httpx

logger = logging.getLogger(__name__)

# T-B12 timeout budget — sourced from the contract:
SOFT_ACK_SECONDS = float(os.getenv("SIM_SUBAGENT_SOFT_ACK_SECONDS", "5"))
HARD_TIMEOUT_SECONDS = float(os.getenv("SIM_SUBAGENT_HARD_TIMEOUT_SECONDS", "120"))

SoftAckCallback = Callable[[str], Awaitable[None]]


@dataclass
class SubAgentReply:
    sub_agent: str
    summary: str
    citations: list[str]
    degraded: bool = False
    error: str | None = None
    # Spec-036 / FR-060 — populated by production adapters (None for stub adapters).
    prompt_hash: str | None = None
    model_deployment: str | None = None
    sub_agent_invocation_id: str | None = None


SubAgentFn = Callable[[str, str], Awaitable[SubAgentReply]]


class SubAgentInvoker:
    def __init__(
        self,
        *,
        soft_ack_callback: SoftAckCallback | None = None,
        soft_ack_seconds: float = SOFT_ACK_SECONDS,
        hard_timeout_seconds: float = HARD_TIMEOUT_SECONDS,
    ) -> None:
        self._adapters: dict[str, SubAgentFn] = {}
        self._soft_ack_callback = soft_ack_callback
        self._soft_ack_seconds = soft_ack_seconds
        self._hard_timeout_seconds = hard_timeout_seconds

    def register(self, name: str, fn: SubAgentFn) -> None:
        self._adapters[name] = fn

    def register_alias(self, alias: str, target: str) -> None:
        """Register *alias* → *target* (e.g. kebab → snake)."""
        if target not in self._adapters:
            raise KeyError(f"target adapter {target!r} not registered")
        self._adapters[alias] = self._adapters[target]

    def available(self) -> list[str]:
        return sorted(self._adapters.keys())

    async def _emit_soft_ack(self, sub_agent: str) -> None:
        try:
            await asyncio.sleep(self._soft_ack_seconds)
        except asyncio.CancelledError:
            return
        if self._soft_ack_callback is not None:
            try:
                await self._soft_ack_callback(sub_agent)
            except Exception:  # pragma: no cover - defensive
                logger.exception("sub_agent.soft_ack_callback_error sub_agent=%s", sub_agent)

    async def invoke(
        self,
        sub_agent: str,
        question: str,
        *,
        tenant_id: str,
        timeout_s: float | None = None,
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
        hard_timeout = timeout_s if timeout_s is not None else self._hard_timeout_seconds
        soft_ack_task = asyncio.create_task(self._emit_soft_ack(sub_agent))
        try:
            return await asyncio.wait_for(fn(tenant_id, question), timeout=hard_timeout)
        except TimeoutError:
            logger.warning("sub_agent.timeout sub_agent=%s tenant=%s", sub_agent, tenant_id)
            return SubAgentReply(
                sub_agent=sub_agent,
                summary=f"Sub-agent '{sub_agent}' did not respond within {hard_timeout:.0f}s.",
                citations=[],
                degraded=True,
                error="timeout",
            )
        except asyncio.CancelledError:
            logger.info("sub_agent.cancel sub_agent=%s tenant=%s", sub_agent, tenant_id)
            raise
        except Exception as exc:  # noqa: BLE001
            logger.exception("sub_agent.error sub_agent=%s", sub_agent)
            return SubAgentReply(
                sub_agent=sub_agent,
                summary=f"Sub-agent '{sub_agent}' errored: {exc}",
                citations=[],
                degraded=True,
                error="error",
            )
        finally:
            soft_ack_task.cancel()


def default_invoker() -> SubAgentInvoker:
    """Empty invoker used in unit tests that don't need the production adapters.

    Per T-B14 the legacy stub adapters have been **deleted**. Callers
    that don't pass an ``http_client`` get an invoker with no registered
    handlers; ``invoke`` returns a degraded reply via the unknown-sub-agent
    fall-through path. Production code MUST call :func:`production_invoker`
    or :func:`select_invoker` with a real ``httpx.AsyncClient``.
    """
    return SubAgentInvoker()


def production_invoker(
    http_client: httpx.AsyncClient,
    *,
    soft_ack_callback: SoftAckCallback | None = None,
) -> SubAgentInvoker:
    """Wire the real sub-agent adapters (FR-001 / spec-036).

    Each adapter under :mod:`apps.api.app.services.simulation.sub_agents`
    issues an HTTP call to the corresponding agent Container App and
    populates ``prompt_hash`` / ``model_deployment`` /
    ``sub_agent_invocation_id`` on :class:`SubAgentReply` (FR-060).

    The Controller selects this factory when
    ``SIM_CONTROLLER_MODE=production``; the stub registrations from
    :func:`default_invoker` are no longer used.
    """
    # Local imports keep this module import-light when stubs are sufficient
    # (e.g. unit tests that don't have httpx wired). Imported via the
    # ``app.`` namespace because the API container's Dockerfile copies
    # ``apps/api/app/ → ./app/`` and the ``apps.api.app`` namespace does
    # not exist in the runtime image (see memory: api packaging).
    from app.services.simulation.sub_agents import (
        communication_adapter,
        evacuation_adapter,
        monitoring_adapter,
        planning_adapter,
        resource_allocation_adapter,
        risk_assessment_adapter,
    )

    invoker = SubAgentInvoker(soft_ack_callback=soft_ack_callback)
    invoker.register(
        "monitoring",
        lambda t, q: monitoring_adapter.invoke(t, q, http_client=http_client),
    )
    invoker.register(
        "planning",
        lambda t, q: planning_adapter.invoke(t, q, http_client=http_client),
    )
    invoker.register(
        "risk-assessment",
        lambda t, q: risk_assessment_adapter.invoke(t, q, http_client=http_client),
    )
    invoker.register(
        "communication",
        lambda t, q: communication_adapter.invoke(t, q, http_client=http_client),
    )
    invoker.register(
        "evacuation",
        lambda t, q: evacuation_adapter.invoke(t, q, http_client=http_client),
    )
    invoker.register(
        "resource-allocation",
        lambda t, q: resource_allocation_adapter.invoke(t, q, http_client=http_client),
    )
    # Snake-case aliases for one deprecation window:
    invoker.register_alias("risk_assessment", "risk-assessment")
    invoker.register_alias("resource_allocation", "resource-allocation")
    return invoker


def select_invoker(
    *,
    http_client: httpx.AsyncClient | None = None,
    soft_ack_callback: SoftAckCallback | None = None,
) -> SubAgentInvoker:
    """Always returns the production adapter graph when an ``http_client`` is supplied.

    Per T-B14 (FR-002 migration step 4) the legacy ``SIM_CONTROLLER_MODE``
    environment-variable feature-flag is **removed**. The only branch
    remaining is "production" — callers that cannot supply an
    ``http_client`` (e.g. unit tests) get an empty invoker via
    :func:`default_invoker`.
    """
    if http_client is not None:
        return production_invoker(http_client, soft_ack_callback=soft_ack_callback)
    return default_invoker()
