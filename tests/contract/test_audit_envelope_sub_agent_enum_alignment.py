"""Wave A / T-AA10 — sub_agent enum 7-kebab → 9-PascalCase shim test.

Asserts:

1. Canonical ``ALL_SUB_AGENTS`` is the 9-name PascalCase set
   (Amendment A2-07 / FR-070).
2. ``_KEBAB_TO_PASCAL`` maps every Cycle 1 kebab-case name to a PascalCase
   name in ``ALL_SUB_AGENTS``.
3. ``kebab_to_pascal_sub_agent`` round-trips PascalCase unchanged, maps
   legacy kebab-case to PascalCase, and raises ``ValueError`` for unknown.

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
"""

from __future__ import annotations

import pytest

from apps.api.app.services.simulation.audit_writer import (
    _KEBAB_TO_PASCAL,
    kebab_to_pascal_sub_agent,
)
from packages.domain.src.domain.models.aiims_mapping import ALL_SUB_AGENTS


def test_canonical_sub_agent_enum_is_9_pascal_case() -> None:
    """Amendment A2-07 / FR-070 — PascalCase 9-name canonical set."""

    expected = {
        "Comms",
        "Evac",
        "Health",
        "Intel",
        "Logistics",
        "Operations",
        "Planning",
        "Resource",
        "Risk",
    }
    assert set(ALL_SUB_AGENTS) == expected, (
        f"ALL_SUB_AGENTS MUST be the 9-name PascalCase canonical set "
        f"(got {set(ALL_SUB_AGENTS)})."
    )


def test_kebab_to_pascal_table_is_complete() -> None:
    """Cycle 1 historic kebab-case set MUST be covered by the shim."""

    expected_kebab = {
        "monitoring",
        "planning",
        "resource-allocation",
        "communication",
        "evacuation",
        "risk-assessment",
        "simulation-telemetry-injection",
    }
    assert set(_KEBAB_TO_PASCAL.keys()) == expected_kebab, (
        "_KEBAB_TO_PASCAL MUST cover the 7 historic Cycle 1 kebab-case "
        "sub_agent names (Amendment A2-07 read-time tolerance)."
    )

    # Every mapped value MUST be a canonical PascalCase name.
    for kebab, pascal in _KEBAB_TO_PASCAL.items():
        assert pascal in ALL_SUB_AGENTS, (
            f"_KEBAB_TO_PASCAL[{kebab!r}] = {pascal!r} is not in canonical "
            f"PascalCase set ALL_SUB_AGENTS."
        )


def test_pascal_round_trip_unchanged() -> None:
    """Already-PascalCase names pass through without rewriting."""

    for name in ALL_SUB_AGENTS:
        assert kebab_to_pascal_sub_agent(name) == name


def test_kebab_to_pascal_known_mappings() -> None:
    """A spot-check of Cycle 1 → Cycle 2 mapping correctness."""

    assert kebab_to_pascal_sub_agent("evacuation") == "Evac"
    assert kebab_to_pascal_sub_agent("planning") == "Planning"
    assert kebab_to_pascal_sub_agent("resource-allocation") == "Resource"
    assert kebab_to_pascal_sub_agent("communication") == "Comms"


def test_unknown_value_raises() -> None:
    with pytest.raises(ValueError) as exc_info:
        kebab_to_pascal_sub_agent("unknown-sub-agent")
    assert "audit.unknown_sub_agent" in str(exc_info.value)
