"""Tests for drift detection workflow YAML validation.

Validates that .github/workflows/drift-detection.yml has the correct
schedule, permissions, matrix strategy, and issue creation logic.

Covers: T039 (syntax validation), T040 (job structure)
"""

from __future__ import annotations

# ── T039: Drift detection workflow syntax ────────────────────────────────────


class TestDriftWorkflowSyntax:
    """Validate drift-detection workflow YAML structure."""

    def test_drift_workflow_file_exists(self, drift_workflow_path):
        assert drift_workflow_path.exists(), f"Drift detection workflow not found at {drift_workflow_path}"

    def test_drift_workflow_name(self, drift_workflow):
        assert drift_workflow["name"] == "drift-detection", (
            f"Workflow name must be 'drift-detection', got '{drift_workflow['name']}'"
        )

    def test_drift_workflow_schedule_cron(self, drift_workflow):
        trigger = drift_workflow["on"]
        assert "schedule" in trigger, "Drift workflow must have schedule trigger"
        schedules = trigger["schedule"]
        assert isinstance(schedules, list), "schedule must be a list"
        crons = [s["cron"] for s in schedules]
        assert "0 16 * * 6" in crons, f"Schedule must include '0 16 * * 6' (Sat 16:00 UTC), got {crons}"

    def test_drift_workflow_dispatch_trigger(self, drift_workflow):
        trigger = drift_workflow["on"]
        assert "workflow_dispatch" in trigger, "Drift workflow must have workflow_dispatch trigger for manual runs"

    def test_drift_workflow_uses_environment_credentials(self, drift_workflow, drift_workflow_path):
        perms = drift_workflow.get("permissions", {})
        assert "id-token" not in perms, "drift workflow must not require retired Azure OIDC permissions"
        content = drift_workflow_path.read_text(encoding="utf-8")
        assert "secrets.AZURE_CREDENTIALS" in content

    def test_drift_workflow_permissions_contents(self, drift_workflow):
        perms = drift_workflow.get("permissions", {})
        assert perms.get("contents") == "read", "contents permission must be 'read'"

    def test_drift_workflow_permissions_issues(self, drift_workflow):
        perms = drift_workflow.get("permissions", {})
        assert perms.get("issues") == "write", "issues permission must be 'write'"


# ── T040: Drift detection job structure ──────────────────────────────────────


class TestDriftDetectionJobStructure:
    """Validate detect-drift job structure and matrix strategy."""

    def test_detect_drift_job_exists(self, drift_workflow):
        assert "detect-drift" in drift_workflow["jobs"], "detect-drift job must exist in drift-detection workflow"

    def test_detect_drift_runs_on_ubuntu(self, drift_workflow):
        job = drift_workflow["jobs"]["detect-drift"]
        assert job.get("runs-on") == "ubuntu-latest", (
            f"detect-drift must run on ubuntu-latest, got '{job.get('runs-on')}'"
        )

    def test_detect_drift_matrix_strategy(self, drift_workflow):
        job = drift_workflow["jobs"]["detect-drift"]
        strategy = job.get("strategy", {})
        matrix = strategy.get("matrix", {})
        environments = matrix.get("environment", [])
        assert "staging" in environments, "Matrix must include 'staging'"
        assert "production" in environments, "Matrix must include 'production'"

    def test_detect_drift_has_timeout(self, drift_workflow):
        job = drift_workflow["jobs"]["detect-drift"]
        timeout = job.get("timeout-minutes")
        assert timeout is not None, "detect-drift must have a timeout"

    def test_detect_drift_has_checkout_step(self, drift_workflow):
        job = drift_workflow["jobs"]["detect-drift"]
        step_names = [s.get("name", "") for s in job.get("steps", [])]
        step_uses = [s.get("uses", "") for s in job.get("steps", [])]
        assert any("checkout" in u for u in step_uses) or any("checkout" in n.lower() for n in step_names), (
            "detect-drift must include a checkout step"
        )

    def test_detect_drift_has_azure_login(self, drift_workflow):
        job = drift_workflow["jobs"]["detect-drift"]
        step_uses = [s.get("uses", "") for s in job.get("steps", [])]
        assert any("azure/login" in u for u in step_uses), "detect-drift must include Azure login step"

    def test_detect_drift_what_if_step_references_matrix(self, drift_workflow):
        """Verify what-if step uses matrix.environment for resource group and params."""
        job = drift_workflow["jobs"]["detect-drift"]
        steps = job.get("steps", [])
        what_if_steps = [s for s in steps if "what-if" in s.get("name", "").lower() or "what-if" in s.get("id", "")]
        assert len(what_if_steps) > 0, "Must have a What-If analysis step"

        what_if_run = what_if_steps[0].get("run", "")
        assert "matrix.environment" in what_if_run, "What-If step must reference matrix.environment"

    def test_detect_drift_issue_creation_conditional(self, drift_workflow):
        """Verify issue creation is conditional on drift being detected."""
        job = drift_workflow["jobs"]["detect-drift"]
        steps = job.get("steps", [])
        issue_steps = [
            s for s in steps if "issue" in s.get("name", "").lower() and "create" in s.get("name", "").lower()
        ]
        assert len(issue_steps) > 0, "Must have GitHub Issue creation step"

        issue_step = issue_steps[0]
        condition = issue_step.get("if", "")
        assert "drift" in condition.lower(), "Issue creation must be conditional on drift detection"

    def test_detect_drift_uses_infrastructure_drift_label(self, drift_workflow):
        """Verify issues are created with the infrastructure-drift label."""
        job = drift_workflow["jobs"]["detect-drift"]
        steps = job.get("steps", [])
        issue_steps = [
            s for s in steps if "issue" in s.get("name", "").lower() and "create" in s.get("name", "").lower()
        ]
        assert len(issue_steps) > 0, "Must have issue creation step"
        run_content = issue_steps[0].get("run", "")
        assert "infrastructure-drift" in run_content, "Issue must use 'infrastructure-drift' label"

    def test_drift_parser_fails_closed_on_invalid_what_if_output(self, drift_workflow_path):
        content = drift_workflow_path.read_text(encoding="utf-8")
        assert 'type == "object" and (.changes | type == "array")' in content
        assert "refusing to report clean drift status" in content
        assert '|| echo "[]"' not in content
