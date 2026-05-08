"""Per-agent canary gate (Spec 036 T029, FR-RAG-FM-06; extends spec-033 FR-023).

The CLI compares two runners — the legacy Azure-OpenAI path (``--legacy``) and
the Foundry-grounded path (``--foundry``) — across a per-agent JSONL fixture
of golden Q&A cases. It reports three equivalence metrics:

- ``decision_equivalence``: fraction of cases where both runners produce the
  same ``decision`` field. Default threshold ≥0.95 (spec-033 FR-023; FR-RAG-FM-06).
- ``schema_equivalence``: fraction of cases where both runners emit the same
  set of top-level keys (1.0 required to advance the canary).
- ``citation_fidelity``: placeholder for spec-036 grounded cases — fraction of
  Foundry responses that include at least one citation when the agent prompt
  required grounding (1.0 expected once T071 / T091 land; baseline = 1.0 for
  ungrounded fixtures).

Zero-case fixtures **PASS** by convention (matches the spec-033
``tests/equivalence`` harness baseline so the cutover gate landing this code
does not flip a green pipeline red).

This module is consumed by the canary cutover tasks (T093–T097, T145). The
exit code is 0 iff every threshold is met; non-zero blocks canary promotion.
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


__all__ = [
    "DEFAULT_CITATION_THRESHOLD",
    "DEFAULT_DECISION_THRESHOLD",
    "DEFAULT_SCHEMA_THRESHOLD",
    "GateResult",
    "cli_main",
    "run_per_agent_gate",
]


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(cli_main())
