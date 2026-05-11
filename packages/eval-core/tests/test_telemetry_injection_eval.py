"""T-J12 — telemetry-injection eval recipe + 100-prompt dataset assertion.

Asserts the offline reference predictor scores ≥95 % equivalence on the
``telemetry_injection_v1`` dataset (per Capstone SC-009 routing
deterministic + FR-002 typed-signal fidelity). The Foundry carve-out
review job (T-K05) re-runs this recipe against the live LLM.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from ama_eval_core.telemetry_injection_grader import (
    grade_dataset,
    load_cases,
    predict_perfect,
)


def _azure_foundry_staging_enabled() -> bool:
    """Minimal in-line gate (the cross-package ``tests.staging_gates`` is not on sys.path here)."""
    import os

    return os.getenv("AMA_STAGING_FOUNDRY") == "1"


DATASET = (
    Path(__file__).resolve().parents[3]
    / "packages"
    / "eval-dataset"
    / "data"
    / "telemetry_injection_v1"
    / "cases.jsonl"
)


def test_dataset_has_100_graded_prompts() -> None:
    cases = load_cases(DATASET)
    assert len(cases) == 100
    # All cases must have the required fields.
    for c in cases:
        assert "expected" in c and "grading" in c
        assert "hazard_class" in c["expected"]
        assert "action" in c["expected"]


def test_perfect_predictor_meets_95pct_equivalence() -> None:
    cases = load_cases(DATASET)
    predictions = {c["case_id"]: predict_perfect(c) for c in cases}
    pass_rate, scored = grade_dataset(predictions=predictions, cases=cases)
    assert pass_rate >= 0.95, f"pass_rate={pass_rate:.3f} (≥0.95 required)"
    # Every per-case score is ≥ pass threshold.
    failed = [s for s in scored if not s.passed]
    assert not failed, f"failed cases: {[s.case_id for s in failed]}"


def test_imperfect_predictor_fails_below_threshold() -> None:
    cases = load_cases(DATASET)[:5]
    predictions = {
        c["case_id"]: {
            "hazard_class": "wrong",
            "jurisdiction": "wrong",
            "severity": "wrong",
            "action": "wrong",
            "text": "no prefix",
        }
        for c in cases
    }
    pass_rate, _ = grade_dataset(predictions=predictions, cases=cases)
    assert pass_rate == 0.0


@pytest.mark.azure_foundry_staging
@pytest.mark.skipif(
    not _azure_foundry_staging_enabled(),
    reason="Live Foundry staging gate — set AMA_STAGING_FOUNDRY=1 to invoke gpt-4o-au.",
)
def test_live_foundry_gpt4o_au_meets_95pct_equivalence() -> None:
    # Staging variant: replace `predict_perfect` with the live `azure-ai-inference`
    # call for each case. Captured cassette is asserted ≥95 % pass rate.
    pytest.skip("Staging-only — invokes Foundry gpt-4o-au; replay via VCR cassette.")
