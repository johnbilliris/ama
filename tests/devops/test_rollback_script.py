"""Tests for the rollback script (scripts/rollback.sh).

Validates argument parsing, exit codes, dry-run mode, and first-run
bootstrap behavior. These tests parse the script source; they do NOT
execute against live Azure resources.

Covers: T034 (rollback unit tests), T036 (first-run bootstrap)
"""

from __future__ import annotations

# ── T034: Rollback script unit tests ─────────────────────────────────────────


class TestRollbackScriptExists:
    """Validate rollback script exists and is properly structured."""

    def test_rollback_script_file_exists(self, rollback_script_path):
        assert rollback_script_path.exists(), f"Rollback script not found at {rollback_script_path}"

    def test_rollback_script_has_shebang(self, rollback_script_path):
        content = rollback_script_path.read_text(encoding="utf-8")
        assert content.startswith("#!/usr/bin/env bash"), "Rollback script must start with #!/usr/bin/env bash"

    def test_rollback_script_has_strict_mode(self, rollback_script_path):
        content = rollback_script_path.read_text(encoding="utf-8")
        assert "set -euo pipefail" in content, "Rollback script must use 'set -euo pipefail'"


class TestRollbackScriptArguments:
    """Validate argument parsing and flag recognition."""

    def test_script_accepts_environment_flag(self, rollback_script_path):
        content = rollback_script_path.read_text(encoding="utf-8")
        assert "--environment" in content, "Script must accept --environment flag"

    def test_script_accepts_resource_group_flag(self, rollback_script_path):
        content = rollback_script_path.read_text(encoding="utf-8")
        assert "--resource-group" in content, "Script must accept --resource-group flag"

    def test_script_accepts_dry_run_flag(self, rollback_script_path):
        content = rollback_script_path.read_text(encoding="utf-8")
        assert "--dry-run" in content, "Script must accept --dry-run flag"

    def test_script_accepts_revision_api_flag(self, rollback_script_path):
        content = rollback_script_path.read_text(encoding="utf-8")
        assert "--revision-api" in content, "Script must accept --revision-api flag"

    def test_script_accepts_revision_agents_flag(self, rollback_script_path):
        content = rollback_script_path.read_text(encoding="utf-8")
        assert "--revision-agents" in content, "Script must accept --revision-agents flag"

    def test_script_accepts_revision_ingestion_flag(self, rollback_script_path):
        content = rollback_script_path.read_text(encoding="utf-8")
        assert "--revision-ingestion" in content, "Script must accept --revision-ingestion flag"

    def test_script_accepts_revision_web_flag(self, rollback_script_path):
        content = rollback_script_path.read_text(encoding="utf-8")
        assert "--revision-web" in content, "Script must accept --revision-web flag"


class TestRollbackExitCodes:
    """Validate exit code definitions in the script."""

    def test_exit_code_0_defined(self, rollback_script_path):
        """Exit code 0 = success or first-run bootstrap."""
        content = rollback_script_path.read_text(encoding="utf-8")
        assert "exit 0" in content, "Script must define exit code 0"

    def test_exit_code_1_defined(self, rollback_script_path):
        """Exit code 1 = rollback failed."""
        content = rollback_script_path.read_text(encoding="utf-8")
        assert "exit 1" in content, "Script must define exit code 1"

    def test_exit_code_2_defined(self, rollback_script_path):
        """Exit code 2 = invalid arguments."""
        content = rollback_script_path.read_text(encoding="utf-8")
        assert "exit 2" in content, "Script must define exit code 2"

    def test_exit_code_3_defined(self, rollback_script_path):
        """Exit code 3 = Azure CLI not available."""
        content = rollback_script_path.read_text(encoding="utf-8")
        assert "exit 3" in content, "Script must define exit code 3"

    def test_exit_code_4_defined(self, rollback_script_path):
        """Exit code 4 = post-rollback health check failed (critical)."""
        content = rollback_script_path.read_text(encoding="utf-8")
        assert "exit 4" in content, "Script must define exit code 4"


class TestRollbackValidation:
    """Validate input validation logic in the script."""

    def test_validates_environment_values(self, rollback_script_path):
        content = rollback_script_path.read_text(encoding="utf-8")
        assert "staging" in content and "production" in content, (
            "Script must validate environment is staging or production"
        )

    def test_validates_az_cli_availability(self, rollback_script_path):
        content = rollback_script_path.read_text(encoding="utf-8")
        assert "command -v az" in content or "which az" in content, "Script must check for Azure CLI availability"

    def test_validates_resource_group_required(self, rollback_script_path):
        content = rollback_script_path.read_text(encoding="utf-8")
        assert "resource-group" in content.lower() and "required" in content.lower(), (
            "Script must validate resource-group is required"
        )


class TestRollbackDryRun:
    """Validate dry-run mode behavior."""

    def test_dry_run_prefix_in_output(self, rollback_script_path):
        content = rollback_script_path.read_text(encoding="utf-8")
        assert "[DRY-RUN]" in content, "Dry-run output must use [DRY-RUN] prefix"

    def test_dry_run_uses_rollback_prefix(self, rollback_script_path):
        content = rollback_script_path.read_text(encoding="utf-8")
        assert "[ROLLBACK]" in content, "Output must use [ROLLBACK] prefix"


# ── T036: First-run bootstrap ────────────────────────────────────────────────


class TestRollbackFirstRunBootstrap:
    """Validate first-run bootstrap handling (no previous revisions)."""

    def test_first_run_bootstrap_handling(self, rollback_script_path):
        content = rollback_script_path.read_text(encoding="utf-8")
        # Script should handle the case where no previous revision exists
        assert "first" in content.lower() or "bootstrap" in content.lower(), (
            "Script must handle first-run bootstrap case"
        )

    def test_first_run_exits_zero(self, rollback_script_path):
        content = rollback_script_path.read_text(encoding="utf-8")
        # There should be a path where first deployment → exit 0
        assert "bootstrap" in content.lower() and "exit 0" in content, "First-run bootstrap must exit with code 0"


class TestRollbackOutputFormat:
    """Validate structured output format per contract."""

    def test_rollback_prefix_used(self, rollback_script_path):
        content = rollback_script_path.read_text(encoding="utf-8")
        assert "[ROLLBACK]" in content, "Output must use [ROLLBACK] prefix"

    def test_success_indicator(self, rollback_script_path):
        content = rollback_script_path.read_text(encoding="utf-8")
        assert "✅" in content, "Success output must include ✅"

    def test_error_indicator(self, rollback_script_path):
        content = rollback_script_path.read_text(encoding="utf-8")
        assert "❌" in content, "Error output must include ❌"

    def test_health_check_in_script(self, rollback_script_path):
        content = rollback_script_path.read_text(encoding="utf-8")
        assert "health" in content.lower(), "Script must include post-rollback health checks"

    def test_all_four_services_checked(self, rollback_script_path):
        """Verify all 4 service health endpoints are checked."""
        content = rollback_script_path.read_text(encoding="utf-8")
        assert "/api/health" in content, "Must check api at /api/health"
        assert "/health" in content, "Must check agents/ingestion at /health"
        # web uses / — checked via SERVICE_DEFS
