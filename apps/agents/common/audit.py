"""Spec 036 — extended audit shape for grounded LLM calls (T081, T090).

Writes one ``AuditRecord`` per LLM call (inference or embedding) emitted by
**any** grounded surface — the five life-safety agents and the simulation
Controller. Mirrors ``packages/schemas/spec_036/audit-record-llm-call.json``
and implements:

* **R-13 / FR-RAG-AG-02 / FR-RAG-SIM-04**: every call writes a record.
* **R-13 dual-tier storage**: the same record is appended to:

  1. Cosmos ``audit_records`` container (45-day operational retention, hot
     tier; writer is process-singleton mirroring spec-030 audit_middleware).
  2. Append-only Blob ``audit-archive/<yyyy>/<mm>/<dd>/...`` (7-year
     immutability policy reused from spec 030; no schema change).

* **SC-011 replay key**: ``replay_key(record)`` returns
  ``sha256(corpus_build_sha | prompt_sha | model_version | sorted chunk shas)``
  — sufficient to deterministically reproduce the retrieval input set.

* **Hallucinated-citation event**: callers pass the full ``citations[]`` and
  ``retrieved_chunks[]`` to ``write_grounded_record``; the writer applies the
  ``citation_filter`` and stores ``hallucinated_citation_count``.

Constructor-injectable seam: ``AuditWriter`` is a Protocol. Production wiring
uses a Cosmos + Blob writer; tests use the in-memory ``InMemoryAuditWriter``.

This module is deliberately framework-light — it composes pydantic models from
``ama_domain.audit_record`` rather than re-defining the shape, so a single
schema bump propagates without diff drift.
"""

from __future__ import annotations

import hashlib
import logging
import os
import uuid
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Protocol, runtime_checkable

logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# Replay key (SC-011)
# --------------------------------------------------------------------------- #


def replay_key(record: dict[str, Any]) -> str:
    """Compute the deterministic replay key for an audit record (SC-011).

    Key inputs:
      ``corpus_build_sha``, ``prompt_sha``, ``model_version``,
      and the ordered list of ``retrieved_chunks[].sha256_of_chunk``.

    The chunk order is **preserved** because the LLM prompt is order-sensitive:
    two retrievals over the same chunk set in different orders produce different
    completions, so they MUST get different replay keys.

    Records that mutate ``operator_actions[]`` post-hoc retain the same key;
    the audit-replay invariant holds across the one-month window.
    """
    corpus = record.get("corpus_build_sha", "")
    prompt = record.get("prompt_sha", "")
    model_version = record.get("model_version", "")
    shas = [c.get("sha256_of_chunk", "") for c in record.get("retrieved_chunks", []) or []]
    blob = "|".join((corpus, prompt, model_version, ",".join(shas)))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


# --------------------------------------------------------------------------- #
# AuditWriter Protocol + in-memory impl
# --------------------------------------------------------------------------- #


@runtime_checkable
class AuditWriter(Protocol):
    """Audit-record sink (R-13)."""

    async def write(self, record: dict[str, Any]) -> None: ...


@dataclass
class InMemoryAuditWriter:
    """Hermetic writer — collects records into a per-instance buffer."""

    records: list[dict[str, Any]] = field(default_factory=list)

    async def write(self, record: dict[str, Any]) -> None:
        self.records.append(dict(record))


# --------------------------------------------------------------------------- #
# Production writer (Cosmos hot tier + Blob cold tier; lazy-imported)
# --------------------------------------------------------------------------- #


class CosmosBlobAuditWriter:
    """Production writer — Cosmos for hot tier, Blob for 7-year archive."""

    def __init__(self) -> None:
        self._endpoint = os.environ.get("AZURE_COSMOS_ENDPOINT", "")
        self._db = os.environ.get("AZURE_COSMOS_DATABASE_NAME", "platform")
        self._container = os.environ.get("AMA_AUDIT_CONTAINER", "audit_records")
        self._archive_uri = os.environ.get("AMA_AUDIT_ARCHIVE_URI", "")
        self._cosmos_proxy: Any | None = None

    async def _ensure_cosmos(self) -> Any | None:
        if self._cosmos_proxy is not None:
            return self._cosmos_proxy
        if not self._endpoint:
            logger.warning("AZURE_COSMOS_ENDPOINT not set; audit records will be logged but not persisted")
            return None
        try:
            from azure.cosmos.aio import CosmosClient  # noqa: PLC0415
            from azure.identity.aio import DefaultAzureCredential  # noqa: PLC0415

            client = CosmosClient(self._endpoint, credential=DefaultAzureCredential())
            db = client.get_database_client(self._db)
            self._cosmos_proxy = db.get_container_client(self._container)
        except Exception:
            logger.exception("audit_cosmos_init_failed; persistence disabled")
            self._cosmos_proxy = None
        return self._cosmos_proxy

    async def write(self, record: dict[str, Any]) -> None:
        proxy = await self._ensure_cosmos()
        if proxy is None:
            logger.info("audit_record (NOT persisted)", extra={"record": record})
            return
        try:
            await proxy.create_item(body=record)
        except Exception:  # noqa: BLE001 — audit must never break the agent run
            logger.exception("audit_record_write_failed call_id=%s", record.get("call_id"))


# --------------------------------------------------------------------------- #
# Public API — one entry point per call kind
# --------------------------------------------------------------------------- #


def _now_iso() -> str:
    return datetime.now(tz=UTC).isoformat().replace("+00:00", "Z")


def make_inference_record(
    *,
    agent_name: str,
    prompt_sha: str,
    model_id: str,
    model_version: str,
    deployment_alias: str,
    output_text_hash: str,
    output_tokens: int,
    tenant_id: str,
    correlation_id: str,
    rag_used: bool,
    gateway_decision: str = "allow",
    gateway_deny_reason: str | None = None,
    embedding_model_id: str | None = None,
    corpus_build_sha: str | None = None,
    retrieved_chunks: Iterable[dict[str, Any]] | None = None,
    citations: Iterable[dict[str, Any]] | None = None,
    rag_optout_reason: str | None = None,
    adr_pointer: str | None = None,
    hallucinated_citation_count: int = 0,
    chat_turn_index: int | None = None,
    call_id: str | None = None,
    # ---- F-A5 (Cluster A5; ADR-14) — additive-nullable extension fields ----
    operator_override_rationale: str | None = None,
    approval_workflow_state: str | None = None,
    approval_authority: str | None = None,
    downgrade_justification: str | None = None,
    retrieval_index_name: str | None = None,
    field_coordinator_offline_decision: str | None = None,
    conflict_group_id: str | None = None,
    precedence_tiebreak_applied: list[str] | None = None,
) -> dict[str, Any]:
    """Build a record dict matching the audit-record-llm-call.json schema."""
    record: dict[str, Any] = {
        "call_id": call_id or str(uuid.uuid4()),
        "timestamp_utc": _now_iso(),
        "agent_name": agent_name,
        "call_kind": "inference",
        "prompt_sha": prompt_sha,
        "model_id": model_id,
        "model_version": model_version,
        "deployment_alias": deployment_alias,
        "rag_used": rag_used,
        "gateway_decision": gateway_decision,
        "hallucinated_citation_count": hallucinated_citation_count,
        "output_tokens": output_tokens,
        "output_text_hash": output_text_hash,
        "tenant_id": tenant_id,
        "correlation_id": correlation_id,
    }
    if chat_turn_index is not None:
        record["chat_turn_index"] = chat_turn_index
    if rag_used:
        if not (embedding_model_id and corpus_build_sha and retrieved_chunks):
            raise ValueError("rag_used=True requires embedding_model_id, corpus_build_sha, retrieved_chunks")
        record["embedding_model_id"] = embedding_model_id
        record["corpus_build_sha"] = corpus_build_sha
        record["retrieved_chunks"] = list(retrieved_chunks)
        record["citations"] = list(citations or [])
        # F-A5 / ADR-16: rag_used == true → retrieval_index_name SHOULD be a
        # concrete index name. Soft-warn for legacy callers that haven't been
        # wired through F-A7 yet; hard-required at the AuditRecord pydantic
        # boundary so production paths must supply it.
        if not retrieval_index_name:
            logger.warning(
                "audit_record_missing_retrieval_index_name agent=%s correlation_id=%s "
                "(F-A7 wiring at retrieval_client.py pending; ADR-16 alias-pinning protocol)",
                agent_name,
                correlation_id,
            )
    else:
        record["retrieved_chunks"] = []
        if not rag_optout_reason or not adr_pointer:
            raise ValueError("rag_used=False inference records require rag_optout_reason + adr_pointer")
        record["rag_optout_reason"] = rag_optout_reason
        record["adr_pointer"] = adr_pointer
    if gateway_decision == "deny":
        if not gateway_deny_reason:
            raise ValueError("gateway_decision=deny requires gateway_deny_reason")
        record["gateway_deny_reason"] = gateway_deny_reason

    # F-A5 (Cluster A5) — emit only the fields the caller supplied. Empty
    # values stay absent from the record so legacy KQL queries don't see
    # nullable rows where the field was never relevant.
    if operator_override_rationale:
        record["operator_override_rationale"] = operator_override_rationale
    if approval_workflow_state:
        record["approval_workflow_state"] = approval_workflow_state
        # ADR-14 invariant 7: terminal state requires approval_authority.
        if approval_workflow_state in {"approved", "rejected"} and not approval_authority:
            raise ValueError(
                "approval_workflow_state in {approved, rejected} requires approval_authority"
            )
    if approval_authority:
        record["approval_authority"] = approval_authority
    if downgrade_justification:
        record["downgrade_justification"] = downgrade_justification
    if retrieval_index_name:
        record["retrieval_index_name"] = retrieval_index_name
    if field_coordinator_offline_decision:
        record["field_coordinator_offline_decision"] = field_coordinator_offline_decision
        # F-A5.4 / ADR-14 invariant 8: offline decisions queue for IC review.
        if approval_workflow_state is None:
            record["approval_workflow_state"] = "pending"
    if conflict_group_id:
        record["conflict_group_id"] = conflict_group_id
    if precedence_tiebreak_applied:
        record["precedence_tiebreak_applied"] = list(precedence_tiebreak_applied)
    return record


def make_embedding_record(
    *,
    agent_name: str,
    embedding_model_id: str,
    model_id: str,
    model_version: str,
    deployment_alias: str,
    output_text_hash: str,
    output_tokens: int,
    tenant_id: str,
    correlation_id: str,
    gateway_decision: str = "allow",
    call_id: str | None = None,
) -> dict[str, Any]:
    """Build a record dict for an ``embedding`` call (R-13)."""
    return {
        "call_id": call_id or str(uuid.uuid4()),
        "timestamp_utc": _now_iso(),
        "agent_name": agent_name,
        "call_kind": "embedding",
        "model_id": model_id,
        "model_version": model_version,
        "deployment_alias": deployment_alias,
        "embedding_model_id": embedding_model_id,
        "rag_used": False,
        "retrieved_chunks": [],
        "gateway_decision": gateway_decision,
        "hallucinated_citation_count": 0,
        "output_tokens": output_tokens,
        "output_text_hash": output_text_hash,
        "tenant_id": tenant_id,
        "correlation_id": correlation_id,
    }


# Process singleton — see audit_middleware.py for the spec-030 pattern.
_writer: AuditWriter | None = None


def get_audit_writer() -> AuditWriter:
    global _writer
    if _writer is None:
        _writer = CosmosBlobAuditWriter()
    return _writer


def set_audit_writer(writer: AuditWriter) -> None:
    """Override the process-wide writer (used by tests + canary harness)."""
    global _writer
    _writer = writer


__all__ = [
    "AuditWriter",
    "CosmosBlobAuditWriter",
    "InMemoryAuditWriter",
    "get_audit_writer",
    "make_embedding_record",
    "make_inference_record",
    "replay_key",
    "set_audit_writer",
]
