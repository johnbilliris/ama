from __future__ import annotations

import re
from pathlib import Path
from typing import cast

import yaml

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
WORKFLOW_PATH = REPOSITORY_ROOT / ".github" / "workflows" / "ci.yml"
SOVEREIGN_LABELS = ["self-hosted", "ama-au-sovereign", "azure-au", "linux", "x64"]
FEATURE_PATHS = ("tools/specify-cli/", "scripts/spec001/", "specs/001-extension-list/")


def _workflow() -> dict[str, object]:
    return cast(
        dict[str, object],
        yaml.load(WORKFLOW_PATH.read_text(encoding="utf-8"), Loader=yaml.BaseLoader),
    )


def _job(workflow: dict[str, object], name: str) -> dict[str, object]:
    jobs = workflow["jobs"]
    assert isinstance(jobs, dict)
    job = jobs[name]
    assert isinstance(job, dict)
    return job


def _steps(job: dict[str, object]) -> list[dict[str, object]]:
    steps = job["steps"]
    assert isinstance(steps, list)
    return [step for step in steps if isinstance(step, dict)]


def test_specify_cli_quality_uses_full_history_and_exact_changed_path_output() -> None:
    workflow = _workflow()
    quality = _job(workflow, "quality")
    checkout = next(step for step in _steps(quality) if str(step.get("uses", "")).startswith("actions/checkout@"))
    assert checkout.get("with") == {"fetch-depth": "0"}

    outputs = quality.get("outputs")
    assert isinstance(outputs, dict)
    assert outputs.get("specify-cli-changed") == "${{ steps.specify-cli-changes.outputs.changed }}"
    classifier = next(step for step in _steps(quality) if step.get("id") == "specify-cli-changes")
    script = str(classifier.get("run", ""))
    assert "github.event.pull_request.base.sha" in script
    assert "github.event.pull_request.head.sha" in script
    assert "github.event.before" in script
    assert "github.sha" in script
    assert "git diff --name-only" in script
    assert "--depth" not in script
    assert all(path in script for path in FEATURE_PATHS)
    assert re.search(r"changed=(true|false)", script)


def test_specify_cli_quality_is_path_gated_on_exact_sovereign_runner() -> None:
    job = _job(_workflow(), "specify-cli-quality")
    assert job.get("needs") == "quality"
    assert job.get("if") == "needs.quality.outputs.specify-cli-changed == 'true'"
    assert job.get("timeout-minutes") == "30"
    assert job.get("runs-on") == SOVEREIGN_LABELS


def test_specify_cli_quality_clears_indexes_and_keeps_installers_offline() -> None:
    job = _job(_workflow(), "specify-cli-quality")
    environment = job.get("env")
    assert isinstance(environment, dict)
    assert environment.get("PIP_INDEX_URL") == ""
    assert environment.get("UV_DEFAULT_INDEX") == ""
    assert environment.get("PIP_NO_INDEX") == "1"
    assert environment.get("UV_OFFLINE") == "1"

    scripts = "\n".join(str(step.get("run", "")) for step in _steps(job) if "run" in step)
    installer_lines = [
        line.strip()
        for line in scripts.splitlines()
        if re.search(r"\b(uv sync|uv build|uv pip install|pip install)\b", line)
    ]
    assert installer_lines
    assert all("--offline" in line for line in installer_lines)
    assert any("uv pip install" in line and "dist/*.whl" in line for line in installer_lines)


def test_specify_cli_quality_owns_post_implementation_sovereign_lifecycle() -> None:
    job = _job(_workflow(), "specify-cli-quality")
    scripts = "\n".join(str(step.get("run", "")) for step in _steps(job) if "run" in step)
    assert "python scripts/spec001/protected_state_selfcheck.py" in scripts
    assert "python scripts/spec001/run_local_gates.py --self-check" in scripts
    assert scripts.count("--self-check") == 1
    assert "--preflight-prerequisites --execution-mode sovereign" in scripts
    assert "--start-session --execution-mode sovereign" in scripts
    assert "--finalize-session" in scripts
    assert "expected red" not in scripts.lower()
    assert "local-synthetic" in scripts
    assert "release" in scripts
    assert "sovereign" in scripts
