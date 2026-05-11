"""Spec 036 T098 — Bi-weekly parity report (FR-RAG-FM-06, Risk R11).

Computes the four metrics tracked in
``docs/canary/036-bi-weekly-parity-report.md`` from a pair of agent runs
(legacy vs Foundry-grounded) over the same fixture file.

Intended call site (Phase E2 schedules this):

    from ama_eval.parity_report import build_parity_report
    report = build_parity_report(
        fixture_path=Path("apps/eval-runner/fixtures/spec036/risk.jsonl"),
        legacy_results=legacy_runs,    # list[dict] from per_agent_canary_gate
        foundry_results=foundry_runs,  # list[dict]
    )

The report is JSON-serialisable; the GitHub Actions workflow uploads it
to Application Insights as a custom event ``spec036_parity_report``.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .citation_fidelity import (
    CITATION_FIDELITY_THRESHOLD,
    compute_citation_fidelity,
)

DECISION_EQUIVALENCE_THRESHOLD: float = 0.95
SCHEMA_EQUIVALENCE_THRESHOLD: float = 1.0


@dataclass(frozen=True)
class ParityReport:
    fixture_path: str
    cases_total: int
    decision_equivalence: float
    schema_equivalence: float
    citation_fidelity: float
    citation_verbatim_match: float
    hallucinated_citation_count: int
    passes: bool
    failures: list[str]

    def as_json(self) -> dict[str, Any]:
        return asdict(self)


def _decision_equivalence(legacy: list[dict[str, Any]], foundry: list[dict[str, Any]]) -> float:
    if not legacy:
        return 1.0
    matched = 0
    for left, right in zip(legacy, foundry, strict=False):
        if left.get("decision") == right.get("decision"):
            matched += 1
    return matched / len(legacy)


def _schema_equivalence(legacy: list[dict[str, Any]], foundry: list[dict[str, Any]]) -> float:
    if not legacy:
        return 1.0
    matched = 0
    for left, right in zip(legacy, foundry, strict=False):
        if set(left.keys()) == set(right.keys()):
            matched += 1
    return matched / len(legacy)


def _hallucinated_citation_count(foundry: list[dict[str, Any]]) -> int:
    n = 0
    for case in foundry:
        resp = case.get("foundry_response", {}) or {}
        retrieved = {c.get("sha256_of_chunk", "") for c in (resp.get("retrieved_chunks") or [])}
        for cit in resp.get("citations") or []:
            sha = cit.get("sha256_of_chunk", "")
            if sha and sha not in retrieved:
                n += 1
    return n


def build_parity_report(
    *,
    fixture_path: Path,
    legacy_results: list[dict[str, Any]],
    foundry_results: list[dict[str, Any]],
) -> ParityReport:
    decision_eq = _decision_equivalence(legacy_results, foundry_results)
    schema_eq = _schema_equivalence(legacy_results, foundry_results)
    fidelity_signal = compute_citation_fidelity(foundry_results)
    hallucinated = _hallucinated_citation_count(foundry_results)

    failures: list[str] = []
    if decision_eq < DECISION_EQUIVALENCE_THRESHOLD:
        failures.append(f"decision_equivalence {decision_eq:.3f} < {DECISION_EQUIVALENCE_THRESHOLD}")
    if schema_eq < SCHEMA_EQUIVALENCE_THRESHOLD:
        failures.append(f"schema_equivalence {schema_eq:.3f} < {SCHEMA_EQUIVALENCE_THRESHOLD}")
    if fidelity_signal.fidelity < CITATION_FIDELITY_THRESHOLD:
        failures.append(f"citation_fidelity {fidelity_signal.fidelity:.3f} < {CITATION_FIDELITY_THRESHOLD}")
    if hallucinated > 0:
        failures.append(f"hallucinated_citation_count {hallucinated} > 0")

    return ParityReport(
        fixture_path=str(fixture_path),
        cases_total=fidelity_signal.cases_total,
        decision_equivalence=decision_eq,
        schema_equivalence=schema_eq,
        citation_fidelity=fidelity_signal.fidelity,
        citation_verbatim_match=fidelity_signal.verbatim_match,
        hallucinated_citation_count=hallucinated,
        passes=not failures,
        failures=failures,
    )


__all__ = [
    "DECISION_EQUIVALENCE_THRESHOLD",
    "SCHEMA_EQUIVALENCE_THRESHOLD",
    "ParityReport",
    "build_parity_report",
]
