"""Spec-036 Wave 4 — canonical cascade matrix expansion (T-Y01..Y05).

This module materialises the cross-sector cascade dependencies the
omitted-cohort review flagged. It complements the existing kebab-case
``apps/api/app/config/cascade_rules.yaml`` (which drives the
``cascade_orchestrator.fan_out`` legacy role names) with a PascalCase
canonical map keyed off the FR-051 ``SignalCategory`` set and resolved
into the canonical 9-member ``SubAgent`` Literal.

The matrix is consulted by upstream cohort tests (T-Y06) to assert that
each cross-sector dependency is reachable. Production fan-out continues
to flow through ``cascade_orchestrator.fan_out`` + the YAML config — the
two sources are reconciled in ``tests/integration/test_cascade_matrix_expansion.py``.

The 5 entries below correspond to T-Y01..T-Y05:

* utility (T-Y01)        → {Health, Comms, Transport-aware via Logistics, Resource}
* hydrology (T-Y02)      → {Risk, Evac, Comms, Resource}
* transport (T-Y03)      → {Evac, Comms, Resource}
* evacuation-centre (T-Y04) → {Planning, Evac, Resource}
* geohazard (T-Y05)      → {Risk, Evac, Resource}
"""

from __future__ import annotations

from typing import Final

from packages.domain.src.domain.models.aiims_mapping import SubAgent

#: Canonical cascade matrix (T-Y01..Y05). Keys are the
#: ``SignalCategory`` strings used by ``SyntheticSignal.category``;
#: values are the set of :data:`SubAgent` members that MUST receive a
#: cascade fan-out (in addition to the existing direct subscribers).
CASCADE_MATRIX: Final[dict[str, frozenset[str]]] = {
    "utility": frozenset({"Health", "Comms", "Logistics", "Resource"}),
    "hydrology": frozenset({"Risk", "Evac", "Comms", "Resource"}),
    "transport": frozenset({"Evac", "Comms", "Resource"}),
    "evacuation-centre": frozenset({"Planning", "Evac", "Resource"}),
    "geohazard": frozenset({"Risk", "Evac", "Resource"}),
}

# Cycle 2 / T-AA20 / A2-03 — canonical aliases for legacy callers.
# Aliases resolve to the canonical category at lookup time but are
# NOT counted in :func:`all_cascade_categories` (which enumerates the
# canonical Y01..Y05 set only). Per pass-1 Q3 (spec.md L302-337), the
# matrix is the SINGLE source of truth so this alias map is
# materialised here and consumed via :func:`cascade_targets_for` —
# callers do NOT have to normalise.
_CASCADE_ALIASES: Final[dict[str, str]] = {
    "evacuation": "evacuation-centre",
}


def cascade_targets_for(category: str) -> frozenset[str]:
    """Return the canonical SubAgent set for a category.

    Returns an empty frozenset when no cross-sector dependencies are
    declared for the category — the caller MUST treat this as "no
    cascade beyond the direct subscriber set" (per FR-052).
    """

    canonical = _CASCADE_ALIASES.get(category, category)
    return CASCADE_MATRIX.get(canonical, frozenset())


def all_cascade_categories() -> tuple[str, ...]:
    """Return the immutable list of categories with cascade rules."""

    return tuple(CASCADE_MATRIX.keys())


# Sanity check: every named SubAgent must be a member of the canonical
# Literal (caught at import time if the Literal drifts).
for _cat, _targets in CASCADE_MATRIX.items():
    for _sub in _targets:
        assert _sub in SubAgent.__args__, (  # type: ignore[attr-defined]
            f"sim_cascade_matrix: {_cat!r} → unknown SubAgent {_sub!r}"
        )
del _cat, _targets, _sub


__all__ = [
    "CASCADE_MATRIX",
    "all_cascade_categories",
    "cascade_targets_for",
]
