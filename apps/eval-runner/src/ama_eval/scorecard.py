"""Scorecard builder — aggregates per-case eval results into a Scorecard.

Computes per-metric mean, pass-rate, regression delta vs baseline, and
per-model winner. Pure function, no I/O.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime

from ama_eval_core.models import EvaluationRun, MetricResult, Scorecard, ScorecardWinner

from .evaluators.base import EvalResult


def build_scorecard(
    *,
    run: EvaluationRun,
    matrix: dict[str, dict[str, list[EvalResult]]],
    baseline_per_metric: dict[str, dict[str, float]] | None = None,
) -> Scorecard:
    """matrix: { modelKey -> { caseId -> [EvalResult, ...] } }"""

    per_model: dict[str, dict[str, MetricResult]] = {}
    metric_means: dict[str, dict[str, float]] = defaultdict(dict)
    pass_rates: dict[str, dict[str, float]] = defaultdict(dict)

    for model_key, by_case in matrix.items():
        # Aggregate per metric across all cases for this model
        per_metric_scores: dict[str, list[EvalResult]] = defaultdict(list)
        for case_id, results in by_case.items():
            for r in results:
                per_metric_scores[r.metric_id].append(r)

        per_model[model_key] = {}
        for metric_id, results in per_metric_scores.items():
            scores = [r.score for r in results]
            mean = sum(scores) / max(len(scores), 1)
            pass_count = sum(1 for r in results if r.pass_)
            pass_rate = pass_count / max(len(results), 1)

            regression = None
            if baseline_per_metric and metric_id in baseline_per_metric.get(model_key, {}):
                regression = mean - baseline_per_metric[model_key][metric_id]

            per_model[model_key][metric_id] = MetricResult(
                mean=round(mean, 4),
                **{"pass": pass_rate >= 0.95},
                regression=regression,
                distribution={
                    "count": len(scores),
                    "pass_rate": round(pass_rate, 4),
                    "min": round(min(scores), 4) if scores else 0,
                    "max": round(max(scores), 4) if scores else 0,
                },
            )
            metric_means[metric_id][model_key] = mean
            pass_rates[metric_id][model_key] = pass_rate

    # Compute winners
    winner_by_metric: dict[str, str] = {}
    for metric_id, scores_by_model in metric_means.items():
        if not scores_by_model:
            continue
        best = max(scores_by_model.items(), key=lambda kv: kv[1])
        winner_by_metric[metric_id] = best[0]

    # Overall winner = model with most metric wins
    overall_counts: dict[str, int] = defaultdict(int)
    for w in winner_by_metric.values():
        overall_counts[w] += 1
    overall = max(overall_counts.items(), key=lambda kv: kv[1])[0] if overall_counts else None

    return Scorecard(
        runId=run.runId,
        datasetVersion=run.datasetVersion,
        metricSetVersion=run.metricSetVersion,
        perModel=per_model,
        winner=ScorecardWinner(byMetric=winner_by_metric, overall=overall),
        regressionDiagnostics=[],
        secondaryJudgeDisagreements=[],
        createdAt=datetime.now(UTC),
        baselineRunId=run.baselineRunId,
    )


__all__ = ["build_scorecard"]
