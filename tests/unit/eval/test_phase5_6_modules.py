"""Unit tests for provisioner, reconciler, cost, and gate."""

from __future__ import annotations

import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

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
    sc = {
        "runId": "r1",
        "perModel": {
            "gpt-4o@v1": {
                "refusal-correctness": {"mean": 0.97, "passRate": 0.97},
                "refer-to-authority": {"mean": 0.99, "passRate": 0.99},
                "must-include": {"mean": 0.93, "passRate": 0.93},
                "must-not-include": {"mean": 1.0, "passRate": 1.0},
                "prompt-injection-resistance": {"mean": 0.96, "passRate": 0.96},
                "groundedness": {"mean": 0.88, "passRate": 0.88},
            }
        },
    }
    v = evaluate_gate(sc, baseline=None)
    assert v.pass_, v.reasons
    assert v.reasons == []


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


def test_gate_fails_on_regression_vs_baseline():
    sc = {
        "runId": "r1",
        "perModel": {
            "gpt-4o@v1": {
                "refusal-correctness": {"mean": 0.96, "passRate": 0.96},
                "refer-to-authority": {"mean": 0.99, "passRate": 0.99},
                "must-include": {"mean": 0.92, "passRate": 0.92},
                "must-not-include": {"mean": 1.0, "passRate": 1.0},
                "prompt-injection-resistance": {"mean": 0.96, "passRate": 0.96},
                "groundedness": {"mean": 0.70, "passRate": 0.70},
            }
        },
    }
    baseline = {"runId": "baseline-run", "metrics": {"groundedness": {"mean": 0.90}}}
    v = evaluate_gate(sc, baseline=baseline, thresholds=GateThresholds(groundednessMin=0.5))
    assert not v.pass_
    assert any("regression on groundedness" in r for r in v.reasons)
