"""T175 — Integration test for the ingest-time agency-metadata lint
(FR-RAG-AG-04 ext; ADR-13; Plan §F-A1.2).

Asserts that ``validate_chunk_metadata`` rejects any chunk that lacks
both ``agency`` AND ``agency_role`` (Plan §F-A1.2: at least one MUST be
present so the FR-RAG-AG-04 disambiguation has data to work with).
"""

from __future__ import annotations

import pytest

chunker = pytest.importorskip("ama_ingest.chunker")


def _mk_chunk(**kwargs):
    defaults = dict(
        chunk_id="c-1",
        corpus_entry_id="nsw/evac",
        jurisdiction="nsw",
        topic="evac",
        page=1,
        text="x" * 10,
        tokens=10,
        sha256_of_chunk="0" * 64,
        licence_mode="full-text",
        source_url="https://example.gov.au/x.pdf",
        rendered_url="/docs/corpus/nsw/evac/handbook.md#page-1",
    )
    defaults.update(kwargs)
    return chunker.Chunk(**defaults)


def test_lint_passes_with_both_fields() -> None:
    chunks = [_mk_chunk(agency="NSW-RFS", agency_role="rural-fire")]
    chunker.validate_chunk_metadata(chunks)  # MUST NOT raise


def test_lint_passes_with_agency_only() -> None:
    """Plan §F-A1.2 requires ≥1 of (agency, agency_role)."""
    chunks = [_mk_chunk(agency="NSW-RFS")]
    chunker.validate_chunk_metadata(chunks)


def test_lint_passes_with_role_only() -> None:
    chunks = [_mk_chunk(agency_role="rural-fire")]
    chunker.validate_chunk_metadata(chunks)


def test_lint_fails_when_both_missing() -> None:
    chunks = [_mk_chunk()]  # both omitted
    with pytest.raises(chunker.ChunkMetadataError, match=r"chunk_missing_agency_metadata"):
        chunker.validate_chunk_metadata(chunks)


def test_lint_fails_on_invalid_role() -> None:
    chunks = [_mk_chunk(agency="X", agency_role="not-a-real-role")]
    with pytest.raises(chunker.ChunkMetadataError, match=r"chunk_invalid_agency_role"):
        chunker.validate_chunk_metadata(chunks)


def test_lint_fails_on_invalid_authority_level() -> None:
    chunks = [
        _mk_chunk(agency="X", agency_role="rural-fire", authority_level="provincial"),
    ]
    with pytest.raises(chunker.ChunkMetadataError, match=r"chunk_invalid_authority_level"):
        chunker.validate_chunk_metadata(chunks)


def test_lint_fails_on_out_of_bounds_precedence_rank() -> None:
    chunks = [
        _mk_chunk(
            agency="X",
            agency_role="rural-fire",
            authority_level="state-territory",
            precedence_rank=99,
        ),
    ]
    with pytest.raises(chunker.ChunkMetadataError, match=r"chunk_invalid_precedence_rank"):
        chunker.validate_chunk_metadata(chunks)


def test_lint_can_be_disabled_for_legacy_rebuilds() -> None:
    """Legacy re-runs may disable the lint; the build artefact MUST document
    why so the audit trail is preserved (the test asserts the toggle works,
    not the documentation requirement)."""
    chunks = [_mk_chunk()]  # both missing
    chunker.validate_chunk_metadata(chunks, enforce_agency=False, enforce_authority=False)


def test_chunks_to_index_docs_emits_phase_f_fields() -> None:
    chunks = [
        _mk_chunk(
            agency="NSW-RFS",
            agency_role="rural-fire",
            authority_level="state-territory",
            precedence_rank=2,
        )
    ]
    docs = chunker.chunks_to_index_docs(
        chunks,
        embedding_model_id="text-embedding-3-large",
        corpus_build_sha="f" * 64,
        retrieval_index_name="corpus-v3",
    )
    assert len(docs) == 1
    doc = docs[0]
    assert doc["agency"] == "NSW-RFS"
    assert doc["agency_role"] == "rural-fire"
    assert doc["authority_level"] == "state-territory"
    assert doc["precedence_rank"] == 2
    assert doc["retrieval_index_name"] == "corpus-v3"
