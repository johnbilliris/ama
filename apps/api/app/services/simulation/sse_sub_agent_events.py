"""SSE publisher helpers for sub-agent invocation events (T-B10 / FR-003).

Emits canonical SSE events on the simulation chat stream:

* ``sub_agent.started``   — emitted the moment the adapter is dispatched.
* ``sub_agent.completed`` — emitted when the adapter returns successfully.
* ``sub_agent.degraded``  — emitted when the adapter returns
  ``degraded=True`` (timeout, citation-violation, rate-limit).

The helpers are framework-agnostic — they return the canonical
:class:`ChatEvent` instances which the FastAPI route flushes over SSE via
``event.to_sse()``.

Spec references:
* `contracts/sse-map-overlay.md` (16 layer types)
* FR-003 (≤ 1 s first delta / soft-ack visibility)
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any


@dataclass
class SubAgentSSEEvent:
    """Lightweight equivalent of ``ChatEvent`` — keeps this module dependency-free."""

    event: str
    data: dict[str, Any]


def started(*, sub_agent: str, correlation_id: str | None = None) -> SubAgentSSEEvent:
    """Emit the ``sub_agent.started`` event."""
    payload: dict[str, Any] = {"sub_agent": sub_agent, "phase": "started"}
    if correlation_id is not None:
        payload["correlation_id"] = correlation_id
    return SubAgentSSEEvent(event="sub_agent.started", data=payload)


def completed(
    *,
    sub_agent: str,
    summary: str,
    citations: Iterable[str] | None = None,
    correlation_id: str | None = None,
    prompt_hash: str | None = None,
    model_deployment: str | None = None,
) -> SubAgentSSEEvent:
    """Emit the ``sub_agent.completed`` event."""
    payload: dict[str, Any] = {
        "sub_agent": sub_agent,
        "phase": "completed",
        "summary": summary,
        "citations": list(citations or []),
    }
    if correlation_id is not None:
        payload["correlation_id"] = correlation_id
    if prompt_hash is not None:
        payload["prompt_hash"] = prompt_hash
    if model_deployment is not None:
        payload["model_deployment"] = model_deployment
    return SubAgentSSEEvent(event="sub_agent.completed", data=payload)


def degraded(
    *,
    sub_agent: str,
    error: str,
    correlation_id: str | None = None,
    summary: str | None = None,
) -> SubAgentSSEEvent:
    """Emit the ``sub_agent.degraded`` event.

    ``error`` is the canonical reason code (``timeout``,
    ``rate_limit_exhausted``, ``service_unavailable``,
    ``tenant_isolation_violation_filtered``, ``unknown_sub_agent``).
    """
    payload: dict[str, Any] = {
        "sub_agent": sub_agent,
        "phase": "degraded",
        "error": error,
    }
    if summary is not None:
        payload["summary"] = summary
    if correlation_id is not None:
        payload["correlation_id"] = correlation_id
    return SubAgentSSEEvent(event="sub_agent.degraded", data=payload)


def soft_ack(*, sub_agent: str, correlation_id: str | None = None) -> SubAgentSSEEvent:
    """Emit the ``ack.working`` event (FR-006 soft-ack at T+5 s)."""
    payload: dict[str, Any] = {"sub_agent": sub_agent}
    if correlation_id is not None:
        payload["correlation_id"] = correlation_id
    return SubAgentSSEEvent(event="ack.working", data=payload)


# Canonical sub-agent SSE event-type set — exported so contract tests can
# assert it stays in lock-step with the SSE map overlay contract.
SUB_AGENT_SSE_EVENT_TYPES: tuple[str, ...] = (
    "sub_agent.started",
    "sub_agent.completed",
    "sub_agent.degraded",
    "ack.working",
)


def format_sse_event(event_name: str, payload: Any) -> str:
    """Serialise *payload* as an SSE chunk: ``event: …\\ndata: …\\n\\n``.

    Module-local helper used by the map-overlay publisher and any other
    SSE writer that does not have access to the global ``ChatEvent``
    serialiser. Kept dependency-free so it can be imported from anywhere
    in the simulation namespace without dragging in FastAPI.
    """
    import json as _json

    body = _json.dumps(payload, default=str, separators=(",", ":"))
    return f"event: {event_name}\ndata: {body}\n\n"
