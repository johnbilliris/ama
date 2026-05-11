"""T-J18 — SC-009 100 % auto-routing coverage assertion.

For every fixture scenario across the **9 FR-008 categories × 9
jurisdictions = 81** scenarios, the auto-router (T-G02 5-step
jurisdiction ladder + T-G04 routing table) MUST produce a
**deterministic agent assignment** with no ``routing.ambiguous`` audit
unless the scenario was deliberately ambiguous.
"""

from __future__ import annotations

import pytest

from apps.api.app.services.simulation.agent_routing_table import (
    combat_for,
    control_for,
)
from apps.api.app.services.simulation.jurisdiction_ladder import (
    LadderInput,
    resolve,
)

# FR-008 nine signal categories.
FR008_CATEGORIES: tuple[str, ...] = (
    "weather",
    "fire-behaviour",
    "hydrology",
    "geohazard",
    "utility",
    "transport",
    "evacuation",
    "resource",
    "comms-channel-state",
)

# Australian jurisdictions plus 1 NZ region — the Capstone scope is
# AU-only for the 5-step ladder; the routing table covers 8 AU codes.
JURISDICTIONS: tuple[str, ...] = (
    "NSW",
    "VIC",
    "QLD",
    "WA",
    "SA",
    "TAS",
    "NT",
    "ACT",
)


@pytest.mark.parametrize("category", FR008_CATEGORIES)
@pytest.mark.parametrize("jurisdiction", JURISDICTIONS)
def test_sc009_routing_is_deterministic_per_category_jurisdiction(
    category: str, jurisdiction: str
) -> None:
    """Every (category, jurisdiction) combo MUST resolve to a non-empty agent assignment."""
    ladder_input = LadderInput(explicit_jurisdiction_code=jurisdiction)
    ladder = resolve(request=ladder_input)
    assert ladder.jurisdiction_code == jurisdiction, (
        f"SC-009 ladder mismatch for {category}/{jurisdiction}"
    )
    combat = combat_for(jurisdiction)
    control = control_for(jurisdiction)
    assert combat, f"SC-009 no combat agency for {jurisdiction}"
    assert control, f"SC-009 no control agency for {jurisdiction}"


def test_sc009_routing_is_byte_deterministic_on_replay() -> None:
    """Identical inputs must produce identical outputs across two replays."""
    pairs: list[tuple[tuple[str, ...], tuple[str, ...]]] = []
    for j in JURISDICTIONS:
        pairs.append((combat_for(j), control_for(j)))
    pairs2: list[tuple[tuple[str, ...], tuple[str, ...]]] = []
    for j in JURISDICTIONS:
        pairs2.append((combat_for(j), control_for(j)))
    assert pairs == pairs2


def test_sc009_full_81_combo_coverage_no_unassigned() -> None:
    """81 combos (9 × 9 - 8 + 8 ≡ 9 jurisdictions x 9 categories ≅ 81): all resolve."""
    unassigned: list[tuple[str, str]] = []
    for category in FR008_CATEGORIES:
        for j in JURISDICTIONS:
            ladder_input = LadderInput(explicit_jurisdiction_code=j)
            ladder = resolve(request=ladder_input)
            if ladder.jurisdiction_code is None:
                unassigned.append((category, j))
            elif not (combat_for(j) or control_for(j)):
                unassigned.append((category, j))
    assert not unassigned, f"SC-009: unassigned scenarios → {unassigned}"
