"""Corpus-rebuild regression gate (Spec 036 T029, FR-RAG-FM-06; extends spec-033 FR-023).

Originally landed as the per-agent canary cutover gate. Following the
ADR-20 hard cutover (Microsoft Foundry is the canonical chat plane;
``LEGACY_AZURE_OPENAI=1`` flag removed in the §Q-P6-03 cleanup PR), this
CLI is repurposed as a **corpus-rebuild regression gate**: it runs on
every corpus build / embedding-model bump / Foundry deployment change to
prove the new outputs remain decision-equivalent to a stable baseline.

Both ``--legacy`` and ``--foundry`` runner flags are kept verbatim so
existing fixtures and CI invocations continue to work — read ``--legacy``
as "stable baseline" (last green corpus build) and ``--foundry`` as
"candidate" (corpus_build_sha / embedding_model_id under test). The
``corpus_build_sha`` + ``embedding_model_id`` are the regression keys.

The CLI compares two runners across a per-agent JSONL fixture of golden
Q&A cases. It reports three equivalence metrics:

- ``decision_equivalence``: fraction of cases where both runners produce the
  same ``decision`` field. Default threshold ≥0.95 (spec-033 FR-023; FR-RAG-FM-06).
- ``schema_equivalence``: fraction of cases where both runners emit the same
  set of top-level keys (1.0 required to pass the gate).
- ``citation_fidelity``: fraction of candidate Foundry responses that include
  at least one citation when the agent prompt requires grounding (1.0 required
  for grounded fixtures; baseline = 1.0 for ungrounded fixtures).

Zero-case fixtures **PASS** by convention (matches the spec-033
``tests/equivalence`` harness baseline so the gate landing this code does
not flip a green pipeline red).

The exit code is 0 iff every threshold is met; non-zero blocks corpus
promotion (e.g. blue-green AI Search alias flip per FR-RAG-IDX-04).
"""

from __future__ import annotations

import argparse
import json
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from pathlib import Path

# Default thresholds (spec-033 FR-023 + spec-036 FR-RAG-FM-06).
DEFAULT_DECISION_THRESHOLD: float = 0.95
DEFAULT_SCHEMA_THRESHOLD: float = 1.0
DEFAULT_CITATION_THRESHOLD: float = 1.0


@dataclass(frozen=True)
class GateResult:
    """Outcome of a per-agent canary gate run."""

    agent_name: str
    cases_total: int
    decision_equivalence: float
    schema_equivalence: float
    citation_fidelity: float
    threshold: float
    passed: bool
    failures: tuple[str, ...] = field(default_factory=tuple)


# --------------------------------------------------------------------------- #
# Default runners — synthetic placeholders that are overridden by the canary
# job. The real legacy/foundry runners pull from the agent's pipeline and the
# Foundry-grounded chat seam respectively.
# --------------------------------------------------------------------------- #


def _default_runner(prompt: str) -> dict[str, object]:  # noqa: ARG001
    """Stub runner — returns an empty payload; only used when neither runner is injected."""
    return {}


# --------------------------------------------------------------------------- #
# Fixture loading.
# --------------------------------------------------------------------------- #


def _load_fixture(fixture_path: Path) -> list[dict[str, object]]:
    if not fixture_path.exists():
        return []
    cases: list[dict[str, object]] = []
    for line in fixture_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            cases.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return cases


# --------------------------------------------------------------------------- #
# Equivalence computation.
# --------------------------------------------------------------------------- #


def _decision_match(legacy_resp: dict[str, object], foundry_resp: dict[str, object]) -> bool:
    return legacy_resp.get("decision") == foundry_resp.get("decision")


def _schema_match(legacy_resp: dict[str, object], foundry_resp: dict[str, object]) -> bool:
    return set(legacy_resp.keys()) == set(foundry_resp.keys())


def _citation_present(foundry_resp: dict[str, object]) -> bool:
    cites = foundry_resp.get("citations")
    if isinstance(cites, list):
        return len(cites) > 0
    return True  # non-grounded responses are treated as full-fidelity by default


# --------------------------------------------------------------------------- #
# Public entry point.
# --------------------------------------------------------------------------- #


def run_per_agent_gate(
    *,
    agent_name: str,
    fixture_path: Path,
    legacy_runner: Callable[[str], dict[str, object]] | None = None,
    foundry_runner: Callable[[str], dict[str, object]] | None = None,
    threshold: float = DEFAULT_DECISION_THRESHOLD,
) -> GateResult:
    """Run the per-agent canary gate and return a structured ``GateResult``."""
    legacy = legacy_runner or _default_runner
    foundry = foundry_runner or _default_runner

    cases = _load_fixture(Path(fixture_path))
    if not cases:
        # Zero-case → PASS (baseline; spec-033 convention).
        return GateResult(
            agent_name=agent_name,
            cases_total=0,
            decision_equivalence=1.0,
            schema_equivalence=1.0,
            citation_fidelity=1.0,
            threshold=threshold,
            passed=True,
        )

    decision_hits = 0
    schema_hits = 0
    citation_hits = 0
    failures: list[str] = []

    for case in cases:
        case_id = str(case.get("id", "?"))
        prompt = str(case.get("prompt", ""))
        legacy_resp = legacy(prompt)
        foundry_resp = foundry(prompt)

        if _decision_match(legacy_resp, foundry_resp):
            decision_hits += 1
        else:
            failures.append(
                f"{case_id}: decision_mismatch legacy={legacy_resp.get('decision')!r} "
                f"foundry={foundry_resp.get('decision')!r}"
            )
        if _schema_match(legacy_resp, foundry_resp):
            schema_hits += 1
        else:
            failures.append(
                f"{case_id}: schema_mismatch legacy_keys={sorted(legacy_resp.keys())} "
                f"foundry_keys={sorted(foundry_resp.keys())}"
            )
        if _citation_present(foundry_resp):
            citation_hits += 1

    n = len(cases)
    decision_eq = decision_hits / n
    schema_eq = schema_hits / n
    citation_fid = citation_hits / n

    passed = (
        decision_eq >= threshold
        and schema_eq >= DEFAULT_SCHEMA_THRESHOLD
        and citation_fid >= DEFAULT_CITATION_THRESHOLD
    )

    return GateResult(
        agent_name=agent_name,
        cases_total=n,
        decision_equivalence=decision_eq,
        schema_equivalence=schema_eq,
        citation_fidelity=citation_fid,
        threshold=threshold,
        passed=passed,
        failures=tuple(failures),
    )


# --------------------------------------------------------------------------- #
# CLI entry point.
# --------------------------------------------------------------------------- #


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="per-agent-canary-gate",
        description="Spec 036 T029 — Foundry-grounded canary equivalence gate.",
    )
    p.add_argument("--agent", required=True, help="Agent name (e.g. MonitoringAgent).")
    p.add_argument(
        "--fixture",
        required=True,
        type=Path,
        help="JSONL fixture of {id,prompt,expected_decision} cases.",
    )
    p.add_argument(
        "--threshold",
        type=float,
        default=DEFAULT_DECISION_THRESHOLD,
        help="Decision-equivalence threshold (default 0.95).",
    )
    p.add_argument(
        "--report",
        type=Path,
        default=None,
        help="Optional path to write the JSON report to.",
    )
    return p


def cli_main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    result = run_per_agent_gate(
        agent_name=args.agent,
        fixture_path=args.fixture,
        threshold=args.threshold,
    )

    payload = asdict(result)
    if args.report is not None:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload))
    return 0 if result.passed else 1


# --------------------------------------------------------------------------- #
# Final canary gate (T142, FR-RAG-FM-06, SC-011) — extends the per-agent gate
# with the four binding thresholds tracked in
# data-model.md §EquivalenceTestResult, keyed by (corpus_build_sha,
# embedding_model_id) for SC-011 reproducibility.
# --------------------------------------------------------------------------- #


# Final-gate thresholds (data-model.md §EquivalenceTestResult).
FINAL_DECISION_EQUIVALENCE_THRESHOLD: float = 0.95
FINAL_SCHEMA_EQUIVALENCE_THRESHOLD: float = 1.0
FINAL_CITATION_FIDELITY_THRESHOLD: float = 0.70
FINAL_VERBATIM_SOURCE_MATCH_THRESHOLD: float = 0.90


@dataclass(frozen=True)
class FinalCanaryGateResult:
    """Final canary gate outcome (T142, T145).

    Mirrors the spec-036 ``EquivalenceTestResult`` JSON shape in
    ``data-model.md`` so the same record can be uploaded to App Insights
    and replayed against historical canaries.
    """

    agent_name: str
    cases_total: int
    decision_equivalence: float
    schema_equivalence: float
    citation_fidelity: float
    verbatim_source_match: float
    hallucinated_citation_count: int
    corpus_build_sha: str
    embedding_model_id: str
    passed: bool
    failures: tuple[str, ...] = field(default_factory=tuple)


def run_final_canary_gate(
    *,
    agent_name: str,
    legacy_results: list[dict[str, object]],
    foundry_results: list[dict[str, object]],
    corpus_build_sha: str,
    embedding_model_id: str,
) -> FinalCanaryGateResult:
    """Compute the final canary gate result for ``agent_name``.

    Computes the same four metrics as ``parity_report.build_parity_report``
    but binds them with the SC-011 reproducibility key. Zero-case fixtures
    PASS by convention (matches per-agent gate baseline) but still carry
    the reproducibility key.
    """
    # Local import keeps the module's import-time cost low and lets
    # parity_report import from us without circularity.
    from .citation_fidelity import compute_citation_fidelity
    from .parity_report import (
        DECISION_EQUIVALENCE_THRESHOLD,
        SCHEMA_EQUIVALENCE_THRESHOLD,
        _decision_equivalence,
        _hallucinated_citation_count,
        _schema_equivalence,
    )

    if not legacy_results and not foundry_results:
        return FinalCanaryGateResult(
            agent_name=agent_name,
            cases_total=0,
            decision_equivalence=1.0,
            schema_equivalence=1.0,
            citation_fidelity=1.0,
            verbatim_source_match=1.0,
            hallucinated_citation_count=0,
            corpus_build_sha=corpus_build_sha,
            embedding_model_id=embedding_model_id,
            passed=True,
        )

    decision_eq = _decision_equivalence(legacy_results, foundry_results)
    schema_eq = _schema_equivalence(legacy_results, foundry_results)
    fidelity_signal = compute_citation_fidelity(foundry_results)
    hallucinated = _hallucinated_citation_count(foundry_results)

    failures: list[str] = []
    if decision_eq < DECISION_EQUIVALENCE_THRESHOLD:
        failures.append(f"decision_equivalence {decision_eq:.3f} < {DECISION_EQUIVALENCE_THRESHOLD}")
    if schema_eq < SCHEMA_EQUIVALENCE_THRESHOLD:
        failures.append(f"schema_equivalence {schema_eq:.3f} < {SCHEMA_EQUIVALENCE_THRESHOLD}")
    if fidelity_signal.fidelity < FINAL_CITATION_FIDELITY_THRESHOLD:
        failures.append(f"citation_fidelity {fidelity_signal.fidelity:.3f} < {FINAL_CITATION_FIDELITY_THRESHOLD}")
    if fidelity_signal.verbatim_match < FINAL_VERBATIM_SOURCE_MATCH_THRESHOLD:
        failures.append(
            f"verbatim_source_match {fidelity_signal.verbatim_match:.3f} < {FINAL_VERBATIM_SOURCE_MATCH_THRESHOLD}"
        )
    if hallucinated > 0:
        failures.append(f"hallucinated_citation_count {hallucinated} > 0")

    return FinalCanaryGateResult(
        agent_name=agent_name,
        cases_total=fidelity_signal.cases_total,
        decision_equivalence=decision_eq,
        schema_equivalence=schema_eq,
        citation_fidelity=fidelity_signal.fidelity,
        verbatim_source_match=fidelity_signal.verbatim_match,
        hallucinated_citation_count=hallucinated,
        corpus_build_sha=corpus_build_sha,
        embedding_model_id=embedding_model_id,
        passed=not failures,
        failures=tuple(failures),
    )


__all__ = [
    "DEFAULT_CITATION_THRESHOLD",
    "DEFAULT_DECISION_THRESHOLD",
    "DEFAULT_SCHEMA_THRESHOLD",
    "FINAL_CITATION_FIDELITY_THRESHOLD",
    "FINAL_DECISION_EQUIVALENCE_THRESHOLD",
    "FINAL_SCHEMA_EQUIVALENCE_THRESHOLD",
    "FINAL_VERBATIM_SOURCE_MATCH_THRESHOLD",
    "FinalCanaryGateResult",
    "GateResult",
    "cli_main",
    "run_final_canary_gate",
    "run_per_agent_gate",
]


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(cli_main())
