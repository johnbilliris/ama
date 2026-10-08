"""Unit tests for provisioner, reconciler, cost, and gate."""

from __future__ import annotations

import importlib.util
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

_REPO_ROOT = Path(__file__).resolve().parents[3]
for p in (_REPO_ROOT, _REPO_ROOT / "apps" / "eval-runner" / "src", _REPO_ROOT / "packages" / "eval-core" / "src"):
    sys.path.insert(0, str(p))

import pytest  # noqa: E402
from ama_eval.cost import aggregate_run_cost, compute_cost  # noqa: E402
from ama_eval.gate import GateThresholds, evaluate_gate  # noqa: E402
from ama_eval.provisioner import (  # noqa: E402
    ProvisionContext,
    deprovision_models,
    provision_models,
)
from ama_eval.reconciler import ReconcileContext, reconcile  # noqa: E402
from ama_eval_core.models import (  # noqa: E402
    EvaluationRun,
    ModelUnderTest,
    ProvisioningPolicy,
)


def _policy() -> ProvisioningPolicy:
    return ProvisioningPolicy(
        policyVersion="1.0.0",
        env="dev",
        allowedRegions=["australiaeast", "eastus2"],
        allowedSkus=["Standard", "GlobalStandard"],
        maxConcurrentDeployments=4,
        maxRunCostAud=250.0,
        maxRunDurationMinutes=480,
        prFastSubsetMaxMinutes=30,
        secondaryJudgeSamplingRate=0.05,
        evaluatorRoles={"viewer": "Eval.Viewer"},
    )


def _run(*models) -> EvaluationRun:
    return EvaluationRun(
        runId="01HXTESTRUN0000000000ABCD",
        status="queued",
        mode="ad-hoc",
        datasetId="d",
        datasetVersion="1.0.0",
        models=[ModelUnderTest(modelId=m, version="v") for m in models],
        metricSetVersion="1.0.0",
        policyVersion="1.0.0",
        createdAt=datetime.now(UTC),
        createdBy="t",
    )


def test_acr_build_contexts_include_every_required_source_directory() -> None:
    script_path = _REPO_ROOT / "scripts" / "run_llm_evaluation.py"
    spec = importlib.util.spec_from_file_location("run_llm_evaluation", script_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    assert Path("apps/console_logging.py") in module.EVAL_RUNNER_BUILD_CONTEXT_PATHS
    assert {
        Path("scripts/install_pyproject_dependencies.py"),
        Path("apps/console_logging.py"),
        Path("apps/agents"),
        Path("apps/ingestion"),
        Path("docs/risk-register"),
        Path("docs/governance-hub/adoption-roadmap"),
        Path("docs/governance-hub/executive-kpi"),
        Path("docs/governance-hub/rai-register"),
        Path("specs/shared"),
    } <= set(module.API_BUILD_CONTEXT_PATHS)
    assert all(
        (module.REPO_ROOT / path).exists()
        for path in [*module.EVAL_RUNNER_BUILD_CONTEXT_PATHS, *module.API_BUILD_CONTEXT_PATHS]
    )


def test_pr_fast_execute_posts_bounded_correlated_run_and_gates_scorecard(monkeypatch, tmp_path) -> None:
    script_path = _REPO_ROOT / "scripts" / "run_llm_evaluation.py"
    spec = importlib.util.spec_from_file_location("run_llm_evaluation_pr_gate", script_path)
    assert spec is not None and spec.loader is not None
    script = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = script
    spec.loader.exec_module(script)

    ctx = script.RunContext(
        env=script.replace(script.ENVIRONMENTS["dev"], api_base_url="https://api.dev.local"),
        args=SimpleNamespace(
            api_base_url="https://api.dev.local",
            change_ref="PR-142",
            continue_on_gate_block=False,
            dry_run=False,
            max_cases=2,
            metric_set="disaster-core-v1",
            min_evaluated_samples=2,
            mode="pr-fast-subset",
            models="gpt-5.4-mini:2026-03-17",
            output_dir=str(tmp_path),
            poll_seconds=0,
            timeout_minutes=1,
        ),
    )
    request_bodies: list[dict] = []
    passing_metrics = {
        metric: {"mean": 0.5, "distribution": {"count": 2, "pass_rate": rate}}
        for metric, rate in (
            ("refusal-correctness", 0.97),
            ("refer-to-authority", 0.99),
            ("must-include", 0.93),
            ("must-not-include", 1.0),
            ("prompt-injection-resistance", 0.96),
            ("groundedness", 0.88),
        )
    }

    def fake_get(url, **_kwargs):
        if url.endswith("/api/eval/health"):
            return SimpleNamespace(status_code=200, json=lambda: {"anonymousAccess": True})
        if url.endswith("/api/eval/runs/r1"):
            return SimpleNamespace(status_code=200, json=lambda: {"runId": "r1", "status": "succeeded"})
        if url.endswith("/api/eval/runs/r1/scorecard"):
            return SimpleNamespace(
                status_code=200,
                json=lambda: {"runId": "r1", "perModel": {"gpt-5.4-mini@2026-03-17": passing_metrics}},
            )
        raise AssertionError(f"unexpected eval GET: {url}")

    def fake_post(url, *, json, **_kwargs):
        request_bodies.append(json)
        return SimpleNamespace(status_code=201, json=lambda: {"runId": "r1", "status": "queued"})

    monkeypatch.setattr(script.requests, "get", fake_get)
    monkeypatch.setattr(script.requests, "post", fake_post)
    monkeypatch.setattr(script, "_resolve_api_base_url", lambda *_args, **_kwargs: None)

    script.stage_execute(ctx)

    assert request_bodies == [
        {
            "datasetId": "disaster-response-core",
            "datasetVersion": "1.1.3",
            "models": [
                {
                    "modelId": "gpt-5.4-mini",
                    "version": "2026-03-17",
                    "deploymentRegion": "australiaeast",
                    "sku": "GlobalStandard",
                }
            ],
            "metricSetVersion": "disaster-core-v1",
            "policyVersion": "1.0.0",
            "mode": "pr-fast-subset",
            "estimatedCostAud": 0.0,
            "estimatedDurationMinutes": 30,
            "changeRef": "PR-142",
            "datasetSubset": {"maxCases": 2},
        }
    ]
    assert ctx.state["run_id"] == "r1"
    assert ctx.state["evaluation_status"] == "succeeded"
    assert ctx.state["gate_passed"] is True
    assert ctx.state["evaluated_samples"] == 2


def test_provision_two_models():
    audit = []
    ctx = ProvisionContext(
        run=_run("gpt-4o", "phi-3"),
        policy=_policy(),
        az_run=lambda args: {},
        audit_emit=lambda **kw: audit.append(kw),
    )
    deps = provision_models(ctx)
    assert len(deps) == 2
    assert all(d.region == "australiaeast" for d in deps)
    assert sum(1 for e in audit if e["action"] == "infra.provisioned") == 2


def test_provision_rejects_too_many_models():
    pol = _policy().model_copy(update={"maxConcurrentDeployments": 1})
    ctx = ProvisionContext(run=_run("a", "b"), policy=pol)
    with pytest.raises(ValueError, match="maxConcurrent"):
        provision_models(ctx)


def test_deprovision_calls_az():
    calls = []
    ctx = ProvisionContext(
        run=_run("gpt-4o"),
        policy=_policy(),
        az_run=lambda args: calls.append(args) or {},
    )
    deps = provision_models(ctx)
    deprovision_models(ctx, deps)
    assert any("delete" in tuple(c) for c in calls)


def test_reconcile_cleans_orphans():
    cleaned = []
    deployments = [
        {
            "id": "/sub/a",
            "name": "eval-old-1",
            "createdAt": (datetime.now(UTC) - timedelta(hours=2)).isoformat(),
            "tags": {"eval-runId": "run-done"},
        },
        {
            "id": "/sub/b",
            "name": "eval-fresh",
            "createdAt": datetime.now(UTC).isoformat(),
            "tags": {"eval-runId": "run-active"},
        },
        {"id": "/sub/c", "name": "unrelated", "tags": {}},
    ]
    ctx = ReconcileContext(
        list_deployments=lambda: deployments,
        delete_deployment=lambda name: cleaned.append(name),
        is_run_terminal=lambda rid: rid == "run-done",
        grace_minutes=30,
    )
    n = reconcile(ctx)
    assert n == 1
    assert cleaned == ["eval-old-1"]


def test_compute_cost_gpt_4o():
    e = compute_cost("r1", "gpt-4o", prompt_tokens=10000, completion_tokens=5000)
    assert e.totalCostAud == round(0.075 + 0.1125, 6)


def test_aggregate_run_cost():
    entries = [
        compute_cost("r1", "gpt-4o", 1000, 1000),
        compute_cost("r1", "phi-3", 1000, 1000),
    ]
    assert aggregate_run_cost(entries) > 0


def test_gate_pass_when_thresholds_met():
    def metric(pass_rate: float) -> dict:
        return {
            "mean": 0.5,
            "distribution": {"count": 12, "pass_rate": pass_rate},
        }

    sc = {
        "runId": "r1",
        "perModel": {
            "gpt-4o@v1": {
                "refusal-correctness": metric(0.97),
                "refer-to-authority": metric(0.99),
                "must-include": metric(0.93),
                "must-not-include": metric(1.0),
                "prompt-injection-resistance": metric(0.96),
                "groundedness": metric(0.88),
            }
        },
    }
    v = evaluate_gate(sc, baseline=None)
    assert v.pass_, v.reasons
    assert v.reasons == []
    assert v.evaluatedSamples == 12


def test_gate_fails_on_must_not_include_regression():
    sc = {
        "runId": "r1",
        "perModel": {
            "phi-3@v1": {
                "refusal-correctness": {"mean": 0.96},
                "refer-to-authority": {"mean": 0.99},
                "must-include": {"mean": 0.92},
                "must-not-include": {"mean": 0.85, "passRate": 0.85},
                "prompt-injection-resistance": {"mean": 0.96},
                "groundedness": {"mean": 0.88},
            }
        },
    }
    v = evaluate_gate(sc, baseline=None)
    assert not v.pass_
    assert any("must-not-include" in r for r in v.reasons)


def test_gate_fails_when_required_metric_is_missing():
    sc = {
        "runId": "r1",
        "perModel": {
            "phi-3@v1": {
                "refusal-correctness": {"mean": 0.96},
                "refer-to-authority": {"mean": 0.99},
                "must-include": {"mean": 0.92},
                "must-not-include": {"mean": 1.0},
                "prompt-injection-resistance": {"mean": 0.96},
            }
        },
    }

    verdict = evaluate_gate(sc, baseline=None)

    assert not verdict.pass_
    assert any("missing required metric groundedness" in reason for reason in verdict.reasons)


def test_gate_fails_on_regression_vs_baseline():
    def metric(pass_rate: float) -> dict:
        return {
            "mean": 0.5,
            "distribution": {"count": 12, "pass_rate": pass_rate},
        }

    sc = {
        "runId": "r1",
        "perModel": {
            "gpt-4o@v1": {
                "refusal-correctness": metric(0.96),
                "refer-to-authority": metric(0.99),
                "must-include": metric(0.92),
                "must-not-include": metric(1.0),
                "prompt-injection-resistance": metric(0.96),
                "groundedness": metric(0.70),
            }
        },
    }
    baseline = {"runId": "baseline-run", "metrics": {"groundedness": {"mean": 0.90}}}
    v = evaluate_gate(sc, baseline=baseline, thresholds=GateThresholds(groundednessMin=0.5))
    assert not v.pass_
    assert any("regression on groundedness" in r for r in v.reasons)


def test_gate_fails_when_sample_floor_is_not_met():
    metrics = {
        metric: {"mean": 1.0, "distribution": {"count": 2, "pass_rate": 1.0}}
        for metric in (
            "refusal-correctness",
            "refer-to-authority",
            "must-include",
            "must-not-include",
            "prompt-injection-resistance",
            "groundedness",
        )
    }

    verdict = evaluate_gate(
        {"runId": "r1", "perModel": {"gpt-5.4-mini@2026-03-17": metrics}},
        baseline=None,
        thresholds=GateThresholds(minEvaluatedSamples=3),
    )

    assert not verdict.pass_
    assert verdict.evaluatedSamples == 2
    assert any("evaluated samples 2 < required minimum 3" in reason for reason in verdict.reasons)
