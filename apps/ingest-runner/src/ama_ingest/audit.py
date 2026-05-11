"""Audit-record emission for the ingest pipeline (Spec 036 T056; FR-RAG-AG-02; R-13).

The ingest-runner emits two audit shapes:

- ``call_kind="embedding"`` — one record per Foundry embedding call, carrying
  ``corpus_build_sha``, ``embedding_model_id``, ``deployment_alias``,
  ``chunk_count``, ``embedded_token_count``. ``rag_used=False``,
  ``prompt_sha`` absent, ``retrieved_chunks=[]`` (per ingest-pipeline.md §6).
- ``kind="ingest_summary"`` — one record per ingest run (§6 reference shape).

Both shapes are append-only writes to Cosmos ``audit_records`` (45-day
operational retention) **and** to the existing 7-year append-only Blob archive
(spec 030 immutability policy reused; R-13).

This module provides the in-process shape + a pluggable ``AuditEmitter``
``Protocol`` so production wiring (Cosmos + Blob) and tests (in-memory) share a
single contract — mirrors the ``IndexClient`` pattern in ``indexer.py``.
"""

from __future__ import annotations

import logging
from collections.abc import Iterable
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any, Literal, Protocol

logger = logging.getLogger(__name__)


CallKind = Literal["embedding"]


# --------------------------------------------------------------------------- #
# Shapes — audit-record-llm-call.json compatible projections.
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class EmbeddingAuditRecord:
    """Audit record for a single Foundry embedding call.

    Mirrors the ``call_kind="embedding"`` projection from FR-RAG-AG-02:
    ``corpus_build_sha``, ``embedding_model_id``, ``deployment_alias`` populated;
    ``prompt_sha``, ``retrieved_chunks``, ``rag_used`` set per §6.
    """

    timestamp: str
    call_kind: CallKind
    corpus_build_sha: str
    embedding_model_id: str
    deployment_alias: str
    chunk_count: int
    embedded_token_count: int
    latency_ms: int
    rag_used: bool = False
    correlation_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = asdict(self)
        out["retrieved_chunks"] = []  # always empty for embedding records (R-13)
        return out


@dataclass
class IngestSummaryRecord:
    """Run-level summary record (one per ingest run; ingest-pipeline.md §6 shape)."""

    kind: Literal["ingest_summary"]
    corpus_build_sha: str
    started_at: str
    completed_at: str
    chunks_written: int
    chunks_skipped_idempotent: int
    embedding_calls: int
    embedding_total_cost_usd: float
    blue_green: bool
    parity_gate: str  # "PASS" | "FAIL" | "N/A"
    alias_flipped_to: str | None = None
    previous_index_retained_until: str | None = None
    parity_gate_signals: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# --------------------------------------------------------------------------- #
# Emitter protocol + in-memory implementation
# --------------------------------------------------------------------------- #


class AuditEmitter(Protocol):
    def emit_embedding(self, record: EmbeddingAuditRecord) -> None: ...

    def emit_ingest_summary(self, record: IngestSummaryRecord) -> None: ...


class InMemoryAuditEmitter:
    """Hermetic emitter — collects records into an in-process buffer."""

    def __init__(self) -> None:
        self.embedding_records: list[EmbeddingAuditRecord] = []
        self.summary_records: list[IngestSummaryRecord] = []

    def emit_embedding(self, record: EmbeddingAuditRecord) -> None:
        self.embedding_records.append(record)

    def emit_ingest_summary(self, record: IngestSummaryRecord) -> None:
        self.summary_records.append(record)


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #


def make_embedding_record(
    *,
    corpus_build_sha: str,
    embedding_model_id: str,
    deployment_alias: str,
    chunk_count: int,
    embedded_token_count: int,
    latency_ms: int,
    correlation_id: str | None = None,
) -> EmbeddingAuditRecord:
    return EmbeddingAuditRecord(
        timestamp=datetime.now(tz=UTC).isoformat(),
        call_kind="embedding",
        corpus_build_sha=corpus_build_sha,
        embedding_model_id=embedding_model_id,
        deployment_alias=deployment_alias,
        chunk_count=chunk_count,
        embedded_token_count=embedded_token_count,
        latency_ms=latency_ms,
        correlation_id=correlation_id,
    )


def make_ingest_summary(
    *,
    corpus_build_sha: str,
    started_at: datetime,
    completed_at: datetime,
    chunks_written: int,
    chunks_skipped_idempotent: int,
    embedding_calls: int,
    embedding_total_cost_usd: float,
    blue_green: bool,
    parity_gate: str,
    alias_flipped_to: str | None = None,
    previous_index_retained_until: str | None = None,
    parity_gate_signals: dict[str, Any] | None = None,
) -> IngestSummaryRecord:
    return IngestSummaryRecord(
        kind="ingest_summary",
        corpus_build_sha=corpus_build_sha,
        started_at=started_at.astimezone(UTC).isoformat(),
        completed_at=completed_at.astimezone(UTC).isoformat(),
        chunks_written=chunks_written,
        chunks_skipped_idempotent=chunks_skipped_idempotent,
        embedding_calls=embedding_calls,
        embedding_total_cost_usd=embedding_total_cost_usd,
        blue_green=blue_green,
        parity_gate=parity_gate,
        alias_flipped_to=alias_flipped_to,
        previous_index_retained_until=previous_index_retained_until,
        parity_gate_signals=parity_gate_signals or {},
    )


def emit_batch(
    emitter: AuditEmitter,
    records: Iterable[EmbeddingAuditRecord],
) -> int:
    n = 0
    for r in records:
        emitter.emit_embedding(r)
        n += 1
    return n


__all__ = [
    "AuditEmitter",
    "CallKind",
    "EmbeddingAuditRecord",
    "InMemoryAuditEmitter",
    "IngestSummaryRecord",
    "emit_batch",
    "make_embedding_record",
    "make_ingest_summary",
]
