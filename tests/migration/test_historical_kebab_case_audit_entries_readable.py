"""Wave A / T-AA10 — historic kebab-case audit row read-tolerance.

Cycle 2 / Amendment A2-07 / FR-070 — historic Cycle 1 audit rows persisted
with kebab-case ``sub_agent`` values MUST remain readable. The
``_KEBAB_TO_PASCAL`` shim in :mod:`apps.api.app.services.simulation.audit_writer`
provides read-time tolerance; this test exercises every Cycle 1 kebab-case
literal end-to-end.

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
"""

from __future__ import annotations

import pytest

from apps.api.app.services.simulation.audit_writer import (
    _KEBAB_TO_PASCAL,
    kebab_to_pascal_sub_agent,
)

HISTORIC_KEBAB_TO_PASCAL = {
    "monitoring": "Intel",
    "planning": "Planning",
    "resource-allocation": "Resource",
    "communication": "Comms",
    "evacuation": "Evac",
    "risk-assessment": "Risk",
    "simulation-telemetry-injection": "Operations",
}


@pytest.mark.parametrize("kebab,pascal", sorted(HISTORIC_KEBAB_TO_PASCAL.items()))
def test_historic_kebab_audit_value_maps_to_pascal(kebab: str, pascal: str) -> None:
    """Read-time shim translates legacy kebab → canonical PascalCase."""

    assert kebab_to_pascal_sub_agent(kebab) == pascal


def test_kebab_to_pascal_table_matches_canonical_history() -> None:
    """Sanity check — the in-module table mirrors the canonical history."""

    assert _KEBAB_TO_PASCAL == HISTORIC_KEBAB_TO_PASCAL, (
        "audit_writer._KEBAB_TO_PASCAL MUST match the canonical Cycle 1 → "
        "Cycle 2 migration table (Amendment A2-07 / FR-070)."
    )
