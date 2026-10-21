from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
for _path in (
    _REPO_ROOT,
    _REPO_ROOT / "apps" / "eval-runner" / "src",
    _REPO_ROOT / "packages" / "eval-core" / "src",
):
    sys.path.insert(0, str(_path))

from ama_eval.evaluators import retrieval as _retrieval  # noqa: E402,F401
from ama_eval.evaluators.base import EvalInput, EvalResult, ModelOutput, get  # noqa: E402


def _groundedness(retrieved_context: list[dict[str, object]], output: str) -> EvalResult:
    evaluator = get("groundedness")
    assert evaluator is not None
    return evaluator.evaluate(
        EvalInput(
            case_id="case-retrieval",
            case_inputs={},
            expected_behaviour={},
            sensitivity_labels=[],
            hazard_tags=[],
            severity="medium",
            language="en-AU",
            retrieval_scope=True,
            retrieved_context=retrieved_context,
        ),
        ModelOutput(
            text=output,
            finish_reason="stop",
            safety_filter_triggered=False,
            latency_ms=100,
            prompt_tokens=10,
            completion_tokens=20,
        ),
    )


def test_groundedness_measures_relevant_context_coverage_only() -> None:
    result = _groundedness(
        [
            {
                "content": "Always call 000 first. Evacuate if directed by authorities.",
                "relevanceLabel": "relevant",
            },
            {
                "content": "Unrelated road maintenance information for a different region.",
                "relevanceLabel": "irrelevant",
            },
        ],
        "Always call 000 first. Evacuate if directed by authorities. Stay calm and follow instructions.",
    )

    assert result.pass_
    assert result.score == 1.0
    assert result.evidence["supportedSourceCount"] == 1
    assert result.evidence["relevantSourceCount"] == 1


def test_groundedness_fails_when_relevant_context_is_not_reflected() -> None:
    result = _groundedness(
        [{"content": "Call 000 and evacuate as directed.", "relevanceLabel": "relevant"}],
        "Stay calm and look after your family.",
    )

    assert not result.pass_
    assert result.score < 0.4
