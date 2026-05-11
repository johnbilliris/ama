"""T036 — Entity test: chunk-index doc invariants (FR-RAG-IDX-02, -03, -04).

Generates a small corpus → runs the ingest pipeline → asserts every doc
written to the in-memory index carries the required provenance fields and
type-correct values.
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import os
import tempfile
import textwrap
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
# Use a repo-local scratch dir to dodge `tmp_path` permission failures on
# corporate Windows machines where `C:\Users\<u>\AppData\Local\Temp` is locked.
_SCRATCH_BASE = Path(__file__).resolve().parents[2] / "artifacts" / "test-scratch"


@contextlib.contextmanager
def _scratch_dir() -> os.PathLike[str]:  # type: ignore[misc]
    _SCRATCH_BASE.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=_SCRATCH_BASE) as d:
        yield Path(d)


REQUIRED_FIELDS_FULL_TEXT = {
    "chunk_id",
    "corpus_entry_id",
    "jurisdiction",
    "topic",
    "page",
    "tokens",
    "sha256_of_chunk",
    "source_url",
    "rendered_url",
    "licence_mode",
    "corpus_build_sha",
    "embedding_model_id",
    "embedding",
    "text",
}


def _make_synthetic_corpus(root: Path, *, mode: str = "full-text") -> None:
    handbook_md = (
        textwrap.dedent("""
        # Synthetic Handbook

        ## Page 1

        This is page one of a synthetic disaster-response handbook used solely for
        spec-036 invariant tests. It contains nothing real and references no
        publisher.

        ## Page 2

        Second page. Lorem ipsum dolor sit amet, consectetur adipiscing elit.
    """).strip()
        + "\n"
    )
    sha = hashlib.sha256(handbook_md.encode("utf-8")).hexdigest()
    source = {
        "title": "Synthetic Handbook",
        "publisher": "Synthetic Authority",
        "licence": "TEST-INTERNAL",
        "url": "https://example.gov.au/synthetic/handbook.pdf",
        "sha256": sha,
        "retrieved_at": datetime.now(tz=UTC).isoformat(),
        "mode": mode,
    }
    target = root / "synthetic-jurisdiction" / "synthetic-topic"
    target.mkdir(parents=True, exist_ok=True)
    (target / "handbook.md").write_text(handbook_md, encoding="utf-8")
    (target / "source.json").write_text(json.dumps(source, indent=2), encoding="utf-8")


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


def test_chunk_required_provenance_fields() -> None:
    with _scratch_dir() as tmp_path:
        # Allowed jurisdictions enforced by the chunker — patch in a real one.
        corpus = tmp_path / "corpus"
        corpus.mkdir()
        handbook = (
            textwrap.dedent("""
            # ACT Test Handbook

            ## Page 1

            Body text page one for invariant tests.
        """).strip()
            + "\n"
        )
        target = corpus / "act" / "test-topic"
        target.mkdir(parents=True)
        (target / "handbook.md").write_text(handbook, encoding="utf-8")
        (target / "source.json").write_text(
            json.dumps(
                {
                    "title": "ACT Test",
                    "publisher": "Test",
                    "licence": "TEST",
                    "url": "https://example.act.gov.au/test.pdf",
                    "sha256": hashlib.sha256(handbook.encode("utf-8")).hexdigest(),
                    "retrieved_at": datetime.now(tz=UTC).isoformat(),
                    "mode": "full-text",
                },
                indent=2,
            ),
            encoding="utf-8",
        )

        index = indexer.InMemoryIndex(name="corpus-v1")
        alias = indexer.InMemoryAlias(alias="corpus", active_index=None)

        result = ingest_main.run(
            args=_args(corpus),
            index=index,
            alias=alias,
            embed=embedder.deterministic_stub_embedder(),
            audit_emitter=audit_mod.InMemoryAuditEmitter(),
        )
        assert result.exit_code == 0, result.parity_signals
        assert result.chunks_written >= 1

        docs = list(index.all_documents())
        assert docs, "expected at least one indexed document"

        for doc in docs:
            if doc["licence_mode"] == "full-text":
                missing = REQUIRED_FIELDS_FULL_TEXT - set(doc)
                assert not missing, f"chunk missing fields: {sorted(missing)}"
                assert isinstance(doc["page"], int)
                assert isinstance(doc["tokens"], int)
                assert doc["tokens"] > 0
                assert isinstance(doc["embedding"], list)
                assert len(doc["embedding"]) == embedder.EMBEDDING_DIMS
                assert doc["sha256_of_chunk"] != "0" * 64
                assert doc["rendered_url"].startswith("/docs/corpus/")
                assert doc["embedding_model_id"] == "text-embedding-3-large@1"
                assert doc["jurisdiction"] == "act"
                assert doc["topic"] == "test-topic"


def test_metadata_only_chunks_omit_body_and_embedding() -> None:
    """FR-RAG-IDX-02 — metadata-only docs MUST NOT carry text or embedding."""
    with _scratch_dir() as tmp_path:
        corpus = tmp_path / "corpus"
        target = corpus / "nsw" / "metadata-only-topic"
        target.mkdir(parents=True)
        handbook = "# header\n\n## Page 1\nBody must NOT be indexed.\n"
        (target / "handbook.md").write_text(handbook, encoding="utf-8")
        (target / "source.json").write_text(
            json.dumps(
                {
                    "title": "Metadata-Only",
                    "publisher": "Test",
                    "licence": "TEST",
                    "url": "https://example.nsw.gov.au/meta.pdf",
                    "sha256": hashlib.sha256(handbook.encode("utf-8")).hexdigest(),
                    "retrieved_at": datetime.now(tz=UTC).isoformat(),
                    "mode": "metadata-only",
                },
                indent=2,
            ),
            encoding="utf-8",
        )

        index = indexer.InMemoryIndex(name="corpus-v1")
        result = ingest_main.run(
            args=_args(corpus),
            index=index,
            alias=indexer.InMemoryAlias(alias="corpus", active_index=None),
            embed=embedder.deterministic_stub_embedder(),
            audit_emitter=audit_mod.InMemoryAuditEmitter(),
        )
        assert result.exit_code == 0
        metadata_docs = [d for d in index.all_documents() if d["licence_mode"] == "metadata-only"]
        assert metadata_docs, "expected metadata-only doc to be indexed"
        for doc in metadata_docs:
            assert "text" not in doc or not doc.get("text"), "metadata-only doc must not carry body text"
            # The vector index field MUST be absent for metadata-only.
            assert "embedding" not in doc or not doc.get("embedding"), (
                "metadata-only doc must not carry an embedding vector"
            )
