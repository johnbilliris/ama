"""T037 — Integration test: licence-mode partition (FR-RAG-IDX-02; SC-006).

Asserts the three-mode contract:

- ``full-text`` → body indexed + embedded.
- ``metadata-only`` → metadata-only doc; no body, no embedding vector.
- ``excluded`` → not persisted at all (zero docs reachable).
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import tempfile
from argparse import Namespace
from datetime import UTC, datetime
from pathlib import Path

from ama_ingest import (
    __main__ as ingest_main,
)
from ama_ingest import (
    audit as audit_mod,
)
from ama_ingest import (
    embedder,
    indexer,
)

CARVEOUT_REGISTRY = Path(__file__).resolve().parents[2] / "infra" / "parameters" / "foundry-carveout.yaml"
_SCRATCH_BASE = Path(__file__).resolve().parents[2] / "artifacts" / "test-scratch"


@contextlib.contextmanager
def _scratch_dir():
    _SCRATCH_BASE.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=_SCRATCH_BASE) as d:
        yield Path(d)


def _write_entry(corpus_root: Path, *, jurisdiction: str, topic: str, mode: str) -> None:
    handbook = f"# {jurisdiction.upper()} {topic}\n\n## Page 1\n\nBody content for licence-mode partition test.\n"
    sha = hashlib.sha256(handbook.encode("utf-8")).hexdigest()
    target = corpus_root / jurisdiction / topic
    target.mkdir(parents=True)
    (target / "handbook.md").write_text(handbook, encoding="utf-8")
    (target / "source.json").write_text(
        json.dumps(
            {
                "title": f"{jurisdiction}/{topic}",
                "publisher": "Test",
                "licence": "TEST",
                "url": f"https://example.{jurisdiction}.gov.au/{topic}.pdf",
                "sha256": sha,
                "retrieved_at": datetime.now(tz=UTC).isoformat(),
                "mode": mode,
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def _args(corpus_root: Path) -> Namespace:
    return Namespace(
        corpus_root=corpus_root,
        search_endpoint="",
        index_alias="corpus",
        target_index="corpus-v1",
        embedding_model="text-embedding-3-large@1",
        carveout_registry=CARVEOUT_REGISTRY,
        carveout_region="australiaeast",
        corpus_build_sha=None,
        mode="incremental",
        manifest_out=None,
        offline_bundle_out=None,
        jurisdiction=None,
        log_level="WARNING",
    )


def test_three_mode_partition() -> None:
    with _scratch_dir() as tmp:
        corpus = tmp / "corpus"
        _write_entry(corpus, jurisdiction="act", topic="full-text-topic", mode="full-text")
        _write_entry(corpus, jurisdiction="nsw", topic="meta-only-topic", mode="metadata-only")
        _write_entry(corpus, jurisdiction="qld", topic="excluded-topic", mode="excluded")

        index = indexer.InMemoryIndex(name="corpus-v1")
        result = ingest_main.run(
            args=_args(corpus),
            index=index,
            alias=indexer.InMemoryAlias(alias="corpus", active_index=None),
            embed=embedder.deterministic_stub_embedder(),
            audit_emitter=audit_mod.InMemoryAuditEmitter(),
        )
        assert result.exit_code == 0, result.parity_signals

        docs = list(index.all_documents())

        # Excluded: 0 docs reachable.
        excluded = [d for d in docs if d.get("topic") == "excluded-topic"]
        assert excluded == [], f"excluded entry leaked into index: {excluded}"

        # Full-text: body + embedding present.
        full = [d for d in docs if d.get("topic") == "full-text-topic"]
        assert full, "expected at least one full-text chunk"
        for d in full:
            assert d["licence_mode"] == "full-text"
            assert d.get("text"), "full-text doc must carry body text"
            assert isinstance(d.get("embedding"), list) and len(d["embedding"]) == embedder.EMBEDDING_DIMS

        # Metadata-only: NO body, NO embedding.
        meta = [d for d in docs if d.get("topic") == "meta-only-topic"]
        assert meta, "expected at least one metadata-only doc"
        for d in meta:
            assert d["licence_mode"] == "metadata-only"
            assert not d.get("text"), "metadata-only doc must omit body"
            assert not d.get("embedding"), "metadata-only doc must omit vector"


def test_excluded_count_in_filter_decision() -> None:
    """Direct check of the licence_filter to lock the excluded short-circuit."""
    from ama_ingest import licence_filter

    decision = licence_filter.classify({"mode": "excluded"})
    assert decision.mode == "excluded"
    assert decision.summary_only is False
    assert decision.index is False  # excluded ⇒ never indexed

    decision = licence_filter.classify({"mode": "metadata-only"})
    assert decision.mode == "metadata-only"
    assert decision.summary_only is True
    assert decision.embed is False  # metadata-only ⇒ no embedding

    decision = licence_filter.classify({"mode": "full-text"})
    assert decision.mode == "full-text"
    assert decision.summary_only is False
    assert decision.embed is True
    assert decision.chunk is True

    # Default (no mode key) ⇒ full-text for back-compat with spec-032 source.json
    decision = licence_filter.classify({})
    assert decision.mode == "full-text"
