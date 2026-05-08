"""Indexer (Spec 036 T044; FR-RAG-IDX-03 / -04; R-15).

Writes chunk documents into Azure AI Search with **blue-green** semantics:

- Determines the target index (``corpus-v{N+1}`` for a model swap, otherwise
  ``corpus-v{N}``) from the alias state.
- Skips entries whose ``sha256_of_chunk`` is already present in the index
  (FR-RAG-IDX-04 idempotency).
- Stamps every doc with the provenance fields required by FR-RAG-IDX-03.
- Emits a flip-helper that the parity gate (T046) calls once it has signed
  off on the new index.

The implementation is **pluggable** — the ``IndexClient`` abstract surface
matches both the live ``azure-search-documents`` ``SearchClient`` and the
in-memory ``InMemoryIndex`` used by the unit + integration tests. Tests inject
the in-memory client and never hit Azure.
"""

from __future__ import annotations

import logging
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from typing import Any, Protocol

logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# Provenance invariants — required keys on every persisted doc (FR-RAG-IDX-03).
# --------------------------------------------------------------------------- #


REQUIRED_PROVENANCE_FIELDS: frozenset[str] = frozenset(
    {
        "chunk_id",
        "corpus_entry_id",
        "jurisdiction",
        "topic",
        "page",
        "sha256_of_chunk",
        "source_url",
        "rendered_url",
        "licence_mode",
        "corpus_build_sha",
        "embedding_model_id",
    }
)


# --------------------------------------------------------------------------- #
# Capacity alert (FR-RAG-IDX-08; R-10).
# --------------------------------------------------------------------------- #


CAPACITY_ALERT_THRESHOLD: float = 0.70
"""Threshold (fraction of 0..1) at which the AI Search capacity alert fires.

Tied to ``infra/modules/ai-search.bicep`` ``capacityAlertThresholdPercent``
(default 70) — keep both values in sync. The Bicep alert is the production
mechanism; this helper exists for the runner-side telemetry path and tests.
"""


def is_capacity_alert(*, used: float, total: float) -> bool:
    """Return ``True`` if ``used / total ≥ CAPACITY_ALERT_THRESHOLD``.

    ``total <= 0`` is treated as "no signal" (returns ``False``) — production
    callers must always supply a positive denominator.
    """
    if total <= 0:
        return False
    return (used / total) >= CAPACITY_ALERT_THRESHOLD


# --------------------------------------------------------------------------- #
# Index client protocol — the surface the indexer needs.
# --------------------------------------------------------------------------- #


class IndexClient(Protocol):
    """Minimal AI-Search-compatible surface used by the indexer.

    Production: a thin wrapper over ``azure.search.documents.SearchClient``.
    Tests: ``InMemoryIndex``.
    """

    def upload_documents(self, documents: Sequence[dict[str, Any]]) -> int: ...

    def get_document_by_chunk_id(self, chunk_id: str) -> dict[str, Any] | None: ...

    def list_chunk_ids(self) -> list[str]: ...

    def count(self) -> int: ...

    def distinct_embedding_model_ids(self) -> list[str]: ...


# --------------------------------------------------------------------------- #
# In-memory implementation (used by tests + dry-run mode).
# --------------------------------------------------------------------------- #


class InMemoryIndex:
    """In-memory ``IndexClient`` for hermetic tests and ``--dry-run`` mode."""

    def __init__(self, *, name: str) -> None:
        self.name = name
        self._docs: dict[str, dict[str, Any]] = {}

    def upload_documents(self, documents: Sequence[dict[str, Any]]) -> int:
        written = 0
        for doc in documents:
            missing = REQUIRED_PROVENANCE_FIELDS - set(doc.keys())
            if missing:
                raise ValueError(f"index doc missing required provenance fields: {sorted(missing)}")
            if doc["licence_mode"] not in ("full-text", "metadata-only"):
                raise ValueError(
                    f"unexpected licence_mode {doc['licence_mode']!r}; excluded chunks must NEVER reach the indexer"
                )
            self._docs[doc["chunk_id"]] = dict(doc)
            written += 1
        return written

    def get_document_by_chunk_id(self, chunk_id: str) -> dict[str, Any] | None:
        return self._docs.get(chunk_id)

    def list_chunk_ids(self) -> list[str]:
        return list(self._docs.keys())

    def count(self) -> int:
        return len(self._docs)

    def distinct_embedding_model_ids(self) -> list[str]:
        return sorted({d.get("embedding_model_id", "") for d in self._docs.values()})

    # ---- helpers used by tests ------------------------------------------ #

    def all_documents(self) -> list[dict[str, Any]]:
        return list(self._docs.values())

    def documents_by_licence_mode(self, mode: str) -> list[dict[str, Any]]:
        return [d for d in self._docs.values() if d.get("licence_mode") == mode]


# --------------------------------------------------------------------------- #
# Alias service — wraps the AI-Search alias API; in-memory test stand-in too.
# --------------------------------------------------------------------------- #


class AliasService(Protocol):
    """Manages the ``corpus`` alias pointer + retention semantics."""

    def get_active_index(self) -> str | None: ...

    def get_active_embedding_model_id(self) -> str | None: ...

    def flip(self, *, alias: str, target_index: str) -> float: ...

    def list_indices(self) -> list[str]: ...


@dataclass
class _RetentionRecord:
    index_name: str
    retain_until_iso: str


class InMemoryAlias:
    """In-memory alias manager — preserves the 7-day retention contract."""

    def __init__(
        self,
        *,
        alias: str,
        active_index: str | None = None,
        active_embedding_model_id: str | None = None,
    ) -> None:
        self.alias = alias
        self._active_index = active_index
        self._active_embedding_model_id = active_embedding_model_id
        self._indices: list[str] = list({active_index} - {None})  # type: ignore[arg-type]
        self._retentions: list[_RetentionRecord] = []
        self.last_flip_latency_s: float = 0.0

    def get_active_index(self) -> str | None:
        return self._active_index

    def get_active_embedding_model_id(self) -> str | None:
        return self._active_embedding_model_id

    def set_active_embedding_model_id(self, value: str) -> None:
        self._active_embedding_model_id = value

    def register_index(self, name: str) -> None:
        if name not in self._indices:
            self._indices.append(name)

    def flip(self, *, alias: str, target_index: str) -> float:
        """Atomically point ``alias`` at ``target_index``. Returns latency seconds."""
        if alias != self.alias:
            raise ValueError(f"alias mismatch {alias!r} ≠ {self.alias!r}")
        previous = self._active_index
        # In-memory flip is instantaneous; production wraps the AI Search REST
        # alias-update call which is documented to complete in <60s (R-15).
        self._active_index = target_index
        self.last_flip_latency_s = 0.0  # in-memory; real value populated by REST.
        if previous and previous != target_index:
            from datetime import UTC, datetime, timedelta  # noqa: PLC0415

            self._retentions.append(
                _RetentionRecord(
                    index_name=previous,
                    retain_until_iso=(datetime.now(tz=UTC) + timedelta(days=7)).isoformat(),
                )
            )
        return self.last_flip_latency_s

    def list_indices(self) -> list[str]:
        return list(self._indices)

    def retentions(self) -> list[_RetentionRecord]:
        return list(self._retentions)


# --------------------------------------------------------------------------- #
# Indexer
# --------------------------------------------------------------------------- #


@dataclass
class IndexerStats:
    documents_written: int = 0
    documents_skipped_idempotent: int = 0
    documents_failed: int = 0
    embedding_model_ids_seen: set[str] = field(default_factory=set)


@dataclass
class FlipResult:
    flipped: bool
    previous_index: str | None
    new_index: str
    latency_s: float
    parity_gate_status: str  # "PASS" | "FAIL" | "N/A"


class BlueGreenIndexer:
    """Coordinates the chunker / embedder / index-write / alias-flip cycle.

    Args:
        index: ``IndexClient`` write target. In production the caller resolves
            ``corpus-v{N}`` (incremental) or ``corpus-v{N+1}`` (model swap).
        alias: ``AliasService`` managing the ``corpus`` alias pointer.
        alias_name: Logical alias (defaults to ``"corpus"``).
        active_embedding_model_id: ``embedding_model_id`` recorded on the
            currently-active index, used to detect a model swap.
    """

    def __init__(
        self,
        *,
        index: IndexClient,
        alias: AliasService,
        alias_name: str = "corpus",
    ) -> None:
        self._index = index
        self._alias = alias
        self._alias_name = alias_name
        self.stats = IndexerStats()

    # ------------------------------------------------------------------ #
    # Idempotency check (FR-RAG-IDX-04 §3.1)
    # ------------------------------------------------------------------ #

    def is_idempotent_skip(self, doc: dict[str, Any]) -> bool:
        existing = self._index.get_document_by_chunk_id(doc["chunk_id"])
        if existing is None:
            return False
        return existing.get("sha256_of_chunk") == doc.get("sha256_of_chunk")

    # ------------------------------------------------------------------ #
    # Write — applies idempotency + invariant checks
    # ------------------------------------------------------------------ #

    def write_chunks(self, docs: Iterable[dict[str, Any]]) -> int:
        """Upsert docs, skipping idempotent matches; returns number written."""
        to_write: list[dict[str, Any]] = []
        for doc in docs:
            missing = REQUIRED_PROVENANCE_FIELDS - set(doc.keys())
            if missing:
                raise ValueError(f"index doc missing required provenance fields: {sorted(missing)}")
            if doc["licence_mode"] == "excluded":
                raise ValueError("excluded chunks must NEVER reach the indexer (FR-RAG-IDX-02)")
            self.stats.embedding_model_ids_seen.add(doc.get("embedding_model_id", ""))
            if self.is_idempotent_skip(doc):
                self.stats.documents_skipped_idempotent += 1
                continue
            to_write.append(doc)

        if not to_write:
            return 0
        written = self._index.upload_documents(to_write)
        self.stats.documents_written += written
        return written

    # ------------------------------------------------------------------ #
    # Single-model invariant (R-05 signal 4)
    # ------------------------------------------------------------------ #

    def assert_single_embedding_model(self) -> None:
        ids = self._index.distinct_embedding_model_ids()
        ids = [i for i in ids if i]
        if len(ids) > 1:
            raise RuntimeError(
                f"index hosts multiple embedding_model_id values {ids}; blue-green rebuild required (R-05 signal 4)"
            )

    # ------------------------------------------------------------------ #
    # Alias flip — gate-guarded (caller passes parity_gate_status="PASS")
    # ------------------------------------------------------------------ #

    def flip_alias(
        self,
        *,
        target_index: str,
        parity_gate_status: str,
    ) -> FlipResult:
        """Atomically point the alias at ``target_index`` if the gate passed."""
        previous = self._alias.get_active_index()
        if parity_gate_status != "PASS":
            return FlipResult(
                flipped=False,
                previous_index=previous,
                new_index=target_index,
                latency_s=0.0,
                parity_gate_status=parity_gate_status,
            )
        latency = self._alias.flip(alias=self._alias_name, target_index=target_index)
        return FlipResult(
            flipped=True,
            previous_index=previous,
            new_index=target_index,
            latency_s=latency,
            parity_gate_status=parity_gate_status,
        )


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #


def next_index_name(*, current_index: str | None, prefix: str = "corpus-v") -> str:
    """Compute the next blue-green index name from the active alias target."""
    if current_index is None or not current_index.startswith(prefix):
        return f"{prefix}1"
    suffix = current_index[len(prefix) :]
    try:
        n = int(suffix)
    except ValueError:
        return f"{prefix}1"
    return f"{prefix}{n + 1}"


__all__ = [
    "AliasService",
    "BlueGreenIndexer",
    "FlipResult",
    "IndexClient",
    "IndexerStats",
    "InMemoryAlias",
    "InMemoryIndex",
    "REQUIRED_PROVENANCE_FIELDS",
    "next_index_name",
]
