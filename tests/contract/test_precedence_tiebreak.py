"""T176 — Contract test for the deterministic precedence tie-break order
(FR-RAG-AC-01; Pass 1 Q-P1-02; ADR-13; Plan §F-A3.3).

Synthesises four chunks with identical ``authority_level`` +
``precedence_rank`` but varying ``(corpus_build_sha-driven recency,
licence_mode, embedding_model_id, chunk_id)``; asserts the deterministic
ranking order:

  (1) recency               (newer ``corpus_build_sha.generated_at`` wins)
  (2) ``licence_mode``       (``full-text`` > ``metadata-only``)
  (3) ``embedding_model_id`` (lexicographic ascending)
  (4) ``chunk_id``           (lexicographic ascending)

Asserts ``precedence_tiebreak_applied[]`` audit emission lists every tier
that was *actually triggered* during ranking (skipped tiers are NOT listed).
"""

from __future__ import annotations

import importlib
from datetime import UTC, datetime

import pytest


def _load_ranker():
    """Import the precedence ranker from retrieval_client.

    F-A3 (T185) places ``apply_precedence_tiebreak`` (or equivalent) on
    ``apps/agents/common/retrieval_client``. The function takes a list of
    chunk dicts and returns an (ordered_chunks, tiebreak_applied) tuple.
    """
    pytest.importorskip("ama_domain")
    mod = importlib.import_module("common.retrieval_client")
    if not hasattr(mod, "apply_precedence_tiebreak"):
        pytest.skip(
            "apply_precedence_tiebreak not yet implemented (T185 in flight); "
            "schema cohort tests still gate the contract."
        )
    return mod.apply_precedence_tiebreak


def _mk_chunk(
    *,
    chunk_id: str,
    generated_at: datetime,
    licence_mode: str = "full-text",
    embedding_model_id: str = "text-embedding-3-large",
    authority_level: str = "state-territory",
    precedence_rank: int = 2,
) -> dict:
    return {
        "chunk_id": chunk_id,
        "authority_level": authority_level,
        "precedence_rank": precedence_rank,
        "licence_mode": licence_mode,
        "embedding_model_id": embedding_model_id,
        "corpus_build_generated_at": generated_at.isoformat(),
    }


def test_recency_wins_when_only_dates_differ() -> None:
    rank = _load_ranker()
    older = _mk_chunk(chunk_id="a", generated_at=datetime(2025, 11, 1, tzinfo=UTC))
    newer = _mk_chunk(chunk_id="b", generated_at=datetime(2025, 11, 18, tzinfo=UTC))
    ordered, applied = rank([older, newer])
    assert ordered[0]["chunk_id"] == "b"
    assert "recency" in applied


def test_licence_mode_wins_when_recency_ties() -> None:
    rank = _load_ranker()
    same_date = datetime(2025, 11, 18, tzinfo=UTC)
    metadata = _mk_chunk(chunk_id="m", generated_at=same_date, licence_mode="metadata-only")
    fulltext = _mk_chunk(chunk_id="f", generated_at=same_date, licence_mode="full-text")
    ordered, applied = rank([metadata, fulltext])
    assert ordered[0]["chunk_id"] == "f"
    assert "licence_mode" in applied


def test_embedding_model_id_lex_when_higher_tiers_tie() -> None:
    rank = _load_ranker()
    same_date = datetime(2025, 11, 18, tzinfo=UTC)
    older_emb = _mk_chunk(
        chunk_id="x",
        generated_at=same_date,
        licence_mode="full-text",
        embedding_model_id="text-embedding-3-small",
    )
    larger_emb = _mk_chunk(
        chunk_id="y",
        generated_at=same_date,
        licence_mode="full-text",
        embedding_model_id="text-embedding-3-large",
    )
    ordered, applied = rank([larger_emb, older_emb])
    # Lex ascending: "text-embedding-3-large" < "text-embedding-3-small"
    assert ordered[0]["chunk_id"] == "y"
    assert "embedding_model_id" in applied


def test_chunk_id_lex_when_all_higher_tiers_tie() -> None:
    rank = _load_ranker()
    same_date = datetime(2025, 11, 18, tzinfo=UTC)
    a = _mk_chunk(chunk_id="aaa", generated_at=same_date)
    b = _mk_chunk(chunk_id="bbb", generated_at=same_date)
    ordered, applied = rank([b, a])
    assert ordered[0]["chunk_id"] == "aaa"
    assert "chunk_id" in applied


def test_no_ties_no_lower_tiers_listed() -> None:
    rank = _load_ranker()
    older = _mk_chunk(chunk_id="a", generated_at=datetime(2025, 11, 1, tzinfo=UTC))
    newer = _mk_chunk(chunk_id="b", generated_at=datetime(2025, 11, 18, tzinfo=UTC))
    _ordered, applied = rank([older, newer])
    # Recency strictly distinguished — no further tie-break needed.
    assert applied == ["recency"], (
        f"only recency should be listed when no further ties; got {applied}"
    )


def test_full_chain_when_all_tiers_tied_until_chunk_id() -> None:
    rank = _load_ranker()
    same_date = datetime(2025, 11, 18, tzinfo=UTC)
    a = _mk_chunk(chunk_id="aaa", generated_at=same_date)
    b = _mk_chunk(chunk_id="bbb", generated_at=same_date)
    _ordered, applied = rank([b, a])
    assert applied == [
        "recency",
        "licence_mode",
        "embedding_model_id",
        "chunk_id",
    ], (
        f"chain MUST list every tier traversed; got {applied}"
    )
