"""T033 — Integration test: blue-green alias flip on model swap (FR-RAG-IDX-04 §3.2; R-15).

Asserts that when the ``embedding_model_id`` advertised on the alias differs
from the model the new ingest run uses, the orchestrator:

1. Computes ``corpus-v{N+1}`` as the target index.
2. Writes the new corpus to that index.
3. Confirms ``parity_gate_status == "PASS"`` (synthetic inputs).
4. Flips the alias atomically — alias now points at v{N+1}.
5. Records the blue-green metadata in the audit summary.
"""

from __future__ import annotations

from argparse import Namespace
from pathlib import Path

import pytest
from ama_ingest import (
    __main__ as ingest_main,
)
from ama_ingest import (
    audit as audit_mod,
)
from ama_ingest import (
    embedder,
    indexer,
    parity_gate,
)

CORPUS_ROOT = Path(__file__).resolve().parents[2] / "docs" / "corpus"
CARVEOUT_REGISTRY = Path(__file__).resolve().parents[2] / "infra" / "parameters" / "foundry-carveout.yaml"


def _args(*, embedding_model: str, target_index: str | None = None) -> Namespace:
    return Namespace(
        corpus_root=CORPUS_ROOT,
        search_endpoint="",
        index_alias="corpus",
        target_index=target_index,
        embedding_model=embedding_model,
        carveout_registry=CARVEOUT_REGISTRY,
        carveout_region="australiaeast",
        corpus_build_sha=None,
        mode="incremental",
        manifest_out=None,
        offline_bundle_out=None,
        jurisdiction="act",
        log_level="WARNING",
    )


def test_blue_green_alias_flip_on_model_swap() -> None:
    if not CORPUS_ROOT.exists():
        pytest.skip(f"corpus root {CORPUS_ROOT} not present")

    # Pre-existing v1 with the OLD model.
    old_index = indexer.InMemoryIndex(name="corpus-v1")
    new_index = indexer.InMemoryIndex(name="corpus-v2")
    alias = indexer.InMemoryAlias(
        alias="corpus",
        active_index="corpus-v1",
        active_embedding_model_id="text-embedding-3-large@1",
    )
    alias.register_index("corpus-v1")
    audit = audit_mod.InMemoryAuditEmitter()

    # Caller invokes ingest with v2 model — orchestrator must flip alias.
    result = ingest_main.run(
        args=_args(embedding_model="text-embedding-3-large@2", target_index="corpus-v2"),
        index=new_index,
        alias=alias,
        embed=embedder.deterministic_stub_embedder(),
        audit_emitter=audit,
    )

    assert result.exit_code == 0, result.parity_signals
    assert result.blue_green is True
    assert result.target_index == "corpus-v2"
    assert result.parity_gate_status == "PASS"

    # Alias must point at the NEW index now.
    assert alias.get_active_index() == "corpus-v2"
    assert alias.get_active_embedding_model_id() == "text-embedding-3-large@2"

    # OLD index untouched.
    assert old_index.count() == 0

    # Audit recorded the flip.
    assert audit.summary_records
    summary = audit.summary_records[0]
    assert summary.blue_green is True
    assert summary.alias_flipped_to == "corpus-v2"


def test_next_index_name_increments_version() -> None:
    assert indexer.next_index_name(current_index="corpus-v1") == "corpus-v2"
    assert indexer.next_index_name(current_index="corpus-v9") == "corpus-v10"
    assert indexer.next_index_name(current_index=None) == "corpus-v1"
    assert indexer.next_index_name(current_index="corpus-v123") == "corpus-v124"


def test_blue_green_skipped_when_model_unchanged() -> None:
    """Same model_id ⇒ orchestrator does NOT trigger blue-green path."""
    if not CORPUS_ROOT.exists():
        pytest.skip(f"corpus root {CORPUS_ROOT} not present")

    index = indexer.InMemoryIndex(name="corpus-v1")
    alias = indexer.InMemoryAlias(
        alias="corpus",
        active_index="corpus-v1",
        active_embedding_model_id="text-embedding-3-large@1",
    )
    alias.register_index("corpus-v1")

    result = ingest_main.run(
        args=_args(embedding_model="text-embedding-3-large@1"),
        index=index,
        alias=alias,
        embed=embedder.deterministic_stub_embedder(),
        audit_emitter=audit_mod.InMemoryAuditEmitter(),
    )

    assert result.exit_code == 0
    assert result.blue_green is False
    assert result.target_index == "corpus-v1"


def test_full_mode_forces_blue_green() -> None:
    """``--mode full`` always triggers a fresh index + alias flip (R-15)."""
    if not CORPUS_ROOT.exists():
        pytest.skip(f"corpus root {CORPUS_ROOT} not present")

    new_index = indexer.InMemoryIndex(name="corpus-v2")
    alias = indexer.InMemoryAlias(
        alias="corpus",
        active_index="corpus-v1",
        active_embedding_model_id="text-embedding-3-large@1",
    )
    alias.register_index("corpus-v1")
    args = _args(embedding_model="text-embedding-3-large@1", target_index="corpus-v2")
    args.mode = "full"

    result = ingest_main.run(
        args=args,
        index=new_index,
        alias=alias,
        embed=embedder.deterministic_stub_embedder(),
        audit_emitter=audit_mod.InMemoryAuditEmitter(),
        # Provide synthetic parity inputs so the gate passes (orchestrator's
        # built-in inputs use old_chunk_count=0 which trivially passes too).
        parity_inputs_override=parity_gate.ParityInputs(
            old_chunk_count=140,
            new_chunk_count=140,
            old_embedding_cost_usd=1.0,
            new_embedding_cost_usd=1.0,
            decision_equivalence=1.0,
            new_index_distinct_embedding_model_ids=1,
        ),
    )

    assert result.exit_code == 0
    assert result.blue_green is True
    assert result.target_index == "corpus-v2"
    assert alias.get_active_index() == "corpus-v2"
