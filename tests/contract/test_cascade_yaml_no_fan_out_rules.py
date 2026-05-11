"""Wave D / T-AA20 — build-time guard: `fan_out_rules:` MUST stay removed.

The legacy YAML block under ``apps/api/app/config/cascade_rules.yaml``
was the source of A2-03's drift. Pass-1 Q3 made
:func:`packages.domain.src.domain.sim_cascade_matrix.cascade_targets_for`
the SOLE source of truth. This test fails if the block is reintroduced.

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
"""

from __future__ import annotations

from pathlib import Path

import pytest

_YAML_PATH = (
    Path(__file__).resolve().parents[2]
    / "apps"
    / "api"
    / "app"
    / "config"
    / "cascade_rules.yaml"
)


@pytest.fixture(scope="module")
def yaml_text() -> str:
    return _YAML_PATH.read_text(encoding="utf-8")


def test_yaml_does_not_declare_fan_out_rules(yaml_text: str) -> None:
    """Cycle 2 / T-AA20 / A2-03 — `fan_out_rules:` MUST be absent."""

    forbidden_lines = [
        line.strip() for line in yaml_text.splitlines()
        if line.strip().startswith("fan_out_rules:")
    ]
    assert not forbidden_lines, (
        "cascade_rules.yaml MUST NOT declare `fan_out_rules:` — the "
        "matrix in `packages/domain/src/domain/sim_cascade_matrix.py` "
        "is the canonical source of truth (pass-1 Q3 / A2-03)."
    )


def test_yaml_retains_ladder_and_cap(yaml_text: str) -> None:
    """The operational `ladder:` + `cap:` keys remain (FR-057)."""

    assert "ladder:" in yaml_text
    assert "cap:" in yaml_text


def test_yaml_documents_removal_in_a_comment(yaml_text: str) -> None:
    """Removal MUST be documented inline so a future contributor knows
    why the block isn't there."""

    assert "T-AA20" in yaml_text or "A2-03" in yaml_text or "sim_cascade_matrix" in yaml_text
