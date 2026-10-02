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
        "min_evaluated_samples",
        "max_hallucination_rate",
        "max_false_positive_rate",
        "fail_on_missing_metrics",
        "evaluation_summary_json",
    ]:
        assert required_input in inputs, f"workflow_call input missing: {required_input}"

    for required_output in [
        "evaluation_status",
        "gate_passed",
        "evaluated_samples",
        "hallucination_rate",
        "false_positive_rate",
    ]:
        assert required_output in outputs, f"workflow_call output missing: {required_output}"


def test_eval_gate_threshold_defaults_are_fail_closed(eval_pr_gate_workflow):
    call = eval_pr_gate_workflow["on"]["workflow_call"]
    inputs = call["inputs"]
    assert inputs["min_evaluated_samples"]["default"] == 1
    assert inputs["max_hallucination_rate"]["default"] == 0.02
    assert inputs["max_false_positive_rate"]["default"] == 0.05
    assert inputs["fail_on_missing_metrics"]["default"] is True


def test_eval_gate_enforces_non_zero_collection_and_required_metrics(eval_pr_gate_workflow_path):
    text = eval_pr_gate_workflow_path.read_text(encoding="utf-8")
    assert "No evaluation samples collected at required floor" in text
    assert "Missing required metrics" in text
    assert "Missing evaluation summary JSON" in text


def test_eval_gate_blocks_when_runner_not_configured(eval_pr_gate_workflow_path):
    text = eval_pr_gate_workflow_path.read_text(encoding="utf-8")
    assert "EVAL_RUNNER_JOB_NAME and EVAL_RG must be configured" in text
    assert "Skipping Container Apps eval runner" not in text


def test_eval_gate_binds_thresholds_for_hallucination_and_false_positive(eval_pr_gate_workflow_path):
    text = eval_pr_gate_workflow_path.read_text(encoding="utf-8")
    assert "Hallucination rate breach" in text
    assert "False-positive rate breach" in text
