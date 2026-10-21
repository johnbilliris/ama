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


def test_windows_candidate_map_job_uses_two_isolated_uncached_installs() -> None:
    text = _ci_text()
    job = text.split("  phase8-python-windows-candidate-maps:\n", 1)[1].split("\n  simulation-tenant-isolation:", 1)[0]

    assert (
        "if: github.event_name == 'pull_request' && "
        "github.event.pull_request.head.ref == '001-proxy-dependency-upgrades'"
    ) in job
    assert "needs: python-package-source-policy" in job
    assert "runs-on: windows-latest" in job
    assert "foreach ($runId in @('a', 'b'))" in job
    assert "phase8-windows-root-$runId" in job
    assert "uv sync --locked --extra windows-ci --no-install-project --no-cache" in job
    assert "uv pip install --python $python --no-deps --no-cache -e apps/eval-runner" in job
    assert "Compare-Object -ReferenceObject $mapA -DifferenceObject $mapB" in job
    assert "name: phase8-python-windows-candidate-maps" in job
    assert "actions/cache@" not in job


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
    run_step = job.split("- name: Run story acceptance tests (chromium + mobile)", 1)[1]
    story_specs = (
        "test_incident_commander_dashboard.spec.ts",
        "test_persona_workspace.spec.ts",
        "test_dashboard_decision_support.spec.ts",
    )

    for story_spec in story_specs:
        assert story_spec in collection_step
        assert story_spec in run_step

    assert "../../tests/e2e/" not in collection_step
    assert "../../tests/e2e/" not in run_step


def test_feature_x64_validation_jobs_are_scoped_and_uncached() -> None:
    text = _ci_text()
    node_job = text.split("  phase8-node-x64-candidate-maps:\n", 1)[1].split(
        "\n  phase8-alpine-x64-candidate-builds:", 1
    )[0]
    alpine_job = text.split("  phase8-alpine-x64-candidate-builds:\n", 1)[1].split(
        "\n  simulation-tenant-isolation:", 1
    )[0]
    for job in (node_job, alpine_job):
        assert "github.event_name == 'pull_request'" in job
        assert "github.event.pull_request.head.ref == '001-proxy-dependency-upgrades'" in job
        assert "github.event.pull_request.head.repo.full_name == github.repository" in job
        assert "runs-on: ubuntu-24.04" in job
        assert "contents: read" in job
        assert "NPM_CONFIG_REGISTRY: https://packagefeedproxy.microsoft.io/npm/" in job
        assert 'node-version: "24.21.0"' in job
        assert "for run_id in a b; do" in job
        assert "actions/cache@" not in job
        assert "continue-on-error" not in job
        assert "if-no-files-found: error" in job
    assert "phase8-node-store-$run_id" in node_job
    assert "pnpm install --frozen-lockfile --store-dir" in node_job
    assert 'test ! -e "$NPM_CONFIG_STORE_DIR"' in node_job
    assert "pnpm --filter @ama/web test" in node_job
    assert 'cmp "$out/map-a.txt" "$out/map-b.txt"' in node_job
    assert (
        "ALPINE_BASE: node:24-alpine@sha256:83f1c388c31fb2e51f7cbd4dea949b96260798c98f206e8e4696bc93bd964e3a"
    ) in alpine_job
    assert "docker build --no-cache --platform linux/amd64" in alpine_job
    assert "--publish 127.0.0.1:33124:3000" in alpine_job
    assert 'cmp "$out/builder-expected-$run_id.txt" "$out/builder-input-$run_id.txt"' in alpine_job
    assert 'cmp "$out/map-a.txt" "$out/map-b.txt"' in alpine_job
    assert "--retry 20 --retry-all-errors --retry-delay 1 --retry-max-time 60 --max-time 5" in alpine_job
    assert "trap cleanup EXIT" in alpine_job
    assert 'docker logs "$container" > "$out/server-$run_id.log" 2>&1' in alpine_job
    assert 'exit "$status"' in alpine_job
    assert "docker push" not in alpine_job
