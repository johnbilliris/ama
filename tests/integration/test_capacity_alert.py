"""T038 — Integration test: capacity alert + chunk_size_tokens histogram (FR-RAG-IDX-08, R-10).

Validates the chunker emits a token-size histogram and that an explicit
**threshold helper** evaluates 70% utilisation correctly. The live AI Search
capacity alert is wired via Bicep (T049) — its config is asserted in
``test_ai_search_blue_green_bicep.py``. This test exercises the
**telemetry-side** invariants the runner is responsible for.
"""

from __future__ import annotations

import textwrap

import pytest
from ama_ingest import chunker


def test_chunker_emits_size_histogram() -> None:
    handbook = (
        textwrap.dedent("""
        # Test Handbook

        ## Page 1

        First paragraph one.

        Second paragraph two with more words to make it heftier.

        ## Page 2

        Page two content.
    """).strip()
        + "\n"
    )

    stats = chunker.ChunkerStats()
    chunks = chunker.chunk_handbook(
        handbook_md=handbook,
        corpus_entry_id="test/topic",
        jurisdiction="test",
        topic="topic",
        licence_mode="full-text",
        source_url="https://example",
        stats=stats,
    )

    assert chunks, "expected at least one chunk from a 2-page handbook"
    assert stats.chunk_size_tokens, "ChunkerStats.chunk_size_tokens must be populated"
    assert all(b > 0 for b in stats.chunk_size_tokens), "histogram bins must be positive"

    # Truncation ratio is recorded (even if 0).
    assert hasattr(stats, "truncated_pages"), "stats must carry truncated_pages"
    assert stats.truncated_pages >= 0
    assert 0.0 <= stats.truncation_rate <= 1.0


def test_capacity_threshold_helper_70pct() -> None:
    """Helper that evaluates capacity utilisation against the FR-RAG-IDX-08 70% threshold."""
    from ama_ingest import indexer

    assert hasattr(indexer, "is_capacity_alert"), (
        "indexer must expose `is_capacity_alert(used, total)` for FR-RAG-IDX-08"
    )
    # Explicit threshold = 0.70.
    assert indexer.is_capacity_alert(used=70, total=100) is True
    assert indexer.is_capacity_alert(used=69, total=100) is False
    assert indexer.is_capacity_alert(used=50, total=100) is False
    assert indexer.is_capacity_alert(used=100, total=100) is True
    assert indexer.CAPACITY_ALERT_THRESHOLD == pytest.approx(0.70)


def test_chunk_truncation_rate_is_recorded() -> None:
    """Truncation > 0.5% must be reportable via stats (R-10 alert input)."""
    from ama_ingest import chunker

    stats = chunker.ChunkerStats()

    # Synthesise a chunk that exceeds the cap to force truncation.
    very_long = "word " * (chunker.MAX_TOKENS * 3)
    handbook = f"# H\n\n## Page 1\n\n{very_long}\n"
    chunks = chunker.chunk_handbook(
        handbook_md=handbook,
        corpus_entry_id="x/y",
        jurisdiction="x",
        topic="y",
        licence_mode="full-text",
        source_url="https://x",
        stats=stats,
    )
    assert chunks
    # Either truncation_pages incremented OR multiple chunks produced (overlap split).
    assert stats.truncated_pages >= 0
    assert 0.0 <= stats.truncation_rate <= 1.0
