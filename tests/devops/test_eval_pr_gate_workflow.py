"""Tests for eval PR gate workflow triggers and fail-closed quality semantics."""

from __future__ import annotations


def test_eval_gate_workflow_file_exists(eval_pr_gate_workflow_path):
    assert eval_pr_gate_workflow_path.exists(), f"Workflow not found at {eval_pr_gate_workflow_path}"


def test_eval_gate_has_required_triggers(eval_pr_gate_workflow):
    trigger = eval_pr_gate_workflow["on"]
    assert "workflow_dispatch" in trigger
    assert "pull_request" in trigger
    assert "workflow_call" in trigger


def test_eval_gate_workflow_call_exposes_explicit_inputs_outputs(eval_pr_gate_workflow):
    call = eval_pr_gate_workflow["on"]["workflow_call"]
    inputs = call.get("inputs", {})
    outputs = call.get("outputs", {})

    for required_input in [
        "evaluation_mode",
        "evaluation_region",
        "min_evaluated_samples",
        "max_cases",
    ]:
        assert required_input in inputs, f"workflow_call input missing: {required_input}"

    for required_output in [
        "evaluation_status",
        "gate_passed",
        "evaluated_samples",
        "run_id",
    ]:
        assert required_output in outputs, f"workflow_call output missing: {required_output}"


def test_eval_gate_threshold_defaults_are_fail_closed(eval_pr_gate_workflow):
    call = eval_pr_gate_workflow["on"]["workflow_call"]
    inputs = call["inputs"]
    assert "default" not in inputs["min_evaluated_samples"]
    assert inputs["max_cases"]["default"] == 200
    evaluation_step = next(
        step for step in eval_pr_gate_workflow["jobs"]["eval-gate"]["steps"] if step.get("id") == "evaluation"
    )
    assert "inputs.max_cases" in evaluation_step["env"]["MIN_EVALUATED_SAMPLES"]


def test_eval_gate_enforces_non_zero_collection_and_required_metrics(eval_pr_gate_workflow_path):
    text = eval_pr_gate_workflow_path.read_text(encoding="utf-8")
    gate_path = eval_pr_gate_workflow_path.parents[2] / "apps" / "eval-runner" / "src" / "ama_eval" / "gate.py"
    gate_text = gate_path.read_text(encoding="utf-8")
    assert "Run correlated PR evaluation and scorecard gate" in text
    assert "evaluated samples" in gate_text
    assert "missing required metric" in gate_text


def test_eval_gate_defaults_to_documented_dev_platform(eval_pr_gate_workflow_path):
    text = eval_pr_gate_workflow_path.read_text(encoding="utf-8")
    assert "vars.EVAL_RUNNER_JOB_NAME || 'caj-eval-runner-dev'" in text
    assert "vars.EVAL_RG || 'rg-ama-eval-dev'" in text
    assert "EVAL_RUNNER_JOB_NAME and EVAL_RG must be configured" in text
    assert "az containerapp job show" in text
    assert "Skipping Container Apps eval runner" not in text


def test_eval_gate_uses_correlated_run_and_scorecard(eval_pr_gate_workflow_path):
    text = eval_pr_gate_workflow_path.read_text(encoding="utf-8")
    assert "--stage execute" in text
    assert "--change-ref" in text
    assert "EVAL_GATE_SUMMARY_JSON" not in text
    assert "az containerapp job execution list" not in text


def test_eval_gate_tests_the_versioned_dataset_generator(eval_pr_gate_workflow_path):
    text = eval_pr_gate_workflow_path.read_text(encoding="utf-8")
    assert "pip install -e packages/eval-dataset" in text
    assert "packages/eval-dataset/tests/" in text
