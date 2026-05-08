"""Spec 036 T098/T100 — citation_fidelity + parity_report unit tests."""

from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("ama_eval.citation_fidelity")
pytest.importorskip("ama_eval.parity_report")

from ama_eval.citation_fidelity import (  # noqa: E402
    CITATION_FIDELITY_THRESHOLD,
    compute_citation_fidelity,
)
from ama_eval.parity_report import build_parity_report  # noqa: E402


def _case(*, requires_citation: bool, citations, retrieved_chunks, decision: str = "accept", schema_keys=None):
    return {
        "id": "case-1",
        "decision": decision,
        "expected": {"requires_citation": requires_citation},
        "foundry_response": {
            "citations": citations,
            "retrieved_chunks": retrieved_chunks,
            **({k: None for k in (schema_keys or [])}),
        },
    }


def test_citation_fidelity_perfect_score() -> None:
    sha = "a" * 64
    chunks = [{"sha256_of_chunk": sha, "text": "When the area is deemed safe…"}]
    citations = [
        {
            "sha256_of_chunk": sha,
            "rendered_url": "/docs/corpus/nsw/x/handbook.md#page-1",
            "snippet": "When the area is deemed safe",
        }
    ]
    cases = [_case(requires_citation=True, citations=citations, retrieved_chunks=chunks)]
    sig = compute_citation_fidelity(cases)
    assert sig.fidelity == 1.0
    assert sig.verbatim_match == 1.0


def test_citation_fidelity_misses_when_sha_unknown() -> None:
    citations = [
        {
            "sha256_of_chunk": "z" * 64,
            "rendered_url": "/docs/corpus/nsw/x/handbook.md#page-1",
        }
    ]
    chunks = [{"sha256_of_chunk": "a" * 64, "text": "x"}]
    cases = [_case(requires_citation=True, citations=citations, retrieved_chunks=chunks)]
    sig = compute_citation_fidelity(cases)
    assert sig.fidelity == 0.0


def test_citation_fidelity_skips_cases_without_required_citation() -> None:
    cases = [_case(requires_citation=False, citations=[], retrieved_chunks=[])]
    sig = compute_citation_fidelity(cases)
    assert sig.fidelity == 1.0
    assert sig.verbatim_match == 1.0


def test_parity_report_pass() -> None:
    sha = "a" * 64
    chunks = [{"sha256_of_chunk": sha, "text": "Compliant snippet"}]
    citations = [{"sha256_of_chunk": sha, "rendered_url": "/x", "snippet": "Compliant snippet"}]

    def case():
        return {
            "id": "c",
            "decision": "accept",
            "expected": {"requires_citation": True},
            "foundry_response": {"citations": citations, "retrieved_chunks": chunks},
        }

    legacy = [case() for _ in range(20)]
    foundry = [case() for _ in range(20)]
    report = build_parity_report(
        fixture_path=Path("apps/eval-runner/fixtures/spec036/risk.jsonl"),
        legacy_results=legacy,
        foundry_results=foundry,
    )
    assert report.passes is True
    assert report.decision_equivalence == 1.0
    assert report.schema_equivalence == 1.0
    assert report.citation_fidelity >= CITATION_FIDELITY_THRESHOLD
    assert report.hallucinated_citation_count == 0


def test_parity_report_fails_on_decision_drift() -> None:
    sha = "a" * 64
    chunks = [{"sha256_of_chunk": sha, "text": "x"}]
    citations = [{"sha256_of_chunk": sha, "rendered_url": "/x"}]

    def case(decision: str):
        return {
            "id": "c",
            "decision": decision,
            "expected": {"requires_citation": True},
            "foundry_response": {"citations": citations, "retrieved_chunks": chunks},
        }

    legacy = [case("accept") for _ in range(20)]
    foundry = [case("escalate") for _ in range(20)]  # 0% match
    report = build_parity_report(
        fixture_path=Path("apps/eval-runner/fixtures/spec036/risk.jsonl"),
        legacy_results=legacy,
        foundry_results=foundry,
    )
    assert report.passes is False
    assert any("decision_equivalence" in f for f in report.failures)


def test_parity_report_flags_hallucinated_citations() -> None:
    chunks = [{"sha256_of_chunk": "a" * 64, "text": "x"}]
    bad_citations = [{"sha256_of_chunk": "z" * 64, "rendered_url": "/x"}]

    def case():
        return {
            "id": "c",
            "decision": "accept",
            "expected": {"requires_citation": False},
            "foundry_response": {"citations": bad_citations, "retrieved_chunks": chunks},
        }

    cases = [case() for _ in range(5)]
    report = build_parity_report(
        fixture_path=Path("apps/eval-runner/fixtures/spec036/risk.jsonl"),
        legacy_results=cases,
        foundry_results=cases,
    )
    assert report.hallucinated_citation_count == 5
    assert report.passes is False
