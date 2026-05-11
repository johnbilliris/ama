"""Licence filter (Spec 036 T043; FR-RAG-IDX-02).

Three-mode gating for ``CorpusEntry`` records:

============== =========================================================
``mode``       Behaviour
============== =========================================================
``full-text``  Chunked + embedded + indexed body + metadata.
``metadata-only`` Title + URL + summary only — body NEVER leaves disk.
``excluded``   No doc emitted; embedding budget never touched.
============== =========================================================

A deploy-time warning fires if any agent prompt template references an
``excluded`` source (FR-RAG-IDX-02 + edge-case "Excluded source crept into
prompt template"). The check runs as part of the ``check_licence_inventory``
helper consumed by the lint workflow (T039 / T055).

This module is **deterministic** — given an entry record it returns the same
verdict for every invocation, which keeps blue-green re-builds idempotent.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Literal

logger = logging.getLogger(__name__)

LicenceMode = Literal["full-text", "metadata-only", "excluded"]

#: Default mode applied when ``source.json`` predates spec 036 (the historic
#: AIDR-only pipeline did not carry a ``mode`` field). The default keeps the
#: pre-spec behaviour — every existing entry is treated as ``full-text``.
#: New entries that wish to opt to ``metadata-only`` or ``excluded`` MUST set
#: the field explicitly; the lint workflow (T039) flags absent values once the
#: licence inventory is authoritative.
DEFAULT_MODE: LicenceMode = "full-text"

#: Allowed values — anything else is rejected at validation time.
ALLOWED_MODES: frozenset[str] = frozenset({"full-text", "metadata-only", "excluded"})


@dataclass(frozen=True)
class FilterDecision:
    """Outcome of the licence filter for a single ``CorpusEntry``."""

    mode: LicenceMode
    chunk: bool  #: True iff the chunker should run.
    embed: bool  #: True iff the embedder should run.
    index: bool  #: True iff a document should be written to AI Search.
    summary_only: bool  #: True iff only ``summary`` (no body) is indexed.


def classify(entry: dict[str, Any]) -> FilterDecision:
    """Classify a ``CorpusEntry`` ``source.json`` record.

    Args:
        entry: Parsed ``source.json`` record. Honours an explicit ``mode``
            field; falls back to ``DEFAULT_MODE`` when absent.

    Returns:
        ``FilterDecision`` with the four boolean gates the ingest pipeline
        consults at chunk / embed / index / projection time.

    Raises:
        ValueError: if ``mode`` is set to an unknown value.
    """
    raw = entry.get("mode", DEFAULT_MODE)
    if raw not in ALLOWED_MODES:
        raise ValueError(f"unknown licence mode {raw!r}; expected one of {sorted(ALLOWED_MODES)}")
    mode: LicenceMode = raw  # type: ignore[assignment]
    if mode == "excluded":
        return FilterDecision(mode=mode, chunk=False, embed=False, index=False, summary_only=False)
    if mode == "metadata-only":
        return FilterDecision(mode=mode, chunk=False, embed=False, index=True, summary_only=True)
    # full-text
    return FilterDecision(mode=mode, chunk=True, embed=True, index=True, summary_only=False)


def metadata_only_doc(
    entry: dict[str, Any],
    *,
    jurisdiction: str,
    topic: str,
    embedding_model_id: str,
    corpus_build_sha: str,
) -> dict[str, Any]:
    """Project a ``metadata-only`` entry into an AI-Search-shaped document.

    The body is **never** included; only the publisher-supplied summary,
    jurisdiction, topic, and source URL. The ``embedding`` field is omitted
    entirely (R-11 wire-format invariant: omitted, not nulled, not masked).
    """
    summary = entry.get("summary") or entry.get("title") or ""
    chunk_id = f"{jurisdiction}/{topic}#metadata"
    sha = entry.get("sha256", "")
    return {
        "chunk_id": chunk_id,
        "corpus_entry_id": f"{jurisdiction}/{topic}",
        "jurisdiction": jurisdiction,
        "topic": topic,
        "page": 1,
        "summary": summary,
        "tokens": 0,
        "sha256_of_chunk": sha,
        "licence_mode": "metadata-only",
        "source_url": entry.get("url", ""),
        "rendered_url": f"/docs/corpus/{jurisdiction}/{topic}/handbook.md",
        "cross_page": False,
        "embedding_model_id": embedding_model_id,
        "corpus_build_sha": corpus_build_sha,
    }


def is_excluded(entry: dict[str, Any]) -> bool:
    """Convenience predicate used by the inventory lint."""
    return entry.get("mode") == "excluded"


__all__ = [
    "ALLOWED_MODES",
    "DEFAULT_MODE",
    "FilterDecision",
    "LicenceMode",
    "classify",
    "is_excluded",
    "metadata_only_doc",
]
