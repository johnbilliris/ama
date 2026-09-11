"""Wave C / T-AA19 — smoke-injection tenant isolation guard.

Asserts the smoke-injection job runs as the ``Simulation.Coordinator``
identity in the dedicated ``tnt-stg-smoke`` tenant — never under a
production tenant.

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
"""

from __future__ import annotations

from pathlib import Path

import pytest

_WORKFLOW_PATH = Path(__file__).resolve().parents[2] / ".github" / "workflows" / "staging-promotion.yml"


@pytest.fixture(scope="module")
def workflow_text() -> str:
    return _WORKFLOW_PATH.read_text(encoding="utf-8")


def test_smoke_identity_is_coordinator(workflow_text: str) -> None:
    assert "Simulation.Coordinator" in workflow_text


def test_smoke_tenant_is_dedicated_test_tenant(workflow_text: str) -> None:
    assert "tnt-stg-smoke" in workflow_text


def test_smoke_does_not_reference_prod_tenant_literals(workflow_text: str) -> None:
    """No production tenant ID literal appears anywhere — smoke runs in
    the dedicated test tenant only."""

    # Grep for typical production tenant ID prefixes that would be a
    # tell-tale leakage. Comments mentioning "production-tenant" in
    # descriptive prose are fine; we look for actual identifier shapes.
    forbidden_literals = (
        "tenant_id: tnt-prod",
        "tenant_id: tnt-au-",
        "SMOKE_TENANT_ID: tnt-prod",
        "SMOKE_TENANT_ID: tnt-au-",
    )
    for literal in forbidden_literals:
        assert literal not in workflow_text, f"smoke-injection MUST NOT reference {literal!r}"
