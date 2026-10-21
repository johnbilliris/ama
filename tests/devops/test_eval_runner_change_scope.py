"""Regression coverage for eval runner change scope passed from CI to CD."""

from __future__ import annotations

import yaml


def test_ci_records_the_full_push_scope(ci_workflow_path):
    workflow = yaml.safe_load(ci_workflow_path.read_text(encoding="utf-8"))
    job = workflow["jobs"]["eval-runner-changes"]
    assert job["if"] == "github.event_name == 'push' && github.ref_name != 'main'"
    checkout, detect, publish = job["steps"]
    assert checkout["with"]["fetch-depth"] == 0
    assert detect["env"]["BEFORE_SHA"] == "${{ github.event.before }}"
    assert detect["env"]["HEAD_SHA"] == "${{ github.sha }}"
    assert 'git diff --quiet "$BEFORE_SHA" "$HEAD_SHA" -- apps/eval-runner/' in detect["run"]
    assert "git hash-object -t tree /dev/null" in detect["run"]
    assert 'exit "$status"' in detect["run"]
    assert publish["with"]["name"] == "eval-runner-changes"
    assert publish["with"]["if-no-files-found"] == "error"


def test_cd_reads_scope_from_the_exact_ci_run(cd_workflow):
    deploy = cd_workflow["jobs"]["deploy"]
    detect = next(step for step in deploy["steps"] if step.get("id") == "eval-changes")
    assert detect["env"]["CI_RUN_ID"] == "${{ github.event.workflow_run.id }}"
    assert detect["env"]["HEAD_SHA"] == "${{ github.event.workflow_run.head_sha }}"
    assert 'gh run download "$CI_RUN_ID" --name eval-runner-changes' in detect["run"]
    assert '.head_sha == $head_sha and (.changed | type == "boolean")' in detect["run"]
    assert deploy["outputs"]["eval_runner_changed"] == "${{ steps.eval-changes.outputs.changed }}"


def test_cd_skips_eval_without_eval_runner_changes(cd_workflow):
    gate = cd_workflow["jobs"]["quality-gate"]
    assert gate["needs"] == ["deploy"]
    assert "needs.deploy.result == 'success'" in gate["if"]
    assert "needs.deploy.outputs.eval_runner_changed == 'true'" in gate["if"]
    rollback = cd_workflow["jobs"]["rollback"]
    assert "needs.quality-gate.result == 'failure'" in rollback["if"]
    assert "needs.quality-gate.result == 'skipped'" not in rollback["if"]
