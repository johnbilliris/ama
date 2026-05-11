"""spec-038 T-AA050 — deterministic chat ``pattern_id`` hasher.

``pattern_id`` clusters chat answers that share the same retrieval set so
``ContentReviewBacklogItem`` can aggregate negative feedback across sessions
(FR-022a / FR-022a-AMEND).

Hash formula::

    sha256(question_intent_cluster_id + ":" + ":".join(citation_source_ids))

**Ordering matters.** FR-022a-AMEND mandates "exact ordered set" of
citations: callers MUST pass citation source ids in the order the assistant
returned them (do NOT pre-sort). Two answers with the same intent cluster
but different citation order produce different pattern ids.
"""

from __future__ import annotations

import hashlib


def compute_pattern_id(question_intent_cluster_id: str, citation_source_ids: list[str]) -> str:
    """Return the SHA-256 hex digest used as ``ChatTurn.pattern_id``."""
    if not question_intent_cluster_id:
        raise ValueError("question_intent_cluster_id is required")
    payload = question_intent_cluster_id + ":" + ":".join(citation_source_ids)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


__all__ = ["compute_pattern_id"]
