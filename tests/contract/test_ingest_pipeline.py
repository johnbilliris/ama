"""T031 — Contract test for the corpus ingest pipeline (Spec 036 / FR-RAG-IDX-04; R-04, R-05).

Asserts the four binding contracts of ``contracts/ingest-pipeline.md``:

1. **Idempotency** (§3.1) — unchanged docs ⇒ 0 embedding calls + 0 writes.
2. **Provenance on every chunk** (§3.4) — required keys present.
3. **Single ``embedding_model_id`` per index** (§3.3 signal 4 / R-05).
4. **Parity-gate signal contract** (§3.3) — 4 named signals each with a
   threshold and a pass/fail verdict.

This test goes RED before T040..T046 land and GREEN immediately after — it
exercises ``ama_ingest`` modules in-memory only (no Azure, no Foundry).
"""

from __future__ import annotations

import importlib
from typing import Any

import pytest

# --------------------------------------------------------------------------- #
# Module-load helpers
# --------------------------------------------------------------------------- #


def _ingest(name: str) -> Any:
    return importlib.import_module(f"ama_ingest.{name}")


# --------------------------------------------------------------------------- #
# §3.4 Provenance — every chunk doc carries the required fields.
# --------------------------------------------------------------------------- #


def test_required_provenance_fields_declared() -> None:
    indexer = _ingest("indexer")
    required = indexer.REQUIRED_PROVENANCE_FIELDS
    expected = {
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
    assert expected <= set(required), f"missing {expected - set(required)}"


def test_indexer_rejects_doc_missing_provenance() -> None:
    indexer = _ingest("indexer")
    idx = indexer.InMemoryIndex(name="corpus-v1")
    with pytest.raises(ValueError, match="provenance"):
        idx.upload_documents([{"chunk_id": "c1", "licence_mode": "full-text"}])


def test_indexer_refuses_excluded_chunks() -> None:
    indexer = _ingest("indexer")
    idx = indexer.InMemoryIndex(name="corpus-v1")
    bg = indexer.BlueGreenIndexer(
        index=idx,
        alias=indexer.InMemoryAlias(alias="corpus", active_index=None),
    )
    doc = _make_doc(licence_mode="excluded")
    with pytest.raises(ValueError, match="excluded"):
        bg.write_chunks([doc])


# --------------------------------------------------------------------------- #
# §3.1 Idempotency — re-write of same chunk ⇒ skipped (no upload).
# --------------------------------------------------------------------------- #


def test_indexer_skips_unchanged_chunk_by_sha256() -> None:
    indexer = _ingest("indexer")
    idx = indexer.InMemoryIndex(name="corpus-v1")
    bg = indexer.BlueGreenIndexer(
        index=idx,
        alias=indexer.InMemoryAlias(alias="corpus", active_index=None),
    )
    doc = _make_doc()
    first = bg.write_chunks([doc])
    second = bg.write_chunks([doc])  # identical sha — idempotent skip
    assert first == 1
    assert second == 0
    assert bg.stats.documents_skipped_idempotent == 1


# --------------------------------------------------------------------------- #
# §3.3 signal 4 — single ``embedding_model_id`` per index.
# --------------------------------------------------------------------------- #


def test_indexer_assert_single_embedding_model() -> None:
    indexer = _ingest("indexer")
    idx = indexer.InMemoryIndex(name="corpus-v2")
    idx.upload_documents([_make_doc(embedding_model_id="model-A", chunk_id="a")])
    idx.upload_documents([_make_doc(embedding_model_id="model-B", chunk_id="b")])
    bg = indexer.BlueGreenIndexer(
        index=idx,
        alias=indexer.InMemoryAlias(alias="corpus"),
    )
    with pytest.raises(RuntimeError, match="multiple embedding_model_id"):
        bg.assert_single_embedding_model()


# --------------------------------------------------------------------------- #
# §3.3 — parity gate signal contract (names + thresholds match the spec).
# --------------------------------------------------------------------------- #


def test_parity_gate_emits_four_named_signals() -> None:
    parity = _ingest("parity_gate")
    inputs = parity.ParityInputs(
        old_chunk_count=1000,
        new_chunk_count=1010,
        old_embedding_cost_usd=10.0,
        new_embedding_cost_usd=11.0,
        decision_equivalence=0.97,
        new_index_distinct_embedding_model_ids=1,
    )
    verdict = parity.evaluate(inputs)
    names = [s.name for s in verdict.signals]
    assert names == [
        "chunk_count_delta",
        "cost_ratio",
        "decision_equivalence",
        "single_embedding_model",
    ]
    assert verdict.status == "PASS"


def test_parity_gate_thresholds_documented() -> None:
    parity = _ingest("parity_gate")
    assert parity.CHUNK_COUNT_TOLERANCE == pytest.approx(0.05)
    assert parity.COST_RATIO_CEILING == pytest.approx(1.3)
    assert parity.DECISION_EQUIVALENCE_FLOOR == pytest.approx(0.95)


def test_parity_gate_each_signal_can_fail() -> None:
    parity = _ingest("parity_gate")

    # Signal 1 — chunk count delta > 5%
    v1 = parity.evaluate(
        parity.ParityInputs(
            old_chunk_count=1000,
            new_chunk_count=1100,
            old_embedding_cost_usd=10.0,
            new_embedding_cost_usd=10.0,
            decision_equivalence=1.0,
            new_index_distinct_embedding_model_ids=1,
        )
    )
    assert v1.status == "FAIL"
    failed = [s.name for s in v1.failed_signals]
    assert failed == ["chunk_count_delta"]

    # Signal 2 — cost ratio > 1.3
    v2 = parity.evaluate(
        parity.ParityInputs(
            old_chunk_count=1000,
            new_chunk_count=1000,
            old_embedding_cost_usd=10.0,
            new_embedding_cost_usd=14.0,
            decision_equivalence=1.0,
            new_index_distinct_embedding_model_ids=1,
        )
    )
    assert "cost_ratio" in [s.name for s in v2.failed_signals]

    # Signal 3 — decision equivalence < 0.95
    v3 = parity.evaluate(
        parity.ParityInputs(
            old_chunk_count=1000,
            new_chunk_count=1000,
            old_embedding_cost_usd=10.0,
            new_embedding_cost_usd=10.0,
            decision_equivalence=0.90,
            new_index_distinct_embedding_model_ids=1,
        )
    )
    assert "decision_equivalence" in [s.name for s in v3.failed_signals]

    # Signal 4 — multiple embedding_model_id
    v4 = parity.evaluate(
        parity.ParityInputs(
            old_chunk_count=1000,
            new_chunk_count=1000,
            old_embedding_cost_usd=10.0,
            new_embedding_cost_usd=10.0,
            decision_equivalence=1.0,
            new_index_distinct_embedding_model_ids=2,
        )
    )
    assert "single_embedding_model" in [s.name for s in v4.failed_signals]


# --------------------------------------------------------------------------- #
# Cost / chunk-count limits per R-04
# --------------------------------------------------------------------------- #


def test_chunker_max_tokens_constant() -> None:
    chunker = _ingest("chunker")
    assert chunker.MAX_TOKENS == 1024  # R-04
    assert chunker.OVERLAP_RATIO == pytest.approx(0.10)  # R-04


def test_embedder_dims_constant() -> None:
    embedder = _ingest("embedder")
    assert embedder.EMBEDDING_DIMS == 3072  # R-02


def test_embedder_uses_aad_scope() -> None:
    embedder = _ingest("embedder")
    assert embedder.AAD_SCOPE == "https://cognitiveservices.azure.com/.default"


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #


def _make_doc(
    *,
    chunk_id: str = "c-001",
    licence_mode: str = "full-text",
    embedding_model_id: str = "text-embedding-3-large@1",
) -> dict[str, Any]:
    return {
        "chunk_id": chunk_id,
        "corpus_entry_id": "nsw/evacuation-planning",
        "jurisdiction": "nsw",
        "topic": "evacuation-planning",
        "page": 47,
        "sha256_of_chunk": "f9c3a8" + "0" * 58,
        "source_url": "https://example.gov.au/source.pdf",
        "rendered_url": "/docs/corpus/nsw/evacuation-planning/handbook.md#page-47",
        "licence_mode": licence_mode,
        "corpus_build_sha": "0" * 64,
        "embedding_model_id": embedding_model_id,
        "tokens": 200,
        "cross_page": False,
        "text": "When the area is deemed safe...",
    }
