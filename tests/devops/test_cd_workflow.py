"""Tests for CD workflow YAML syntax and structure validation.

Validates that .github/workflows/cd.yml is well-formed YAML with
the correct trigger, permissions, and top-level structure.

Covers: T012 (workflow syntax), T013 (job structure)
"""

from __future__ import annotations

import yaml

# ── T012: Workflow syntax validation ─────────────────────────────────────────


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
        assert cd_workflow["name"] == "cd", (
            f"Workflow name must be 'cd', got '{cd_workflow['name']}'"
        )

    def test_cd_workflow_trigger_is_workflow_run(self, cd_workflow):
        trigger = cd_workflow["on"]
        assert "workflow_run" in trigger, "CD workflow must use workflow_run trigger"

    def test_cd_workflow_trigger_references_ci(self, cd_workflow):
        wr = cd_workflow["on"]["workflow_run"]
        workflows = wr.get("workflows", [])
        assert "ci" in workflows, (
            f"workflow_run must reference 'ci' workflow, got {workflows}"
        )

    def test_cd_workflow_trigger_completed_type(self, cd_workflow):
        wr = cd_workflow["on"]["workflow_run"]
        types = wr.get("types", [])
        assert "completed" in types, (
            f"workflow_run must include 'completed' type, got {types}"
        )

    def test_cd_workflow_trigger_main_branch(self, cd_workflow):
        wr = cd_workflow["on"]["workflow_run"]
        branches = wr.get("branches", [])
        assert "main" in branches, (
            f"workflow_run must filter to 'main' branch, got {branches}"
        )

    def test_cd_workflow_permissions_oidc(self, cd_workflow):
        perms = cd_workflow.get("permissions", {})
        assert perms.get("id-token") == "write", "id-token permission must be 'write'"

    def test_cd_workflow_permissions_contents(self, cd_workflow):
        perms = cd_workflow.get("permissions", {})
        assert perms.get("contents") == "read", "contents permission must be 'read'"

    def test_cd_workflow_permissions_issues(self, cd_workflow):
        perms = cd_workflow.get("permissions", {})
        assert perms.get("issues") == "write", "issues permission must be 'write'"

    def test_cd_workflow_permissions_actions(self, cd_workflow):
        perms = cd_workflow.get("permissions", {})
        assert perms.get("actions") == "read", "actions permission must be 'read'"


# ── T013: Deployment job structure ───────────────────────────────────────────


class TestDeployStagingJobStructure:
    """Validate deploy-staging job structure and configuration."""

    def test_deploy_staging_job_exists(self, cd_workflow):
        assert "deploy-staging" in cd_workflow["jobs"], (
            "deploy-staging job must exist in CD workflow"
        )

    def test_deploy_staging_environment(self, cd_workflow):
        job = cd_workflow["jobs"]["deploy-staging"]
        assert job.get("environment") == "staging", (
            f"deploy-staging must use 'staging' environment, got '{job.get('environment')}'"
        )

    def test_deploy_staging_concurrency_group(self, cd_workflow):
        job = cd_workflow["jobs"]["deploy-staging"]
        concurrency = job.get("concurrency", {})
        assert concurrency.get("group") == "deploy-staging", (
            f"Concurrency group must be 'deploy-staging', got '{concurrency.get('group')}'"
        )

    def test_deploy_staging_concurrency_no_cancel(self, cd_workflow):
        job = cd_workflow["jobs"]["deploy-staging"]
        concurrency = job.get("concurrency", {})
        assert concurrency.get("cancel-in-progress") is False, (
            "deploy-staging must not cancel in-progress deployments"
        )

    def test_deploy_staging_success_condition(self, cd_workflow):
        job = cd_workflow["jobs"]["deploy-staging"]
        condition = job.get("if", "")
        assert "workflow_run.conclusion" in condition, (
            "deploy-staging must check workflow_run.conclusion"
        )
        assert "success" in condition, (
            "deploy-staging must check for 'success' conclusion"
        )

    def test_deploy_staging_runs_on_ubuntu(self, cd_workflow):
        job = cd_workflow["jobs"]["deploy-staging"]
        assert job.get("runs-on") == "ubuntu-latest", (
            f"deploy-staging must run on ubuntu-latest, got '{job.get('runs-on')}'"
        )

    def test_deploy_staging_has_outputs(self, cd_workflow):
        job = cd_workflow["jobs"]["deploy-staging"]
        outputs = job.get("outputs", {})
        assert "deployment-status" in outputs, (
            "deploy-staging must output 'deployment-status'"
        )

    def test_deploy_staging_has_timeout(self, cd_workflow):
        job = cd_workflow["jobs"]["deploy-staging"]
        timeout = job.get("timeout-minutes")
        assert timeout is not None, "deploy-staging must have a timeout"
        assert timeout <= 30, f"deploy-staging timeout should be ≤30 min, got {timeout}"
