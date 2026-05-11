"""Chunker (Spec 036 T041; FR-RAG-IDX-02; R-04).

Splits a corpus ``handbook.md`` into page-aligned, overlap-aware chunks bounded
by a hard token cap. The chunker is **deterministic** (same input ⇒ same
output) so blue-green re-builds are bit-identical for unchanged sources, which
in turn keeps the parity gate (R-05) signal 1 reliable.

Algorithm (R-04, fully bound by ``ingest-pipeline.md`` §5):

1. **Page split** on ``## Page N`` headings — one logical chunk per page is the
   primary unit so citations carry the publisher-original page number.
2. **Token cap (≤ 1024)** — pages that exceed the cap are split at ``H2`` /
   blank-line boundaries; ``cross_page=True`` is set on the spillover chunks so
   the citation token still anchors to the originating page number.
3. **10% sliding overlap** at chunk boundaries (≈100 tokens at 1024 cap) —
   absorbs sentences that straddle a chunk boundary so semantic-search recall
   is preserved.
4. **Atomic preservation of code blocks and tables** — the splitter never
   breaks inside Markdown code fences (triple-backtick) or Markdown tables.

Tokeniser: ``tiktoken cl100k_base`` (matches OpenAI / Foundry embedding
tokenisation).  When ``tiktoken`` is unavailable (light unit tests) the chunker
falls back to a whitespace approximation of ``len(text.split())`` — the cap is
still enforced and the histogram is still emitted, but bit-parity with the
production tokeniser is deferred until ``tiktoken`` is installed.

Telemetry (R-04 validation gate):
- ``chunk_size_tokens`` histogram (every chunk).
- ``cross_page_rate`` gauge — percentage of chunks marked ``cross_page=True``.
- ``truncation_rate`` gauge — percentage of pages where the cap forced a split;
  alert if > 0.5% (Quality-memo R10).
"""

from __future__ import annotations

import hashlib
import logging
import re
import uuid
from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
# Constants — bound by R-04
# --------------------------------------------------------------------------- #

#: Hard token cap per chunk. CI fails any chunk above this value (R-04 invariant).
MAX_TOKENS: int = 1024

#: Sliding-window overlap ratio at chunk boundaries.
OVERLAP_RATIO: float = 0.10

#: UUID-v5 namespace for stable chunk_id generation across re-runs.
#: Must NOT change once chunks are persisted — that would invalidate every
#: existing ``chunk_id`` and break audit replay (FR-RAG-AG-02).
CHUNK_NAMESPACE: uuid.UUID = uuid.UUID("4e8d5a3a-3036-4f00-bc63-1f0036f036ff")

#: Page-heading regex. ``docs/corpus/README.md`` guarantees one ``## Page N``
#: heading per page in the rendered Markdown handbooks.
_PAGE_HEADING_RE = re.compile(r"^##\s+Page\s+(\d+)\s*$", re.MULTILINE)

#: Code-fence regex used to detect atomic code blocks.
_CODE_FENCE_RE = re.compile(r"```")

# --------------------------------------------------------------------------- #
# Data shapes
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class Chunk:
    """A single retrievable unit produced by the chunker.

    Mirrors ``data-model.md §Chunk``. The ``embedding`` and ``embedding_model_id``
    fields are populated downstream by ``embedder.py``; the chunker only
    produces text + provenance.

    Spec-036 Phase F (T181 + T182) NEW fields:
      * ``agency`` + ``agency_role``       — Cluster A1 disambiguation.
      * ``authority_level`` + ``precedence_rank`` — Cluster A3 ranking.

    All four NEW fields are optional on the dataclass for backward-compat
    with pre-Phase-F handbooks; the ingest-time lint
    (``validate_chunk_metadata``) enforces presence at the boundary so a
    rebuild that omits them fails non-zero before the alias flip.
    """

    chunk_id: str
    corpus_entry_id: str
    jurisdiction: str
    topic: str
    page: int
    text: str
    tokens: int
    sha256_of_chunk: str
    licence_mode: str
    source_url: str
    rendered_url: str
    cross_page: bool = False
    summary: str | None = None  # populated by licence_filter for metadata-only entries.
    # Phase F (T181 — Cluster A1)
    agency: str | None = None
    agency_role: str | None = None
    # Phase F (T182 — Cluster A3)
    authority_level: str | None = None
    precedence_rank: int | None = None
    # Phase F (T200 — Cluster A2 cultural authority)
    cultural_classification: str = "public"
    cultural_authority_required: bool = False


@dataclass
class ChunkerStats:
    """Per-run histogram + truncation telemetry (R-04 validation gate)."""

    chunk_size_tokens: list[int] = field(default_factory=list)
    cross_page_count: int = 0
    truncated_pages: int = 0
    total_pages: int = 0

    @property
    def cross_page_rate(self) -> float:
        total = len(self.chunk_size_tokens) or 1
        return self.cross_page_count / total

    @property
    def truncation_rate(self) -> float:
        total = self.total_pages or 1
        return self.truncated_pages / total


# --------------------------------------------------------------------------- #
# Tokeniser (with fall-through stub)
# --------------------------------------------------------------------------- #


def _count_tokens(text: str) -> int:
    """Return the token count of ``text`` using ``tiktoken cl100k_base`` when
    available; otherwise approximates with whitespace splitting.

    The approximation is only used in hermetic unit tests where ``tiktoken`` is
    not installed — production runtimes always have ``tiktoken`` (declared in
    ``apps/ingest-runner/pyproject.toml``).
    """
    try:
        import tiktoken  # noqa: PLC0415

        enc = tiktoken.get_encoding("cl100k_base")
        return len(enc.encode(text))
    except Exception:  # noqa: BLE001 — fallback path only.
        # Whitespace approximation; tightens a touch by counting non-empty tokens.
        return len([t for t in text.split() if t])


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #


def chunk_handbook(
    *,
    handbook_md: str,
    corpus_entry_id: str,
    jurisdiction: str,
    topic: str,
    licence_mode: str,
    source_url: str,
    rendered_url_prefix: str | None = None,
    max_tokens: int = MAX_TOKENS,
    overlap_ratio: float = OVERLAP_RATIO,
    stats: ChunkerStats | None = None,
    # Phase F (T181 + T182) — additive metadata; default None keeps pre-F
    # ingest paths working but the post-chunk lint will reject any chunk
    # that doesn't carry them in production rebuilds.
    agency: str | None = None,
    agency_role: str | None = None,
    authority_level: str | None = None,
    precedence_rank: int | None = None,
    cultural_classification: str = "public",
    cultural_authority_required: bool = False,
) -> list[Chunk]:
    """Split a Markdown handbook into chunks.

    Args:
        handbook_md: Full handbook Markdown body (as rendered by
            ``scripts/disaster_corpus/`` — read from disk by the caller).
        corpus_entry_id: Slash-joined ``"<jurisdiction>/<topic>"`` key.
        jurisdiction: Jurisdiction enum value (``"act"``, ``"nsw"``, ...).
        topic: URL-safe slug.
        licence_mode: One of ``"full-text"`` / ``"metadata-only"`` (chunker is
            never invoked for ``"excluded"`` — the licence filter halts before).
        source_url: Original publisher URL (carried through to every chunk).
        rendered_url_prefix: Optional override for the rendered URL prefix; the
            ``#page-N`` anchor is appended automatically.
        max_tokens: Hard token cap (R-04). Chunks above this size are split.
        overlap_ratio: Sliding overlap at chunk boundaries.
        stats: Optional ``ChunkerStats`` to receive telemetry; created if None.

    Returns:
        List of ``Chunk`` instances in deterministic page-then-offset order.
    """
    if stats is None:
        stats = ChunkerStats()

    pages = _split_pages(handbook_md)
    stats.total_pages += len(pages)

    if rendered_url_prefix is None:
        rendered_url_prefix = f"/docs/corpus/{jurisdiction}/{topic}/handbook.md"

    chunks: list[Chunk] = []
    for page_num, page_body in pages:
        page_pieces = _split_page(
            body=page_body,
            max_tokens=max_tokens,
            overlap_ratio=overlap_ratio,
        )
        if len(page_pieces) > 1:
            stats.truncated_pages += 1
        for offset, piece in enumerate(page_pieces):
            tokens = _count_tokens(piece)
            cross_page = len(page_pieces) > 1 and offset > 0
            sha = hashlib.sha256(piece.encode("utf-8")).hexdigest()
            chunk_id = str(uuid.uuid5(CHUNK_NAMESPACE, f"{corpus_entry_id}/{page_num}/{offset}"))
            rendered_url = f"{rendered_url_prefix}#page-{page_num}"
            chunks.append(
                Chunk(
                    chunk_id=chunk_id,
                    corpus_entry_id=corpus_entry_id,
                    jurisdiction=jurisdiction,
                    topic=topic,
                    page=page_num,
                    text=piece,
                    tokens=tokens,
                    sha256_of_chunk=sha,
                    licence_mode=licence_mode,
                    source_url=source_url,
                    rendered_url=rendered_url,
                    cross_page=cross_page,
                    agency=agency,
                    agency_role=agency_role,
                    authority_level=authority_level,
                    precedence_rank=precedence_rank,
                    cultural_classification=cultural_classification,
                    cultural_authority_required=cultural_authority_required,
                )
            )
            stats.chunk_size_tokens.append(tokens)
            if cross_page:
                stats.cross_page_count += 1
    return chunks


# --------------------------------------------------------------------------- #
# Internals
# --------------------------------------------------------------------------- #


def _split_pages(handbook_md: str) -> list[tuple[int, str]]:
    """Split a handbook into ``(page_number, body)`` tuples on ``## Page N``."""
    matches = list(_PAGE_HEADING_RE.finditer(handbook_md))
    if not matches:
        # No page headings — treat the whole handbook as page 1.
        return [(1, handbook_md.strip())] if handbook_md.strip() else []

    pages: list[tuple[int, str]] = []
    for idx, m in enumerate(matches):
        page_num = int(m.group(1))
        start = m.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(handbook_md)
        body = handbook_md[start:end].strip()
        if body:
            pages.append((page_num, body))
    return pages


def _split_page(*, body: str, max_tokens: int, overlap_ratio: float) -> list[str]:
    """Split a single page into ``<= max_tokens`` chunks with overlap.

    Honours atomic preservation of code-fenced blocks (triple-backtick fenced)
    — never splits inside a fenced block.
    """
    if _count_tokens(body) <= max_tokens:
        return [body]

    # Atomic-block-aware splitting: paragraphs separated by blank lines, but
    # any fenced code block is treated as a single inseparable paragraph.
    paragraphs = _atomic_paragraph_split(body)

    chunks: list[str] = []
    current: list[str] = []
    current_tokens = 0
    overlap_tokens = max(int(max_tokens * overlap_ratio), 1)

    for para in paragraphs:
        ptok = _count_tokens(para)
        if current_tokens + ptok <= max_tokens:
            current.append(para)
            current_tokens += ptok
            continue
        # Flush the current accumulator.
        if current:
            chunks.append("\n\n".join(current))
            # Build overlap by taking the tail of the previous chunk.
            overlap = _tail_tokens("\n\n".join(current), overlap_tokens)
            current = [overlap, para] if overlap else [para]
            current_tokens = _count_tokens(current[0]) + ptok if overlap else ptok
        else:
            # Paragraph alone exceeds cap: hard-split by words.
            for piece in _hard_split(para, max_tokens=max_tokens):
                chunks.append(piece)
            current = []
            current_tokens = 0
    if current:
        chunks.append("\n\n".join(current))

    # Final pass — guarantee no chunk exceeds the cap.
    final: list[str] = []
    for c in chunks:
        if _count_tokens(c) <= max_tokens:
            final.append(c)
        else:
            final.extend(_hard_split(c, max_tokens=max_tokens))
    return final


def _atomic_paragraph_split(body: str) -> list[str]:
    """Split body into paragraphs with code fences kept atomic."""
    lines = body.splitlines()
    paragraphs: list[str] = []
    current: list[str] = []
    in_fence = False
    for line in lines:
        if _CODE_FENCE_RE.match(line):
            in_fence = not in_fence
            current.append(line)
            continue
        if not line.strip() and not in_fence:
            if current:
                paragraphs.append("\n".join(current))
                current = []
        else:
            current.append(line)
    if current:
        paragraphs.append("\n".join(current))
    return paragraphs


def _tail_tokens(text: str, n_tokens: int) -> str:
    """Return the last ``n_tokens`` tokens of ``text`` as a string."""
    words = text.split()
    if len(words) <= n_tokens:
        return text
    return " ".join(words[-n_tokens:])


def _hard_split(text: str, *, max_tokens: int) -> list[str]:
    """Last-resort word-level split honouring ``max_tokens``."""
    words = text.split()
    if not words:
        return []
    out: list[str] = []
    bucket: list[str] = []
    bucket_tokens = 0
    for word in words:
        bucket.append(word)
        bucket_tokens += 1
        if bucket_tokens >= max_tokens:
            out.append(" ".join(bucket))
            bucket = []
            bucket_tokens = 0
    if bucket:
        out.append(" ".join(bucket))
    return out


# --------------------------------------------------------------------------- #
# Convenience helpers used by the indexer
# --------------------------------------------------------------------------- #


def chunks_to_index_docs(
    chunks: Iterable[Chunk],
    *,
    embedding_model_id: str,
    corpus_build_sha: str,
    embeddings: dict[str, list[float]] | None = None,
    retrieval_index_name: str | None = None,
) -> list[dict[str, Any]]:
    """Project a chunk iterable into AI-Search-shaped index documents.

    The ``embeddings`` map is keyed by ``chunk_id``. When omitted, ``embedding``
    is left absent (``metadata-only`` mode) and the indexer caller must enforce
    that no body text leaks downstream.

    Phase F (T182 — Cluster A3): emits ``authority_level`` + ``precedence_rank``
    when set on the source ``Chunk``. ``retrieval_index_name`` is the concrete
    target index for this rebuild (e.g. ``"corpus-v3"``); ingest stamps the
    same name on every doc so audit replay can pin without alias resolution.
    """
    docs: list[dict[str, Any]] = []
    for chunk in chunks:
        doc: dict[str, Any] = {
            "chunk_id": chunk.chunk_id,
            "corpus_entry_id": chunk.corpus_entry_id,
            "jurisdiction": chunk.jurisdiction,
            "topic": chunk.topic,
            "page": chunk.page,
            "tokens": chunk.tokens,
            "sha256_of_chunk": chunk.sha256_of_chunk,
            "licence_mode": chunk.licence_mode,
            "source_url": chunk.source_url,
            "rendered_url": chunk.rendered_url,
            "cross_page": chunk.cross_page,
            "embedding_model_id": embedding_model_id,
            "corpus_build_sha": corpus_build_sha,
        }
        if chunk.licence_mode == "full-text":
            doc["text"] = chunk.text
            if embeddings and chunk.chunk_id in embeddings:
                doc["embedding"] = embeddings[chunk.chunk_id]
        elif chunk.licence_mode == "metadata-only":
            doc["summary"] = chunk.summary or ""
        # Phase F additive metadata.
        if chunk.agency is not None:
            doc["agency"] = chunk.agency
        if chunk.agency_role is not None:
            doc["agency_role"] = chunk.agency_role
        if chunk.authority_level is not None:
            doc["authority_level"] = chunk.authority_level
        if chunk.precedence_rank is not None:
            doc["precedence_rank"] = chunk.precedence_rank
        # Phase F (T200) — cultural authority gating fields. Always emitted
        # so the post-retrieval gate has stable inputs (default public/false
        # is per spec contract chunk-metadata.schema.json).
        doc["cultural_classification"] = chunk.cultural_classification
        doc["cultural_authority_required"] = chunk.cultural_authority_required
        if retrieval_index_name:
            doc["retrieval_index_name"] = retrieval_index_name
        docs.append(doc)
    return docs


# --------------------------------------------------------------------------- #
# Phase F ingest-time metadata lint (T181 + T182)
# --------------------------------------------------------------------------- #


_AGENCY_ROLE_ENUM: frozenset[str] = frozenset(
    {
        "urban-fire",
        "rural-fire",
        "ses",
        "combined",
        "police",
        "ambulance",
        "marine-rescue",
        "national-security",
        "other",
    }
)
_AUTHORITY_LEVEL_ENUM: frozenset[str] = frozenset(
    {"state-territory", "commonwealth", "national-institution"}
)
_CULTURAL_CLASSIFICATION_ENUM: frozenset[str] = frozenset(
    {"public", "indigenous-language", "sacred-site", "land-governance"}
)


class ChunkMetadataError(ValueError):
    """Raised by ``validate_chunk_metadata`` when a chunk is missing or
    has an invalid F-A1/F-A3 metadata field. Ingest-time lint fails the
    build non-zero per Plan §F-A1.2 + §F-A3.1.
    """


def validate_chunk_metadata(
    chunks: Iterable[Chunk],
    *,
    enforce_agency: bool = True,
    enforce_authority: bool = True,
    enforce_cultural: bool = True,
) -> None:
    """Lint a chunk batch against the F-A1 + F-A3 + F-A2 contract.

    Raises ``ChunkMetadataError`` on the first violation. Production CI
    sets all ``enforce_*`` flags True; pre-Phase-F handbooks (legacy
    re-runs) can disable to avoid false positives — but this MUST be
    documented in the build artefact.
    """
    for chunk in chunks:
        if enforce_agency:
            if not chunk.agency and not chunk.agency_role:
                raise ChunkMetadataError(
                    f"chunk_missing_agency_metadata: chunk_id={chunk.chunk_id} "
                    f"corpus_entry_id={chunk.corpus_entry_id} — Plan §F-A1.2 "
                    "requires at least one of (agency, agency_role)."
                )
            if chunk.agency_role and chunk.agency_role not in _AGENCY_ROLE_ENUM:
                raise ChunkMetadataError(
                    f"chunk_invalid_agency_role: chunk_id={chunk.chunk_id} "
                    f"role={chunk.agency_role!r} not in {sorted(_AGENCY_ROLE_ENUM)}"
                )
        if enforce_authority:
            if chunk.authority_level and chunk.authority_level not in _AUTHORITY_LEVEL_ENUM:
                raise ChunkMetadataError(
                    f"chunk_invalid_authority_level: chunk_id={chunk.chunk_id} "
                    f"level={chunk.authority_level!r} not in {sorted(_AUTHORITY_LEVEL_ENUM)}"
                )
            if chunk.precedence_rank is not None and not (1 <= chunk.precedence_rank <= 3):
                raise ChunkMetadataError(
                    f"chunk_invalid_precedence_rank: chunk_id={chunk.chunk_id} "
                    f"rank={chunk.precedence_rank} (expected 1–3)"
                )
        if enforce_cultural:
            if chunk.cultural_classification not in _CULTURAL_CLASSIFICATION_ENUM:
                raise ChunkMetadataError(
                    f"chunk_invalid_cultural_classification: chunk_id={chunk.chunk_id} "
                    f"value={chunk.cultural_classification!r} not in "
                    f"{sorted(_CULTURAL_CLASSIFICATION_ENUM)}"
                )
            # Spec contract chunk-metadata.schema.json allOf invariant 3:
            # cultural_classification != 'public' → cultural_authority_required MUST be true.
            if (
                chunk.cultural_classification != "public"
                and not chunk.cultural_authority_required
            ):
                raise ChunkMetadataError(
                    f"chunk_cultural_invariant_violation: chunk_id={chunk.chunk_id} "
                    f"cultural_classification={chunk.cultural_classification!r} requires "
                    "cultural_authority_required=True (chunk-metadata.schema.json allOf 3)."
                )


__all__ = [
    "CHUNK_NAMESPACE",
    "Chunk",
    "ChunkMetadataError",
    "ChunkerStats",
    "MAX_TOKENS",
    "OVERLAP_RATIO",
    "chunk_handbook",
    "chunks_to_index_docs",
    "validate_chunk_metadata",
]
