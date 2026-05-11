"""T034 — Integration test: parity-gate FAIL halts alias flip (FR-RAG-IDX-04 §3.3).

Synthesises each of the four parity-gate signal failures and confirms the
orchestrator exits with code 2 (``EXIT_PARITY_FAIL``) and **does not flip**
the alias.
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


def _args() -> Namespace:
    return Namespace(
        corpus_root=CORPUS_ROOT,
        search_endpoint="",
        index_alias="corpus",
        target_index="corpus-v2",
        embedding_model="text-embedding-3-large@2",
        carveout_registry=CARVEOUT_REGISTRY,
        carveout_region="australiaeast",
        corpus_build_sha=None,
        mode="incremental",
        manifest_out=None,
        offline_bundle_out=None,
        jurisdiction="act",
        log_level="ERROR",
    )


def _setup_swap_alias() -> indexer.InMemoryAlias:
    """Stage an alias such that the current run triggers blue-green."""
    alias = indexer.InMemoryAlias(
        alias="corpus",
        active_index="corpus-v1",
        active_embedding_model_id="text-embedding-3-large@1",
    )
    alias.register_index("corpus-v1")
    return alias


@pytest.mark.parametrize(
    "synthetic_inputs,failed_signal",
    [
        # Signal 1 — chunk_count_delta > 5%
        (
            parity_gate.ParityInputs(
                old_chunk_count=1000,
                new_chunk_count=1100,
                old_embedding_cost_usd=10.0,
                new_embedding_cost_usd=10.0,
                decision_equivalence=1.0,
                new_index_distinct_embedding_model_ids=1,
            ),
            "chunk_count_delta",
        ),
        # Signal 2 — cost_ratio > 1.3
        (
            parity_gate.ParityInputs(
                old_chunk_count=1000,
                new_chunk_count=1000,
                old_embedding_cost_usd=10.0,
                new_embedding_cost_usd=14.0,
                decision_equivalence=1.0,
                new_index_distinct_embedding_model_ids=1,
            ),
            "cost_ratio",
        ),
        # Signal 3 — decision_equivalence < 0.95
        (
            parity_gate.ParityInputs(
                old_chunk_count=1000,
                new_chunk_count=1000,
                old_embedding_cost_usd=10.0,
                new_embedding_cost_usd=10.0,
                decision_equivalence=0.90,
                new_index_distinct_embedding_model_ids=1,
            ),
            "decision_equivalence",
        ),
    ],
)
def test_parity_fail_halts_flip(synthetic_inputs: parity_gate.ParityInputs, failed_signal: str) -> None:
    if not CORPUS_ROOT.exists():
        pytest.skip(f"corpus root {CORPUS_ROOT} not present")

    new_index = indexer.InMemoryIndex(name="corpus-v2")
    alias = _setup_swap_alias()
    audit = audit_mod.InMemoryAuditEmitter()

    result = ingest_main.run(
        args=_args(),
        index=new_index,
        alias=alias,
        embed=embedder.deterministic_stub_embedder(),
        audit_emitter=audit,
        parity_inputs_override=synthetic_inputs,
    )

    assert result.exit_code == ingest_main.EXIT_PARITY_FAIL
    assert result.parity_gate_status == "FAIL"
    assert any(s["name"] == failed_signal and not s["passed"] for s in result.parity_signals)

    # CRITICAL — alias must STILL point at the OLD index (no flip).
    assert alias.get_active_index() == "corpus-v1"
    assert alias.get_active_embedding_model_id() == "text-embedding-3-large@1"


def test_parity_signal4_multiple_model_ids_aborts_run() -> None:
    """Signal 4 (R-05) — pre-existing two model_ids in the new index aborts before flip."""
    if not CORPUS_ROOT.exists():
        pytest.skip(f"corpus root {CORPUS_ROOT} not present")

    new_index = indexer.InMemoryIndex(name="corpus-v2")
    # Pre-pollute with a doc carrying a different model_id — orchestrator must
    # detect this via ``BlueGreenIndexer.assert_single_embedding_model``.
    new_index.upload_documents(
        [
            {
                "chunk_id": "preexisting-c1",
                "corpus_entry_id": "x/y",
                "jurisdiction": "x",
                "topic": "y",
                "page": 1,
                "sha256_of_chunk": "0" * 64,
                "source_url": "https://example",
                "rendered_url": "/x/y/handbook.md#page-1",
                "licence_mode": "full-text",
                "corpus_build_sha": "0" * 64,
                "embedding_model_id": "rogue-model@9",
            }
        ]
    )
    alias = _setup_swap_alias()
    result = ingest_main.run(
        args=_args(),
        index=new_index,
        alias=alias,
        embed=embedder.deterministic_stub_embedder(),
        audit_emitter=audit_mod.InMemoryAuditEmitter(),
    )

    assert result.exit_code == ingest_main.EXIT_PARITY_FAIL
    # Alias unchanged.
    assert alias.get_active_index() == "corpus-v1"
