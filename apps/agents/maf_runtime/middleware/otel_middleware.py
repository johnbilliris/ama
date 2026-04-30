"""OpenTelemetry middleware — adds ``workflow.*`` span attributes (FR-016).

MAF auto-emits ``ai.agent.name``, ``ai.agent.model``, ``ai.tokens.input``,
``ai.tokens.output``, etc. via the AzureMonitor exporter (configured by
``observability.setup_observability_once``). This middleware adds the workflow-
linkage attributes our operator dashboards (T060) and reconciliation job (T058)
depend on:

- ``workflow.run_id``        — links span to ``workflow_runs.id``
- ``workflow.step``          — name of the agent step
- ``workflow.parent_trace_id`` — top-level run trace id (so a child span rolls up)

Resilient: a failing exporter does not break agent execution (covered by
``observability.setup_observability_once``'s broad except, plus the safety net
inside ``_set_attribute`` here).
"""

from __future__ import annotations

import logging
from typing import Any

from agent_framework import AgentContext, AgentMiddleware

logger = logging.getLogger(__name__)


def _set_attribute(span: Any, key: str, value: Any) -> None:
    """Defensive set_attribute that swallows exporter failures."""
    if span is None:
        return
    try:
        span.set_attribute(key, value)
    except Exception:  # noqa: BLE001 - never break the agent run on telemetry failure
        logger.debug("OTel set_attribute(%s) failed; ignoring", key, exc_info=True)


class OtelMiddleware(AgentMiddleware):
    """Adds custom workflow.* attributes to MAF-emitted spans."""

    def __init__(self, *, agent_name: str) -> None:
        self._agent_name = agent_name

    async def process(self, context: AgentContext, call_next: Any) -> None:  # noqa: D401
        # Lazy import so a missing OTel install never breaks module import.
        try:
            from opentelemetry import trace
        except ImportError:
            await call_next()
            return

        meta = getattr(context, "metadata", None) or {}
        run_id = meta.get("run_id", "isolated")
        step_name = meta.get("step_name", self._agent_name)
        parent_trace_id = meta.get("parent_trace_id", "")

        tracer = trace.get_tracer("ama.maf_runtime")
        with tracer.start_as_current_span(f"agent.{self._agent_name}.{step_name}") as span:
            _set_attribute(span, "workflow.run_id", str(run_id))
            _set_attribute(span, "workflow.step", str(step_name))
            if parent_trace_id:
                _set_attribute(span, "workflow.parent_trace_id", str(parent_trace_id))
            _set_attribute(span, "ai.agent.name", self._agent_name)
            await call_next()


__all__ = ["OtelMiddleware"]
