"""Tests for CD workflow structure and reliability gate wiring."""

from __future__ import annotations

import yaml


class TestCDWorkflowSyntax:
    """Validate CD workflow is valid YAML with required top-level keys."""

    def test_cd_workflow_file_exists(self, cd_workflow_path):
        assert cd_workflow_path.exists(), f"CD workflow not found at {cd_workflow_path}"

    def test_cd_workflow_is_valid_yaml(self, cd_workflow_path):
        content = cd_workflow_path.read_text(encoding="utf-8")
        parsed = yaml.safe_load(content)
        assert isinstance(parsed, dict), "CD workflow must parse to a YAML mapping"

    def test_cd_workflow_has_required_top_level_keys(self, cd_workflow):
        required = {"name", "on", "permissions", "jobs"}
        actual = set(cd_workflow.keys())
        missing = required - actual
        assert not missing, f"Missing top-level keys: {missing}"

    def test_cd_workflow_name_is_cd(self, cd_workflow):
        assert cd_workflow["name"] == "cd", f"Workflow name must be 'cd', got '{cd_workflow['name']}'"

    def test_cd_workflow_trigger_is_workflow_run(self, cd_workflow):
        trigger = cd_workflow["on"]
        assert "workflow_run" in trigger, "CD workflow must use workflow_run trigger"

    def test_cd_workflow_trigger_references_ci(self, cd_workflow):
        wr = cd_workflow["on"]["workflow_run"]
        workflows = wr.get("workflows", [])
        assert "ci" in workflows, f"workflow_run must reference 'ci' workflow, got {workflows}"

    def test_cd_workflow_trigger_completed_type(self, cd_workflow):
        wr = cd_workflow["on"]["workflow_run"]
        types = wr.get("types", [])
        assert "completed" in types, f"workflow_run must include 'completed' type, got {types}"

    def test_cd_workflow_trigger_branch_filters(self, cd_workflow):
        wr = cd_workflow["on"]["workflow_run"]
        branches = wr.get("branches", [])
        assert set(branches) == {"dev", "staging", "production"}, (
            f"workflow_run must filter to dev/staging/production, got {branches}"
        )

    def test_cd_workflow_permissions_contents(self, cd_workflow):
        perms = cd_workflow.get("permissions", {})
        assert perms.get("contents") == "read", "contents permission must be 'read'"

    def test_cd_workflow_permissions_issues(self, cd_workflow):
        perms = cd_workflow.get("permissions", {})
        assert perms.get("issues") == "write", "issues permission must be 'write'"

    def test_cd_workflow_permissions_actions(self, cd_workflow):
        perms = cd_workflow.get("permissions", {})
        assert perms.get("actions") == "read", "actions permission must be 'read'"


class TestCDQualityAndRollbackWiring:
    """Validate post-deploy quality gate and rollback flow semantics."""

    def test_deploy_job_exists(self, cd_workflow):
        assert "deploy" in cd_workflow["jobs"], "deploy job must exist in CD workflow"

    def test_deploy_outputs_health_and_target(self, cd_workflow):
        outputs = cd_workflow["jobs"]["deploy"].get("outputs", {})
        assert "health_passed" in outputs
        assert "target_env" in outputs
        assert "resource_group" in outputs

    def test_quality_gate_job_uses_reusable_eval_gate(self, cd_workflow):
        quality = cd_workflow["jobs"].get("quality-gate", {})
        assert quality.get("uses") == "./.github/workflows/eval-pr-gate.yml"
        assert quality.get("needs") == ["deploy"]
        with_block = quality.get("with", {})
        assert with_block.get("min_evaluated_samples") == 1
        assert with_block.get("max_hallucination_rate") == 0.02
        assert with_block.get("max_false_positive_rate") == 0.05
        assert with_block.get("fail_on_missing_metrics") is True

    def test_rollback_job_exists_and_depends_on_deploy_and_quality(self, cd_workflow):
        rollback = cd_workflow["jobs"].get("rollback", {})
        assert rollback.get("needs") == ["deploy", "quality-gate"]
        assert rollback.get("environment") == "${{ needs.deploy.outputs.target_env }}"

    def test_rollback_condition_is_health_or_quality_failure(self, cd_workflow):
        rollback = cd_workflow["jobs"]["rollback"]
        condition = rollback.get("if", "")
        assert "needs.deploy.outputs.health_passed != 'true'" in condition
        assert "needs.quality-gate.result == 'failure'" in condition
        assert "needs.deploy.outputs.target_env != 'dev'" in condition

    def test_rollback_script_failure_is_not_ignored(self, cd_workflow_path):
        content = cd_workflow_path.read_text(encoding="utf-8")
        assert "- name: Execute rollback script" in content
        assert "continue-on-error: true" not in content

    def test_cd_does_not_reintroduce_retired_progressive_delivery(self, cd_workflow_path):
        content = cd_workflow_path.read_text(encoding="utf-8").lower()
        assert "progressive-delivery" not in content

    def test_cd_does_not_purge_soft_deleted_resources(self, cd_workflow_path):
        content = cd_workflow_path.read_text(encoding="utf-8").lower()
        assert "account purge" not in content
        assert "separately approved" in content

    def test_cd_supports_local_multi_platform_azd_images(self, cd_workflow):
        steps = cd_workflow["jobs"]["deploy"]["steps"]
        docker_setup = next(step for step in steps if step.get("name") == "Set up multi-platform Docker image store")
        qemu_setup = next(step for step in steps if step.get("name") == "Set up QEMU")
        deploy = next(step for step in steps if step.get("name") == "Deploy services")

        assert docker_setup["uses"].startswith("docker/setup-docker-action@")
        daemon_config = yaml.safe_load(docker_setup["with"]["daemon-config"])
        assert daemon_config["features"]["containerd-snapshotter"] is True
        assert qemu_setup["uses"].startswith("docker/setup-qemu-action@")
        assert steps.index(docker_setup) < steps.index(qemu_setup) < steps.index(deploy)
