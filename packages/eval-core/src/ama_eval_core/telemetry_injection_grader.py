"""Telemetry-Injection v1 grader (T-J12).

Pure scoring routine for the telemetry-injection prompt evaluation:
given a *predicted* TypedSignal envelope and an *expected* envelope from
the ``telemetry_injection_v1`` dataset, returns a weighted equivalence
score in ``[0.0, 1.0]``.

A "pass" is when the per-case weighted score ≥ ``grading.pass_threshold``
(default 0.95). The dataset-level pass-rate is asserted ≥ 0.95 in
``packages/eval-core/tests/test_telemetry_injection_eval.py``.

The grader is **deterministic** — no stochastic LLM judges — so it
runs offline in CI without Foundry. The Foundry-carve-out workflow
(T-K05) plumbs the same recipe against the live model on PR diffs.
"""

from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class CaseScore:
    case_id: str
    score: float
    pass_threshold: float
    passed: bool
    breakdown: dict[str, float]


def grade_case(*, predicted: dict[str, Any], case: dict[str, Any]) -> CaseScore:
    """Score a single case: weighted match of fields between *predicted* and ``case['expected']``."""
    expected = case["expected"]
    weights = case["grading"]["weights"]
    pass_threshold = float(case["grading"]["pass_threshold"])

    breakdown: dict[str, float] = {}
    for field, weight in weights.items():
        if field == "prefix_required":
            text = str(predicted.get("text") or predicted.get("prompt") or "")
            ok = text.startswith(expected[field])
        else:
            ok = predicted.get(field) == expected[field]
        breakdown[field] = float(weight) if ok else 0.0
    score = sum(breakdown.values())
    return CaseScore(
        case_id=str(case["case_id"]),
        score=score,
        pass_threshold=pass_threshold,
        passed=score >= pass_threshold,
        breakdown=breakdown,
    )


def grade_dataset(
    *,
    predictions: dict[str, dict[str, Any]],
    cases: Iterable[dict[str, Any]],
) -> tuple[float, list[CaseScore]]:
    """Return ``(pass_rate, per_case_scores)`` for a complete prediction set."""
    scored: list[CaseScore] = []
    for case in cases:
        case_id = str(case["case_id"])
        predicted = predictions.get(case_id, {})
        scored.append(grade_case(predicted=predicted, case=case))
    if not scored:
        return 0.0, []
    pass_rate = sum(1 for s in scored if s.passed) / len(scored)
    return pass_rate, scored


def load_cases(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def predict_perfect(case: dict[str, Any]) -> dict[str, Any]:
    """Reference predictor — copies expected fields and prepends the prefix to the case prompt.

    Used by the offline test-suite; the staging variant swaps this out for the live LLM call.
    """
    expected = case["expected"]
    return {
        "hazard_class": expected["hazard_class"],
        "jurisdiction": expected["jurisdiction"],
        "severity": expected["severity"],
        "action": expected["action"],
        "text": case["prompt"],  # already begins with [SIMULATION]
    }


__all__ = [
    "CaseScore",
    "grade_case",
    "grade_dataset",
    "load_cases",
    "predict_perfect",
]
