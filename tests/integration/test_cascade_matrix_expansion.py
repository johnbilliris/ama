"""Spec-036 Wave 4 — T-Y06 cascade matrix expansion integration test.

One scenario per cascade rule from T-Y01..T-Y05; asserts the canonical
``SubAgent`` set is reachable for each cross-sector dependency.
"""

from __future__ import annotations

import pytest

from packages.domain.src.domain.models.aiims_mapping import (
    AGENT_TO_AIIMS,
    ALL_SUB_AGENTS,
)
from packages.domain.src.domain.sim_cascade_matrix import (
    CASCADE_MATRIX,
    all_cascade_categories,
    cascade_targets_for,
)

# ---------------------------------------------------------------------------
# Per-Y task assertion (one parametrised case per Y01..Y05)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("category", "expected"),
    [
        ("utility", {"Health", "Comms", "Logistics", "Resource"}),
        ("hydrology", {"Risk", "Evac", "Comms", "Resource"}),
        ("transport", {"Evac", "Comms", "Resource"}),
        ("evacuation-centre", {"Planning", "Evac", "Resource"}),
        ("geohazard", {"Risk", "Evac", "Resource"}),
    ],
    ids=["Y01-utility", "Y02-hydrology", "Y03-transport", "Y04-evac-centre", "Y05-geohazard"],
)
def test_cascade_matrix_per_rule(category: str, expected: set[str]) -> None:
    assert cascade_targets_for(category) == expected, (
        f"Cascade matrix for {category!r} expected {expected}, got "
        f"{cascade_targets_for(category)}"
    )


def test_cascade_matrix_targets_subset_of_canonical_subagents() -> None:
    """Every cascade target must be a member of the canonical SubAgent set."""

    canonical = set(ALL_SUB_AGENTS)
    for cat, targets in CASCADE_MATRIX.items():
        for t in targets:
            assert t in canonical, (
                f"Cascade target {t!r} for {cat!r} is not in canonical SubAgent set"
            )


def test_cascade_matrix_aiims_function_attribution() -> None:
    """Every cascade target must have an AIIMS function attribution
    (FR-061; needed by lessons capture T-S03 sub-agent responses)."""

    for cat, targets in CASCADE_MATRIX.items():
        for t in targets:
            assert t in AGENT_TO_AIIMS, (
                f"Cascade target {t!r} for {cat!r} has no AIIMS attribution"
            )


def test_cascade_matrix_categories_count() -> None:
    """Five new cross-sector dependencies (Y01-Y05) — no more, no less."""

    assert len(all_cascade_categories()) == 5
    assert set(all_cascade_categories()) == {
        "utility",
        "hydrology",
        "transport",
        "evacuation-centre",
        "geohazard",
    }


def test_unknown_category_returns_empty_frozenset() -> None:
    """Unknown category must yield an empty frozenset (no implicit fan-out)."""

    assert cascade_targets_for("nonexistent") == frozenset()
