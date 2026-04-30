"""Tests for the automated demo script (scripts/demo.py).

Validates the full pipeline, failure paths, scenario switching,
verbose mode, output file, and CI performance requirements.
"""

from __future__ import annotations

import json
import sys
import time
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import pytest

# Ensure imports resolve the same way tests/conftest.py sets up paths
_REPO_ROOT = Path(__file__).resolve().parents[2]
_SCRIPTS = _REPO_ROOT / "scripts"
for _p in (
    _REPO_ROOT,
    _REPO_ROOT / "apps" / "api",
    _REPO_ROOT / "apps" / "agents",
    _SCRIPTS,
):
    _p_str = str(_p)
    if _p_str not in sys.path:
        sys.path.insert(0, _p_str)

# Now we can import from the demo script
from scripts.demo import (  # noqa: E402
    REQUIRED_LANGUAGES,
    SCENARIO_CONFIGS,
    DemoRun,
    Narrator,
    load_seed_data,
    run_pipeline,
    serialize_output,
)

# ---------------------------------------------------------------------------
# Markers
# ---------------------------------------------------------------------------

pytestmark = pytest.mark.simulation


# ---------------------------------------------------------------------------
# T034 — Success-path tests
# ---------------------------------------------------------------------------


class TestFullPipeline:
    """Test that run_pipeline() completes all 7 phases successfully."""

    def test_default_bushfire_all_phases_pass(self) -> None:
        """US1: Full pipeline with default bushfire scenario exits 0."""
        buf = StringIO()
        with patch("sys.stdout", buf):
            exit_code = run_pipeline(verbose=False, scenario="bushfire")

        assert exit_code == 0

        output = json.loads(buf.getvalue())
        assert output["status"] == "pass"
        assert output["scenario"] == "bushfire"
        assert len(output["phases"]) == 7

        for phase in output["phases"]:
            assert phase["status"] == "pass", f"Phase {phase['phase']} failed: {phase.get('error')}"

    def test_json_output_schema_keys(self) -> None:
        """Verify JSON output contains all root schema keys per output-schema.md."""
        buf = StringIO()
        with patch("sys.stdout", buf):
            run_pipeline(verbose=False, scenario="bushfire")

        output = json.loads(buf.getvalue())

        required_keys = {
            "run_id",
            "scenario",
            "status",
            "started_at",
            "completed_at",
            "duration_seconds",
            "phases",
            "audit_trail",
            "handoffs",
            "alerts",
        }
        assert required_keys.issubset(output.keys())

    def test_audit_trail_has_decision_records(self) -> None:
        """US3: audit_trail contains at least 4 decision records."""
        buf = StringIO()
        with patch("sys.stdout", buf):
            run_pipeline(verbose=False, scenario="bushfire")

        output = json.loads(buf.getvalue())
        audit_trail = output["audit_trail"]
        assert len(audit_trail) >= 4, f"Expected ≥4 decision records, got {len(audit_trail)}"

        # Check required fields
        for rec in audit_trail:
            assert "timestamp" in rec
            assert "decision_type" in rec
            assert "agent" in rec
            assert "approver_role" in rec
            assert "policy" in rec
            assert "outcome" in rec
            assert "supporting_data" in rec

    def test_handoffs_has_entries(self) -> None:
        """US3: handoffs contains at least 4 entries."""
        buf = StringIO()
        with patch("sys.stdout", buf):
            run_pipeline(verbose=False, scenario="bushfire")

        output = json.loads(buf.getvalue())
        handoffs = output["handoffs"]
        assert len(handoffs) >= 4, f"Expected ≥4 handoffs, got {len(handoffs)}"

        for h in handoffs:
            assert "source_agent" in h
            assert "target_agent" in h
            assert "confidence" in h
            assert "handoff_id" in h
            assert h["source_agent"] != h["target_agent"]

    def test_alerts_languages_six(self) -> None:
        """US1/US2: alerts.languages contains all 6 language codes."""
        buf = StringIO()
        with patch("sys.stdout", buf):
            run_pipeline(verbose=False, scenario="bushfire")

        output = json.loads(buf.getvalue())
        languages = output["alerts"]["languages"]
        for lang in REQUIRED_LANGUAGES:
            assert lang in languages, f"Missing language: {lang}"

    def test_alerts_summary_fields(self) -> None:
        """Verify AlertSummary has required fields."""
        buf = StringIO()
        with patch("sys.stdout", buf):
            run_pipeline(verbose=False, scenario="bushfire")

        output = json.loads(buf.getvalue())
        alerts = output["alerts"]
        assert alerts["total"] >= 1
        assert alerts["safety_validated"] is True
        assert len(alerts["channel_targets"]) > 0

    def test_run_id_format(self) -> None:
        """Verify run_id matches demo-YYYYMMDD-HHmmss pattern."""
        import re

        buf = StringIO()
        with patch("sys.stdout", buf):
            run_pipeline(verbose=False, scenario="bushfire")

        output = json.loads(buf.getvalue())
        assert re.match(r"demo-\d{8}-\d{6}", output["run_id"])

    def test_phase_order_sequential(self) -> None:
        """Verify phases are in correct order 1-7."""
        buf = StringIO()
        with patch("sys.stdout", buf):
            run_pipeline(verbose=False, scenario="bushfire")

        output = json.loads(buf.getvalue())
        orders = [p["order"] for p in output["phases"]]
        assert orders == [1, 2, 3, 4, 5, 6, 7]

    def test_exit_code_zero_on_success(self) -> None:
        """FR-007: exit code 0 on full pipeline success."""
        buf = StringIO()
        with patch("sys.stdout", buf):
            exit_code = run_pipeline(verbose=False, scenario="bushfire")
        assert exit_code == 0


# ---------------------------------------------------------------------------
# T035 — Failure-path tests
# ---------------------------------------------------------------------------


class TestFailurePaths:
    """Test failure handling and fail-fast behaviour."""

    def test_missing_seed_data_exits_before_pipeline(self) -> None:
        """US4: missing structural seed file aborts before agents start."""
        with patch(
            "scripts.demo.DATA_DIR",
            Path(__file__).parent / "nonexistent_data_dir",
        ):
            with pytest.raises(SystemExit) as exc_info:
                load_seed_data(SCENARIO_CONFIGS["bushfire"])
            assert exc_info.value.code == 1

    def test_failed_phase_marks_remaining_skipped(self) -> None:
        """FR-007: failure in one phase marks remaining as skipped."""
        # Simulate health-check failure by patching create_clients
        # to return a client that fails on GET /health
        from unittest.mock import MagicMock

        def mock_create_clients() -> dict:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_client.get.return_value = mock_response
            return {
                "platform": mock_client,
                "monitoring": mock_client,
                "risk_assessment": mock_client,
                "evacuation": mock_client,
                "resource_allocation": mock_client,
                "communication": mock_client,
            }

        buf = StringIO()
        with (
            patch("sys.stdout", buf),
            patch("scripts.demo.create_clients", mock_create_clients),
        ):
            exit_code = run_pipeline(verbose=False, scenario="bushfire")

        assert exit_code == 1
        output = json.loads(buf.getvalue())
        assert output["status"] == "fail"

        # First phase should be "fail", rest should be "skipped"
        assert output["phases"][0]["status"] == "fail"
        for phase in output["phases"][1:]:
            assert phase["status"] == "skipped"


# ---------------------------------------------------------------------------
# T036 — Scenario and mode tests
# ---------------------------------------------------------------------------


class TestScenarioAndMode:
    """Test scenario switching and verbose mode."""

    def test_cyclone_scenario_signal_type(self) -> None:
        """US4: --scenario cyclone produces cyclone-specific output."""
        buf = StringIO()
        with patch("sys.stdout", buf):
            exit_code = run_pipeline(verbose=False, scenario="cyclone")

        assert exit_code == 0
        output = json.loads(buf.getvalue())
        assert output["scenario"] == "cyclone"

        # The monitoring phase should reference the cyclone signal
        monitoring = output["phases"][1]
        assert monitoring["status"] == "pass"

    def test_flood_scenario_passes(self) -> None:
        """US4: --scenario flood completes successfully."""
        buf = StringIO()
        with patch("sys.stdout", buf):
            exit_code = run_pipeline(verbose=False, scenario="flood")

        assert exit_code == 0
        output = json.loads(buf.getvalue())
        assert output["scenario"] == "flood"

    def test_verbose_produces_stderr_narration(self) -> None:
        """US2: --verbose produces narration on stderr."""
        stdout_buf = StringIO()
        stderr_buf = StringIO()

        with patch("sys.stdout", stdout_buf), patch("sys.stderr", stderr_buf):
            exit_code = run_pipeline(verbose=True, scenario="bushfire")

        assert exit_code == 0

        # JSON should still be valid on stdout
        json_output = json.loads(stdout_buf.getvalue())
        assert json_output["status"] == "pass"

        # stderr should contain narration
        stderr_text = stderr_buf.getvalue()
        assert "DISASTER RESPONSE HUB" in stderr_text
        assert "Phase" in stderr_text

    def test_output_to_file(self, tmp_path: Path) -> None:
        """FR-006: --output writes JSON to file instead of stdout."""
        output_file = tmp_path / "demo-result.json"
        stdout_buf = StringIO()

        with patch("sys.stdout", stdout_buf):
            exit_code = run_pipeline(
                verbose=False,
                scenario="bushfire",
                output_path=str(output_file),
            )

        assert exit_code == 0
        assert output_file.exists()

        # stdout should be empty (JSON went to file)
        assert stdout_buf.getvalue().strip() == ""

        # File should contain valid JSON
        file_data = json.loads(output_file.read_text(encoding="utf-8"))
        assert file_data["status"] == "pass"
        assert len(file_data["phases"]) == 7


# ---------------------------------------------------------------------------
# T037 — Performance assertion
# ---------------------------------------------------------------------------


class TestPerformance:
    """Test CI performance requirements."""

    def test_pipeline_under_60_seconds(self) -> None:
        """SC-003: Full pipeline completes in under 60 seconds."""
        buf = StringIO()
        t0 = time.perf_counter()

        with patch("sys.stdout", buf):
            exit_code = run_pipeline(verbose=False, scenario="bushfire")

        elapsed = time.perf_counter() - t0

        assert exit_code == 0, "Pipeline must pass for performance test"
        assert elapsed < 60, f"Pipeline took {elapsed:.1f}s, must be under 60s"


# ---------------------------------------------------------------------------
# Additional helper tests
# ---------------------------------------------------------------------------


class TestSeedDataLoading:
    """Test seed data loading and validation."""

    def test_load_seed_data_bushfire(self) -> None:
        """Verify seed data loads correctly for bushfire scenario."""
        seed = load_seed_data(SCENARIO_CONFIGS["bushfire"])

        assert seed.population, "Population data should be loaded"
        assert seed.road_network, "Road network data should be loaded"
        assert seed.resource_inventory, "Resource inventory should be loaded"
        assert len(seed.alert_templates) == 6, "Should have 6 language template files"
        assert len(seed.scenario_templates) > 0, "Should have bushfire templates"

    def test_seed_data_has_expected_keys(self) -> None:
        """Verify seed data structural files have expected top-level keys."""
        seed = load_seed_data(SCENARIO_CONFIGS["bushfire"])

        assert "facilities" in seed.population or "metadata" in seed.population
        assert "nodes" in seed.road_network or "metadata" in seed.road_network
        assert "resources" in seed.resource_inventory


class TestNarrator:
    """Test Narrator class behaviour."""

    def test_narrator_silent_when_not_verbose(self) -> None:
        """Narrator methods are no-ops when verbose=False."""
        buf = StringIO()
        narrator = Narrator(verbose=False)
        with patch("sys.stderr", buf):
            narrator.header("bushfire")
            narrator.phase_start("setup", 1, "test")
            narrator.detail("detail")
            narrator.success("success")
            narrator.warning("warning")

        assert buf.getvalue() == ""

    def test_narrator_outputs_when_verbose(self) -> None:
        """Narrator produces output when verbose=True."""
        buf = StringIO()
        narrator = Narrator(verbose=True)
        with patch("sys.stderr", buf):
            narrator.header("bushfire")
            narrator.success("test message")

        output = buf.getvalue()
        assert "DISASTER RESPONSE HUB" in output
        assert "test message" in output


class TestSerializeOutput:
    """Test output serialisation."""

    def test_serialize_to_stdout(self) -> None:
        """serialize_output writes JSON to stdout by default."""
        from datetime import UTC, datetime

        run = DemoRun(
            run_id="demo-test",
            scenario="bushfire",
            started_at=datetime.now(UTC),
        )
        buf = StringIO()
        with patch("sys.stdout", buf):
            serialize_output(run, None)

        data = json.loads(buf.getvalue())
        assert data["run_id"] == "demo-test"

    def test_serialize_to_file(self, tmp_path: Path) -> None:
        """serialize_output writes JSON to file when path given."""
        from datetime import UTC, datetime

        run = DemoRun(
            run_id="demo-test",
            scenario="bushfire",
            started_at=datetime.now(UTC),
        )
        output_file = tmp_path / "out.json"
        serialize_output(run, str(output_file))

        data = json.loads(output_file.read_text(encoding="utf-8"))
        assert data["run_id"] == "demo-test"
