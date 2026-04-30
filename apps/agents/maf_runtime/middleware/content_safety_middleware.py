"""Content safety middleware — refuses agent invocation on policy block (FR-013).

Wraps the existing ``ContentSafetyValidator`` and ``ContentSafetyCircuitBreaker``
from ``apps/agents/common/`` so the long-tested 3-layer pipeline (Azure AI
Content Safety primary, keyword fallback, AWS-tier alignment) governs every
MAF agent invocation through a single hook.

Edge cases covered:
- Blocked input → raises ``PolicyFailure`` BEFORE the LLM is called.
- Circuit open → falls back to keyword check (existing FR-007/FR-008 contract).
- Resumed Communication-agent step (run already in ``AwaitingApproval``) that
  blocks on safety → marks the run for cancellation via the audit metadata so
  the outer executor can transition to ``Cancelled`` with
  ``failure_reason="content_safety_rejected"`` and notify the commander queue.
"""

from __future__ import annotations

import logging
from typing import Any

from agent_framework import AgentContext, AgentMiddleware
from common.content_safety import ContentSafetyValidator

from ..errors import PolicyFailure

logger = logging.getLogger(__name__)


class ContentSafetyMiddleware(AgentMiddleware):
    """Apply content safety validation to every agent invocation."""

    def __init__(
        self,
        *,
        validator: ContentSafetyValidator | None = None,
        max_input_length: int = 8000,
    ) -> None:
        self._validator = validator or ContentSafetyValidator()
        self._max_input_length = max_input_length

    @staticmethod
    def _extract_text(context: AgentContext) -> str:
        """Best-effort extraction of the agent's input text for content-safety scanning."""
        messages = getattr(context, "messages", None) or getattr(context, "input", None)
        if messages is None:
            return ""
        if isinstance(messages, str):
            return messages
        # MAF Message types expose `.text` or `.content`; otherwise stringify.
        chunks: list[str] = []
        items = messages if isinstance(messages, list) else [messages]
        for m in items:
            for attr in ("text", "content", "value"):
                v = getattr(m, attr, None)
                if isinstance(v, str):
                    chunks.append(v)
                    break
            else:
                chunks.append(str(m))
        return "\n".join(chunks)

    async def process(self, context: AgentContext, call_next: Any) -> None:  # noqa: D401
        text = self._extract_text(context)
        if not text:
            await call_next()
            return

        result = self._validator.validate(text=text, max_length=self._max_input_length)
        if not result.passed:
            meta = getattr(context, "metadata", None)
            correlation_id = ""
            if isinstance(meta, dict):
                correlation_id = str(meta.get("audit_correlation_id", "")) or ""
                # Signal to the outer workflow executor that this run was blocked
                # at the safety boundary while paused on HITL — see edge case
                # "Content safety rejection at the middleware layer for an alert
                # that is already in 'pending approval'".
                meta["content_safety_rejected"] = True
                meta["content_safety_reason"] = result.reason or result.result
            logger.warning(
                "content_safety_blocked",
                extra={
                    "reason": result.reason,
                    "result": result.result,
                    "validation_method": result.validation_method,
                    "correlation_id": correlation_id,
                },
            )
            raise PolicyFailure(
                f"Content safety blocked agent invocation: {result.reason or result.result}",
                correlation_id=correlation_id or "unknown",
                run_id=str((meta or {}).get("run_id")) if isinstance(meta, dict) else None,
                details={
                    "reason": result.reason,
                    "result": result.result,
                    "validation_method": result.validation_method,
                },
            )

        await call_next()


__all__ = ["ContentSafetyMiddleware"]
