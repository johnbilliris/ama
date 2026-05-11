"""Spec 036 T100 — Citation-fidelity signal extension (FR-RAG-AG-05, Risk R3).

Adds a non-blocking ``citation_fidelity ≥ 0.7`` AND ``verbatim-source-match``
signal to the per-agent canary gate. The threshold is informational in
Phase C — it lights up Phase E3's binding gate.

Citation fidelity is the fraction of the agent's emitted citations that
have a non-empty rendered_url AND a sha256_of_chunk that appears in the
companion ``retrieved_chunks`` set. Verbatim-source-match is the fraction
of citations whose ``snippet`` (when present) is a literal substring of
the corresponding chunk text (defence against paraphrase drift).

When the per-agent fixture does NOT set ``requires_citation: true``, the
signal is skipped (1.0 by convention).
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class CitationFidelitySignal:
    fidelity: float
    verbatim_match: float
    cases_with_citations: int
    cases_total: int


def compute_citation_fidelity(cases: Iterable[dict[str, Any]]) -> CitationFidelitySignal:
    """Compute the citation fidelity + verbatim-match signals.

    Each case is a dict shaped like the canary-gate output:

        {
          "id": "...",
          "expected": {"requires_citation": bool, ...},
          "foundry_response": {
            "citations": [{ ..., "snippet": "...", "sha256_of_chunk": "..." }, ...],
            "retrieved_chunks": [{ "sha256_of_chunk": "...", "text": "..." }, ...]
          }
        }
    """
    fid_num = 0
    fid_den = 0
    verb_num = 0
    verb_den = 0
    cases_with_citations = 0
    cases_total = 0
    for case in cases:
        cases_total += 1
        if not case.get("expected", {}).get("requires_citation", False):
            continue
        resp = case.get("foundry_response", {}) or {}
        citations = resp.get("citations") or []
        chunks = resp.get("retrieved_chunks") or []
        if not citations:
            fid_den += 1  # all-citation miss counts against fidelity
            continue
        cases_with_citations += 1
        chunk_index = {c.get("sha256_of_chunk", ""): c for c in chunks}
        for cit in citations:
            fid_den += 1
            sha = cit.get("sha256_of_chunk", "")
            chunk = chunk_index.get(sha)
            if chunk and cit.get("rendered_url"):
                fid_num += 1
            snippet = cit.get("snippet")
            if snippet and chunk and chunk.get("text"):
                verb_den += 1
                if snippet in chunk["text"]:
                    verb_num += 1
    fidelity = (fid_num / fid_den) if fid_den else 1.0
    verbatim = (verb_num / verb_den) if verb_den else 1.0
    return CitationFidelitySignal(
        fidelity=fidelity,
        verbatim_match=verbatim,
        cases_with_citations=cases_with_citations,
        cases_total=cases_total,
    )


CITATION_FIDELITY_THRESHOLD: float = 0.7  # non-blocking in Phase C; binding in Phase E3.


__all__ = [
    "CITATION_FIDELITY_THRESHOLD",
    "CitationFidelitySignal",
    "compute_citation_fidelity",
]
