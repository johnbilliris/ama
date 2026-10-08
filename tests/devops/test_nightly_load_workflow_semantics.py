from __future__ import annotations

from pathlib import Path


def _workflow_text() -> str:
    return Path(".github/workflows/nightly-load.yml").read_text(encoding="utf-8")


def test_nightly_load_invokes_headless_locust_with_required_classes() -> None:
    text = _workflow_text()
    assert "locust --headless" in text
    assert "--users 1000" in text
    assert "--spawn-rate 50" in text
    assert "--run-time 10m" in text
    assert "DashboardUser BurstIngestionUser" in text


def test_nightly_load_requires_staging_host_variable() -> None:
    text = _workflow_text()
    assert "LOAD_TARGET_URL is required" in text
    assert "disaster-response-hub.example" not in text


def test_nightly_load_invokes_corrected_report_and_propagates_failures() -> None:
    text = _workflow_text()
    assert "python tests/load/report.py" in text
    assert "--stats-csv load-results/locust_stats.csv" in text
    assert "|| true" not in text


def test_nightly_load_emits_completed_telemetry_only_on_success() -> None:
    text = _workflow_text()
    assert "- name: Publish results to App Insights" in text
    assert "if: success()" in text


def test_nightly_load_archives_raw_csv_report_and_metadata() -> None:
    text = _workflow_text()
    assert "load-results/locust_stats.csv" in text
    assert "load-results/report.json" in text
    assert "load-results/run-metadata.json" in text
    assert "path: load-results/" in text
