"""T-J10 — simulation-stub-sweep BLOCKING flip contract test."""

from __future__ import annotations

from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
WORKFLOW = REPO / ".github" / "workflows" / "simulation-stub-sweep.yml"
BRANCH_PROTECTION = REPO / ".github" / "branch-protection.yml"


@pytest.fixture(scope="module")
def workflow_text() -> str:
    return WORKFLOW.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def branch_protection_text() -> str:
    return BRANCH_PROTECTION.read_text(encoding="utf-8")


def test_simulation_stub_sweep_uses_enforce_flag(workflow_text: str) -> None:
    assert "--enforce" in workflow_text, (
        "T-J10 — `simulation-stub-sweep.yml` MUST run the tool with `--enforce`."
    )


def test_simulation_stub_sweep_does_not_run_in_informational_mode(workflow_text: str) -> None:
    """The workflow MUST NOT run in informational mode after T-J10."""
    # The exact `python tools/simulation_stub_sweep.py --root .` informational
    # invocation MUST be replaced.
    informational_invocation = "python tools/simulation_stub_sweep.py --root .\n"
    assert informational_invocation not in workflow_text


def test_branch_protection_lists_simulation_stub_sweep(branch_protection_text: str) -> None:
    assert "simulation-stub-sweep" in branch_protection_text, (
        "T-J10 — branch-protection.yml MUST list the simulation-stub-sweep job as a required check."
    )


def test_branch_protection_requires_strict_status_checks(branch_protection_text: str) -> None:
    assert "strict: true" in branch_protection_text
