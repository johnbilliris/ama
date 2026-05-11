"""Wave D / T-AA20 — `evacuation` ↔ `evacuation-centre` cascade alias test.

Pass-1 Q3 ruling — both spellings MUST resolve to the same canonical
SubAgent set so the cascade orchestrator never has to normalise the
category at the call-site.

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
"""

from __future__ import annotations

from packages.domain.src.domain.sim_cascade_matrix import (
    _CASCADE_ALIASES,
    CASCADE_MATRIX,
    cascade_targets_for,
)


def test_evacuation_alias_matches_evacuation_centre() -> None:
    assert cascade_targets_for("evacuation") == cascade_targets_for("evacuation-centre")


def test_evacuation_alias_present_in_alias_map() -> None:
    # Cycle 2 / T-AA20 — alias resolves at lookup time but is NOT
    # counted by ``all_cascade_categories`` (the canonical Y01..Y05
    # set is preserved at 5 entries).
    assert "evacuation" in _CASCADE_ALIASES
    assert _CASCADE_ALIASES["evacuation"] == "evacuation-centre"
    assert "evacuation-centre" in CASCADE_MATRIX


def test_evacuation_alias_resolves_to_planning_evac_resource() -> None:
    expected = frozenset({"Planning", "Evac", "Resource"})
    assert cascade_targets_for("evacuation") == expected
