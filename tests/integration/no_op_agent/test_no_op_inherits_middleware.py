"""No-op agent fixture (T057, SC-005, SC-010 worked example).

A synthetic Agent + 10-line module that proves the cross-cutting middleware
applies uniformly without per-agent code (FR-013, FR-014, FR-015) and that a
new agent needs only a thin module + YAML to become operational (SC-010).
"""

from __future__ import annotations

import asyncio
from typing import Any

import pytest
from pydantic import BaseModel

from apps.agents.maf_runtime.middleware import (
    AuditMiddleware,
    ContentSafetyMiddleware,
    OtelMiddleware,
)


class NoOpOutput(BaseModel):
    echo: str


class _NoOpAgent:
    """The 10-line no-op agent. NO audit/safety/OTel code lives here."""

    name = "no_op"

    async def run(self, payload: dict[str, Any]) -> NoOpOutput:
        return NoOpOutput(echo=str(payload.get("text", "")))


class _DummyContext:
    def __init__(self, *, messages: Any, metadata: dict[str, Any] | None = None) -> None:
        self.messages = messages
        self.metadata = metadata or {}
        self.result: Any = None
        self.correlation_id = "no-op-trace"


class _NullAuditWriter:
    def __init__(self) -> None:
        self.entries: list[dict[str, Any]] = []

    async def write(self, document: dict[str, Any]) -> None:
        self.entries.append(document)


def _wrap(maybe_async_callable: Any) -> Any:
    async def _call() -> None:
        result = maybe_async_callable()
        if asyncio.iscoroutine(result):
            await result

    return _call


def test_no_op_agent_inherits_audit_via_middleware() -> None:
    """SC-005 / SC-010 invariant: a brand-new agent gets audit entries for free."""
    writer = _NullAuditWriter()
    audit_mw = AuditMiddleware(agent_name="no_op", model_tier="drafting", writer=writer)
    safety_mw = ContentSafetyMiddleware()
    otel_mw = OtelMiddleware(agent_name="no_op")

    ctx = _DummyContext(
        messages="please log this",
        metadata={"incident_id": "INC-test", "run_id": "run-test", "step_name": "no_op"},
    )

    async def call_no_op() -> None:
        ctx.result = await _NoOpAgent().run({"text": "hello"})

    async def chain() -> None:
        async def inner() -> None:
            await audit_mw.process(ctx, _wrap(call_no_op))

        async def via_otel() -> None:
            await otel_mw.process(ctx, _wrap(inner))

        await safety_mw.process(ctx, _wrap(via_otel))

    asyncio.run(chain())

    assert isinstance(ctx.result, NoOpOutput)
    assert len(writer.entries) == 1
    entry = writer.entries[0]
    assert entry["agent_name"] == "no_op"
    assert entry["outcome"] == "success"
    assert entry["incident_id"] == "INC-test"
    # NN-3 invariant: fingerprints, never raw text.
    assert "please log this" not in str(entry)
    assert entry["input_fingerprint"]
    assert entry["output_fingerprint"]


@pytest.mark.parametrize("payload", [{"text": "fire"}, {"text": ""}])
def test_no_op_runs_in_isolation(payload: dict[str, Any]) -> None:
    out = asyncio.run(_NoOpAgent().run(payload))
    assert isinstance(out, NoOpOutput)
    assert out.echo == payload["text"]
