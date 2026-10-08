from __future__ import annotations

import tomllib
from pathlib import Path


def _ci_text() -> str:
    path = Path(__file__).resolve().parents[2] / ".github" / "workflows" / "ci.yml"
    return path.read_text(encoding="utf-8")


def test_python_test_step_includes_simulation_slice() -> None:
    text = _ci_text()
    assert "tests/simulation" in text


def test_python_test_step_includes_unit_slice() -> None:
    text = _ci_text()
    assert "pytest tests/unit tests/contract tests/integration tests/simulation" in text


def test_quality_job_has_ten_minute_timeout() -> None:
    text = _ci_text()
    assert "quality:" in text
    assert "timeout-minutes: 10" in text


def test_ci_push_trigger_excludes_feature_branches_to_avoid_duplicate_pr_runs() -> None:
    text = _ci_text()
    push_section = text.split("  push:\n", 1)[1].split("  pull_request:\n", 1)[0]
    assert '"[0-9][0-9][0-9]-*"' not in push_section
    assert all(f"      - {branch}" in push_section for branch in ["main", "dev", "staging", "production"])


def test_required_ci_steps_do_not_swallow_failures() -> None:
    text = _ci_text()
    assert "- name: python-test" in text
    assert "- name: perf-benchmark" in text
    assert "python-test\n        continue-on-error: true" not in text
    assert "perf-benchmark\n        continue-on-error: true" not in text
    assert "pytest tests/benchmark/ --benchmark-json=.benchmarks/current.json -q || true" not in text


def test_coverage_and_benchmark_follow_their_artifact_producers() -> None:
    text = _ci_text()
    assert "- name: python-test\n        id: python-test" in text
    assert "- name: perf-benchmark\n        id: perf-benchmark" in text
    assert "name: coverage-ratchet-unit\n        if: always() && steps.python-test.outcome == 'success'" in text
    assert "name: upload-benchmark-results\n        uses:" in text
    assert "if: always() && steps.perf-benchmark.outcome == 'success'" in text
    assert "name: upload-coverage-results\n        uses:" in text
    assert "if: always() && steps.python-test.outcome == 'success'" in text


def test_strict_python_types_are_a_blocking_gate() -> None:
    text = _ci_text()
    assert "- name: python-type-strict" in text
    assert "run: mypy apps packages" in text
    config_path = Path(__file__).resolve().parents[2] / "pyproject.toml"
    config = tomllib.loads(config_path.read_text(encoding="utf-8"))
    assert config["tool"]["mypy"]["strict"] is True
    assert "python-type-strict\n        continue-on-error: true" not in text


def test_windows_quality_job_uses_locked_uv_dependencies_and_cache() -> None:
    text = _ci_text()
    job = text.split("  quality-windows:\n", 1)[1].split("\n  golden-set-canonical:", 1)[0]

    assert "cache: pip" in job
    assert "cache-dependency-path:" in job
    assert "uv.lock" in job
    assert "name: Cache uv packages" in job
    assert "hashFiles('uv.lock')" in job
    assert "uv sync --locked --extra windows-ci --no-install-project" in job
    assert "uv pip install --python .venv\\Scripts\\python.exe --no-deps -e apps/eval-runner" in job
    assert "uv run --no-sync ruff check apps tests packages" in job
    assert "uv run --no-sync pytest tests/contract tests/integration" in job
    assert "Install eval gate package without runtime dependencies" in job


def test_windows_ci_extra_excludes_eval_runner_runtime_dependencies() -> None:
    config_path = Path(__file__).resolve().parents[2] / "pyproject.toml"
    config = tomllib.loads(config_path.read_text(encoding="utf-8"))
    dependencies = set(config["project"]["optional-dependencies"]["windows-ci"])

    assert dependencies == {
        "ama-disaster-response-agents",
        "ama-disaster-response-api",
        "ama-eval-core",
        "pytest>=8.3",
        "pytest-asyncio>=0.24",
        "hypothesis>=6.0",
        "ruff>=0.8.4",
    }
    assert "ama-eval-runner" not in dependencies


def test_quality_job_runs_web_lint() -> None:
    text = _ci_text()
    assert "name: web-lint" in text
    assert "corepack pnpm --filter @ama/web lint" in text


def test_story_acceptance_job_exists_with_required_projects() -> None:
    text = _ci_text()
    assert "story-acceptance:" in text
    assert "PYTHONPATH: ${{ github.workspace }}/packages/domain/src" in text
    assert "--project=chromium" in text
    assert "--project=mobile" in text


def test_story_acceptance_has_zero_collection_guard() -> None:
    text = _ci_text()
    assert "Assert story acceptance tests are collected" in text
    assert "No acceptance tests collected" in text


def test_story_acceptance_uses_reliable_apt_and_caches_playwright_browsers() -> None:
    text = _ci_text()
    job = text.split("  story-acceptance:\n", 1)[1].split("\n  evidence-pack-publication-gate:", 1)[0]

    assert "name: Cache Playwright browsers" in job
    assert "path: ~/.cache/ms-playwright" in job
    assert "hashFiles('pnpm-lock.yaml')" in job
    assert "name: Configure reliable Ubuntu APT mirror" in job
    assert "azure.archive.ubuntu.com" in job
    assert "archive.ubuntu.com" in job
    assert 'Acquire::Retries "2"' in job
    assert 'Acquire::http::Timeout "30"' in job
    assert 'Acquire::https::Timeout "30"' in job


def test_story_acceptance_targets_original_specs() -> None:
    text = _ci_text()
    job = text.split("  story-acceptance:\n", 1)[1].split("\n  evidence-pack-publication-gate:", 1)[0]
    collection_step = job.split("- name: Assert story acceptance tests are collected", 1)[1].split(
        "- name: Run story acceptance tests", 1
    )[0]
    assert "test_incident_commander_dashboard.spec.ts" in collection_step
    assert "test_persona_workspace.spec.ts" in collection_step
    assert "test_dashboard_decision_support.spec.ts" in collection_step
    assert "../../tests/e2e/" not in collection_step
