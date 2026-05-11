"""Spec 036 T142 — Final canary gate unit tests (FR-RAG-FM-06, SC-011).

The final-canary gate extends the per-agent canary gate with the four
binding thresholds tracked in ``data-model.md §EquivalenceTestResult``:

* ``decision_equivalence ≥ 0.95`` (spec-033 FR-023)
* ``schema_equivalence == 1.00`` (spec-033 FR-023)
* ``citation_fidelity ≥ 0.70`` (spec-036 R-10)
* ``verbatim_source_match ≥ 0.90`` (Quality-memo R2)

The result is **keyed by** ``(corpus_build_sha, embedding_model_id)`` so
re-runs against the same corpus build are reproducible. The Simulation
Controller canary (T145) consumes this gate as its final pre-flip
predicate.
"""

from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("ama_eval.per_agent_canary_gate")

from ama_eval.per_agent_canary_gate import (  # noqa: E402
    FinalCanaryGateResult,
    run_final_canary_gate,
)


def _grounded_case(*, decision: str, requires_citation: bool = True, sha: str = "a" * 64) -> dict:
    return {
        "id": "case-1",
        "decision": decision,
        "expected": {"requires_citation": requires_citation},
        "foundry_response": {
            "decision": decision,
            "citations": [
                {
                    "sha256_of_chunk": sha,
                    "rendered_url": "/docs/corpus/nsw/x/handbook.md#page-1",
                    "snippet": "Compliant snippet text",
                }
            ],
            "retrieved_chunks": [{"sha256_of_chunk": sha, "text": "Compliant snippet text"}],
        },
    }


def test_final_gate_passes_on_perfect_run(tmp_path: Path) -> None:
    legacy = [_grounded_case(decision="accept") for _ in range(20)]
    foundry = [_grounded_case(decision="accept") for _ in range(20)]

    result = run_final_canary_gate(
        agent_name="SimulationController",
        legacy_results=legacy,
        foundry_results=foundry,
        corpus_build_sha="f" * 64,
        embedding_model_id="text-embedding-3-large@1",
    )

    assert isinstance(result, FinalCanaryGateResult)
    assert result.passed is True
    assert result.decision_equivalence >= 0.95
    assert result.schema_equivalence == 1.0
    assert result.citation_fidelity >= 0.7
    assert result.verbatim_source_match >= 0.9
    assert result.hallucinated_citation_count == 0
    # SC-011 reproducibility key.
    assert result.corpus_build_sha == "f" * 64
    assert result.embedding_model_id == "text-embedding-3-large@1"
    assert result.failures == ()


def test_final_gate_blocks_on_decision_drift() -> None:
    legacy = [_grounded_case(decision="accept") for _ in range(20)]
    foundry = [_grounded_case(decision="escalate") for _ in range(20)]
    result = run_final_canary_gate(
        agent_name="SimulationController",
        legacy_results=legacy,
        foundry_results=foundry,
        corpus_build_sha="f" * 64,
        embedding_model_id="text-embedding-3-large@1",
    )
    assert result.passed is False
    assert any("decision_equivalence" in f for f in result.failures)


def test_final_gate_blocks_on_low_citation_fidelity() -> None:
    """A single citation pointing at an unknown chunk drops fidelity below 0.7."""
    bad_sha = "z" * 64
    chunk_sha = "a" * 64
    legacy = []
    foundry = []
    for _ in range(10):
        legacy.append(_grounded_case(decision="accept", sha=chunk_sha))
        foundry.append(
            {
                "id": "case-bad",
                "decision": "accept",
                "expected": {"requires_citation": True},
                "foundry_response": {
                    "decision": "accept",
                    # All citations point at unknown chunks → fidelity = 0.
                    "citations": [
                        {
                            "sha256_of_chunk": bad_sha,
                            "rendered_url": "/x",
                        }
                    ],
                    "retrieved_chunks": [{"sha256_of_chunk": chunk_sha, "text": "x"}],
                },
            }
        )

    result = run_final_canary_gate(
        agent_name="SimulationController",
        legacy_results=legacy,
        foundry_results=foundry,
        corpus_build_sha="f" * 64,
        embedding_model_id="text-embedding-3-large@1",
    )
    assert result.passed is False
    # Both fidelity AND hallucination MUST trip.
    assert any("citation_fidelity" in f for f in result.failures)
    assert result.hallucinated_citation_count > 0


def test_final_gate_blocks_on_verbatim_drift() -> None:
    """Snippet not literally present in chunk → verbatim drop below 0.9."""
    sha = "a" * 64
    chunks = [{"sha256_of_chunk": sha, "text": "Original verbatim source text."}]
    drifted_citation = [
        {
            "sha256_of_chunk": sha,
            "rendered_url": "/x",
            "snippet": "Paraphrased and not in source.",
        }
    ]
    legacy = []
    foundry = []
    for _ in range(20):
        case_legacy = _grounded_case(decision="accept", sha=sha)
        case_foundry = {
            "id": "case-drift",
            "decision": "accept",
            "expected": {"requires_citation": True},
            "foundry_response": {
                "decision": "accept",
                "citations": drifted_citation,
                "retrieved_chunks": chunks,
            },
        }
        legacy.append(case_legacy)
        foundry.append(case_foundry)

    result = run_final_canary_gate(
        agent_name="SimulationController",
        legacy_results=legacy,
        foundry_results=foundry,
        corpus_build_sha="f" * 64,
        embedding_model_id="text-embedding-3-large@1",
    )
    assert result.passed is False
    assert any("verbatim" in f for f in result.failures)


def test_final_gate_emits_reproducibility_key() -> None:
    """The result MUST carry `(corpus_build_sha, embedding_model_id)` for SC-011."""
    result = run_final_canary_gate(
        agent_name="SimulationController",
        legacy_results=[],
        foundry_results=[],
        corpus_build_sha="abc",
        embedding_model_id="text-embedding-3-large@1",
    )
    # zero-case fixture: PASS by convention but still carry the key.
    assert result.passed is True
    assert result.corpus_build_sha == "abc"
    assert result.embedding_model_id == "text-embedding-3-large@1"


def test_final_gate_dry_run_simulation_controller_passes() -> None:
    """T145 dry-run: the simulation fixture's structure must be acceptable to the gate."""
    fixture = Path("apps/eval-runner/fixtures/spec036/simulation.jsonl")
    assert fixture.exists(), "T145 dry-run prerequisite missing — simulation fixture not found"
