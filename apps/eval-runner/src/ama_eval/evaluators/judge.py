"""LLM-judge evaluator (primary + secondary)."""

from __future__ import annotations

import json
import logging
import re
from collections.abc import Callable
from dataclasses import dataclass

from .base import EvalInput, EvalResult, ModelOutput

logger = logging.getLogger(__name__)

_JUDGE_PROMPT_TEMPLATE = """You are an expert evaluator of LLM outputs for a Disaster Response Coordination assistant.

Score the model output on the metric '{metric}' on a 1-5 scale (5 = excellent, 1 = unacceptable).
Reply ONLY with JSON: {{"score": <1-5>, "rationale": "<one sentence>"}}.

INPUT:
{input}

EXPECTED BEHAVIOUR:
{expected}

MODEL OUTPUT:
{output}

METRIC: {metric}
"""

_QUALITY_METRICS = {
    "relevance": "Does the output address the user's input directly and completely?",
    "coherence": "Is the output internally consistent and well-structured?",
    "fluency": "Is the output grammatically fluent in the input language?",
    "factuality": "Are factual claims accurate (where verifiable)?",
    "tone-appropriateness": "Does the tone match the expected disaster-response register?",
}

_PASS_THRESHOLD = 4.0


@dataclass(frozen=True)
class JudgeEvaluator:
    metric_id: str
    family: str
    tier: str
    judge_fn: Callable[[str, str, str, str], dict]

    def evaluate(self, inp: EvalInput, out: ModelOutput) -> EvalResult:
        if not out.text:
            return EvalResult(metric_id=self.metric_id, score=0.0, pass_=False, rationale="empty output")
        try:
            verdict = self.judge_fn(
                self.metric_id,
                str(inp.case_inputs.get("prompt") or inp.case_inputs),
                str(inp.expected_behaviour),
                out.text,
            )
            score = float(verdict.get("score", 0))
            rationale = str(verdict.get("rationale", ""))
        except Exception as exc:
            logger.exception("judge invocation failed: %s", exc)
            return EvalResult(metric_id=self.metric_id, score=0.0, pass_=False, rationale=f"judge error: {exc}")
        return EvalResult(
            metric_id=self.metric_id,
            score=score,
            pass_=score >= _PASS_THRESHOLD,
            rationale=rationale,
            evidence={"raw": verdict},
        )


def make_foundry_judge(client, judge_model_id: str = "gpt-4o", judge_model_version: str = "2024-11-20"):
    def _judge(metric: str, inp: str, expected: str, output: str) -> dict:
        prompt = _JUDGE_PROMPT_TEMPLATE.format(metric=metric, input=inp, expected=expected, output=output)
        resp = client.complete(
            model_id=judge_model_id,
            messages=[
                {"role": "system", "content": "You are a strict, fair LLM-output judge. Reply ONLY with JSON."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.0,
            max_tokens=300,
        )
        text = resp.text or "{}"
        m = re.search(r"\{[^{}]*\"score\"[^{}]*\}", text)
        if m:
            return json.loads(m.group(0))
        return {"score": 0, "rationale": "parse-failed"}

    return _judge


def register_judge_evaluators(judge_fn) -> None:
    from . import base as _base

    for metric_id in _QUALITY_METRICS:
        family = "tone" if metric_id == "tone-appropriateness" else "quality"
        if metric_id == "factuality":
            family = "factuality"
        ev = JudgeEvaluator(metric_id=metric_id, family=family, tier="primary-judge", judge_fn=judge_fn)
        _base._REGISTRY[metric_id] = ev


__all__ = ["JudgeEvaluator", "make_foundry_judge", "register_judge_evaluators"]
