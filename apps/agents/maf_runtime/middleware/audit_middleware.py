"""Audit middleware — emits one immutable audit entry per agent invocation (FR-014, FR-015, SC-004).

This module is the **only** code path in ``apps/agents/maf_runtime/`` that opens
a Cosmos client against the ``audit_entries`` container. The static-analysis
test ``tests/unit/test_audit_writer_uniqueness.py`` (T020b) enforces that
invariant — adding a second writer module would fail CI immediately.

Audit fingerprints are SHA-256 hashes of the canonicalised input/output JSON
(sorted keys, no whitespace, ensure_ascii=True). Raw payloads are NEVER stored —
that would breach Constitution NN-3 (Privacy by design).
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import time
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from agent_framework import AgentContext, AgentMiddleware

logger = logging.getLogger(__name__)


class AuditOutcome(StrEnum):
    """Aligned with contracts/audit-entry.schema.json."""

    SUCCESS = "success"
    FAILED = "failed"
    BLOCKED_BY_CONTENT_SAFETY = "blocked_by_content_safety"
    TOOL_FAILURE = "tool_failure"
    VERSION_MISMATCH = "version_mismatch"


@dataclass
class _ToolInvocationRecord:
    tool_name: str
    version: int
    outcome: str
    latency_ms: int


@dataclass
class _AuditContext:
    """Mutable per-invocation context attached to the AgentContext."""

    incident_id: str
    run_id: str
    agent_name: str
    step_name: str
    model_tier: str
    correlation_id: str
    started_at: float = field(default_factory=time.monotonic)
    started_at_iso: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    tool_invocations: list[_ToolInvocationRecord] = field(default_factory=list)


def _canonicalise(payload: Any) -> bytes:
    """Canonicalise *payload* for fingerprinting — sorted keys, no whitespace, ensure_ascii."""

    def _default(o: Any) -> Any:
        if hasattr(o, "model_dump"):
            return o.model_dump(mode="json", by_alias=True)
        if hasattr(o, "__dict__"):
            return {k: v for k, v in o.__dict__.items() if not k.startswith("_")}
        return repr(o)

    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        default=_default,
    ).encode("utf-8")


def fingerprint(payload: Any) -> str:
    """SHA-256 hex of the canonicalised payload (NN-3: never store raw)."""
    return hashlib.sha256(_canonicalise(payload)).hexdigest()


class _CosmosAuditWriter:
    """Thin Cosmos writer — instantiated once per process, reused thread-safely.

    Uses ``DefaultAzureCredential`` against the platform Cosmos account.
    """

    def __init__(self) -> None:
        self._endpoint = os.environ.get("AZURE_COSMOS_ENDPOINT", "")
        self._db = os.environ.get("AZURE_COSMOS_DATABASE_NAME", "platform")
        self._container = os.environ.get("MAF_AUDIT_CONTAINER", "audit_entries")
        self._client: Any | None = None
        self._container_proxy: Any | None = None

    def _ensure(self) -> Any | None:
        if self._container_proxy is not None:
            return self._container_proxy
        if not self._endpoint:
            logger.warning(
                "AZURE_COSMOS_ENDPOINT not set; audit writes will be logged but not persisted."
            )
            return None
        try:
            from azure.cosmos.aio import CosmosClient
            from azure.identity.aio import DefaultAzureCredential

            self._client = CosmosClient(self._endpoint, credential=DefaultAzureCredential())
            db = self._client.get_database_client(self._db)
            self._container_proxy = db.get_container_client(self._container)
        except Exception:
            logger.exception("Failed to initialise Cosmos audit writer; audit writes will be skipped.")
            self._container_proxy = None
        return self._container_proxy

    async def write(self, document: dict[str, Any]) -> None:
        proxy = self._ensure()
        if proxy is None:
            logger.info("audit_entry (NOT persisted)", extra={"audit_entry": document})
            return
        try:
            await proxy.create_item(body=document)
        except Exception:  # noqa: BLE001 - audit must not break the agent run; rely on reconciliation (T058)
            logger.exception("Failed to persist audit entry %s", document.get("id"))


_writer: _CosmosAuditWriter | None = None


def _get_writer() -> _CosmosAuditWriter:
    global _writer
    if _writer is None:
        _writer = _CosmosAuditWriter()
    return _writer


class AuditMiddleware(AgentMiddleware):
    """Wraps every agent invocation with an immutable audit-entry write.

    Constructor args supply the per-Agent metadata that does not vary per call;
    per-invocation metadata (run_id, step_name, etc.) MUST be set on the
    AgentContext before the call by the workflow executor (T042).
    """

    def __init__(
        self,
        *,
        agent_name: str,
        model_tier: str,
        writer: _CosmosAuditWriter | None = None,
    ) -> None:
        self._agent_name = agent_name
        self._model_tier = model_tier
        self._writer = writer or _get_writer()

    @staticmethod
    def _get_correlation_id(context: AgentContext) -> str:
        # Try MAF's tracing context first; fall back to a fresh UUID4 hex (32 chars to satisfy schema).
        for attr in ("correlation_id", "trace_id"):
            value = getattr(context, attr, None)
            if value:
                return str(value).replace("-", "")[:32].ljust(32, "0")
        return uuid.uuid4().hex

    @staticmethod
    def _get_meta(context: AgentContext, key: str, default: str = "") -> str:
        meta = getattr(context, "metadata", None) or {}
        return str(meta.get(key, default))

    async def process(self, context: AgentContext, call_next: Any) -> None:  # noqa: D401
        """MAF middleware entry point — wraps the call to the next layer in the chain."""
        ctx = _AuditContext(
            incident_id=self._get_meta(context, "incident_id", "unknown"),
            run_id=self._get_meta(context, "run_id", "isolated"),
            agent_name=self._agent_name,
            step_name=self._get_meta(context, "step_name", self._agent_name),
            model_tier=self._model_tier,
            correlation_id=self._get_correlation_id(context),
        )
        # Stash on context so other middleware (otel) can read run_id linkage.
        meta = getattr(context, "metadata", None)
        if isinstance(meta, dict):
            meta.setdefault("audit_correlation_id", ctx.correlation_id)

        input_fp = fingerprint(getattr(context, "messages", None))

        outcome = AuditOutcome.SUCCESS
        failure_reason: str | None = None
        output_fp: str | None = None
        try:
            await call_next()
            output = getattr(context, "result", None)
            output_fp = fingerprint(output)
        except Exception as exc:  # noqa: BLE001 - audit captures every outcome
            outcome = self._classify_outcome(exc)
            failure_reason = f"{type(exc).__name__}: {exc}"
            raise
        finally:
            ended_at = datetime.now(UTC).isoformat()
            await self._writer.write(
                {
                    "id": str(uuid.uuid4()),
                    "incident_id": ctx.incident_id,
                    "run_id": ctx.run_id,
                    "agent_name": ctx.agent_name,
                    "step_name": ctx.step_name,
                    "model_tier": ctx.model_tier,
                    "input_fingerprint": input_fp,
                    "output_fingerprint": output_fp,
                    "correlation_id": ctx.correlation_id,
                    "started_at": ctx.started_at_iso,
                    "ended_at": ended_at,
                    "outcome": outcome.value,
                    "failure_reason": failure_reason,
                    "tool_invocations": [tc.__dict__ for tc in ctx.tool_invocations],
                }
            )

    @staticmethod
    def _classify_outcome(exc: BaseException) -> AuditOutcome:
        # Lazy imports to avoid circular dep on errors.py at import time.
        from ..errors import (
            PolicyFailure,
            ToolFailure,
            ToolVersionMismatchError,
        )

        if isinstance(exc, ToolVersionMismatchError):
            return AuditOutcome.VERSION_MISMATCH
        if isinstance(exc, ToolFailure):
            return AuditOutcome.TOOL_FAILURE
        if isinstance(exc, PolicyFailure):
            return AuditOutcome.BLOCKED_BY_CONTENT_SAFETY
        return AuditOutcome.FAILED


__all__ = ["AuditMiddleware", "AuditOutcome", "fingerprint"]
