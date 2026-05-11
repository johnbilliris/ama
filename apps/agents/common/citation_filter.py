"""Spec 036 — Citation hallucination filter (T080; FR-RAG-AG-05, R-10, R-16).

Every grounded agent's emitted citation set MUST be validated against the
originating ``RetrievalResult.chunks[].sha256_of_chunk`` before reaching the
operator UI or the simulation SSE channel. Citations whose
``sha256_of_chunk`` does NOT appear in the retrieved set are **hallucinated**
and MUST be:

1. suppressed from the rendered card / SSE event,
2. counted into the audit record's ``hallucinated_citation_count``,
3. logged as a structured ``hallucinated_citation`` event for operator-replay.

This is the **only** source of truth for the "which citations make it through"
gate (FR-RAG-AG-05). Agents and the simulation Controller call
``filter_citations(citations, retrieved_chunks)`` and emit ``result.allowed``
to operators — never the raw model output.

Confidence downgrade (R-10 / R-16): when a single response yields ≥ 1
hallucinated citation, the calling agent MAY downgrade its overall confidence
band to "warn-only" (the policy threshold defaults to 1; revisited per agent
in T090–T094).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


# Threshold above which a response's overall confidence is downgraded.
# Default 1 — a single hallucinated citation is enough to taint the response
# (FR-RAG-AG-05; R-10). Per-agent overrides land in T090–T094.
DEFAULT_HALLUCINATION_DOWNGRADE_THRESHOLD: int = 1


@dataclass(frozen=True)
class CitationFilterResult:
    """Outcome of a citation filter pass."""

    allowed: list[Any] = field(default_factory=list)
    """Citations that matched a retrieved chunk; safe to render."""

    hallucinated: list[Any] = field(default_factory=list)
    """Citations that did NOT match any retrieved chunk; suppressed."""

    @property
    def hallucinated_count(self) -> int:
        return len(self.hallucinated)

    @property
    def should_downgrade_confidence(self) -> bool:
        return self.hallucinated_count >= DEFAULT_HALLUCINATION_DOWNGRADE_THRESHOLD


def _sha_of(item: Any) -> str | None:
    """Pull ``sha256_of_chunk`` off either a Citation, a RetrievedChunk, a dict, or a model dump."""
    return getattr(item, "sha256_of_chunk", None) or (item.get("sha256_of_chunk") if isinstance(item, dict) else None)


def filter_citations(
    *,
    citations: list[Any],
    retrieved_chunks: list[Any],
) -> CitationFilterResult:
    """Return the suppression decision for ``citations`` against ``retrieved_chunks``.

    Citations whose ``sha256_of_chunk`` is not present in
    ``retrieved_chunks[].sha256_of_chunk`` are hallucinated (FR-RAG-AG-05);
    they are removed from ``allowed`` and tallied into ``hallucinated``.

    The function is intentionally side-effect-free; structured audit logging
    for each suppression is performed at the call site so the audit record
    can correlate the suppression with the originating ``call_id``.
    """
    valid_shas = {_sha_of(c) for c in retrieved_chunks if _sha_of(c) is not None}
    allowed: list[Any] = []
    hallucinated: list[Any] = []
    for citation in citations:
        sha = _sha_of(citation)
        if sha is None:
            # Treat missing sha as hallucinated (defence-in-depth; the schema
            # already requires this field, but we don't want to panic the
            # request just because one citation is malformed).
            hallucinated.append(citation)
            continue
        if sha in valid_shas:
            allowed.append(citation)
        else:
            hallucinated.append(citation)
            logger.warning(
                "hallucinated_citation suppressed sha=%s rendered_url=%s",
                sha,
                getattr(citation, "rendered_url", None),
            )
    return CitationFilterResult(allowed=allowed, hallucinated=hallucinated)


__all__ = [
    "DEFAULT_HALLUCINATION_DOWNGRADE_THRESHOLD",
    "CitationFilterResult",
    "filter_citations",
]
