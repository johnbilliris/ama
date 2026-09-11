"""Wave C / T-AA19 — staging-promotion smoke-injection e2e contract test.

Asserts that ``.github/workflows/staging-promotion.yml`` declares a
``smoke-injection`` job that:

* runs BEFORE ``runtime-gate`` (i.e. ``runtime-gate`` declares
  ``needs: [static-gate, smoke-injection]``);
* uses a dedicated test tenant ``tnt-stg-smoke`` (no production tenant
  pollution);
* injects across 5 cascade-source categories with at least 8 events each
  (≥ 40 events total → 33 % margin over the 30-sample CLT floor).

Aligns with plan.md §C2.5 risk register #2 and quality.md CHK117 / CHK137.

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

_WORKFLOW_PATH = Path(__file__).resolve().parents[2] / ".github" / "workflows" / "staging-promotion.yml"


@pytest.fixture(scope="module")
def workflow() -> dict:
    return yaml.safe_load(_WORKFLOW_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def workflow_text() -> str:
    return _WORKFLOW_PATH.read_text(encoding="utf-8")


def test_smoke_injection_job_present(workflow: dict) -> None:
    assert "smoke-injection" in workflow["jobs"], (
        "Cycle 2 / T-AA19 — `smoke-injection` job MUST be declared so "
        "the 30-sample CLT floor is reliably met before runtime-gate."
    )


def test_runtime_gate_depends_on_smoke_injection(workflow: dict) -> None:
    runtime = workflow["jobs"]["runtime-gate"]
    needs = runtime.get("needs", [])
    if isinstance(needs, str):
        needs = [needs]
    assert "smoke-injection" in needs, (
        "runtime-gate MUST require smoke-injection so synthetic load "
        "lands BEFORE the 24 h trailing-window SLIs evaluate."
    )


def test_promote_depends_on_smoke_injection(workflow: dict) -> None:
    promote = workflow["jobs"]["promote"]
    needs = promote.get("needs", [])
    if isinstance(needs, str):
        needs = [needs]
    assert "smoke-injection" in needs


def test_smoke_injection_uses_isolated_test_tenant(workflow_text: str) -> None:
    assert "tnt-stg-smoke" in workflow_text, (
        "Cycle 2 / T-AA19 — smoke-injection MUST run in tnt-stg-smoke to prevent production-tenant SLI pollution."
    )


def test_smoke_injection_targets_5_cascade_categories(workflow_text: str) -> None:
    for cat in (
        "weather",
        "fire-behaviour",
        "hydrology",
        "transport",
        "evacuation-centre",
    ):
        assert cat in workflow_text, f"smoke-injection missing category {cat}"


def test_smoke_injection_at_least_40_events(workflow_text: str) -> None:
    """≥ 40 events = 5 categories × 8 each = 33 % margin over 30 floor."""
    assert "SMOKE_TARGET_PER_CATEGORY: 8" in workflow_text
    assert "< 40" in workflow_text or "total < 40" in workflow_text
