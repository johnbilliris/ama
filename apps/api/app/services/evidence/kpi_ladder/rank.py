"""Life-safety primacy ranker (T-S13, FR-006, CHK006).

Sorts indicators / scorecard rows so that life-safety indicators precede
efficiency indicators regardless of magnitude. Used by every rollup view.
"""

from __future__ import annotations

from collections.abc import Iterable

from ..models.kpi import IndicatorDefinition

_TIER_ORDER = {"life_safety": 0, "efficiency": 1}


def life_safety_first(indicators: Iterable[IndicatorDefinition]) -> list[IndicatorDefinition]:
    """Stable sort: life-safety tier first, then by name (deterministic)."""
    return sorted(indicators, key=lambda i: (_TIER_ORDER.get(i.life_safety_tier, 99), i.name))


def life_safety_first_dicts(rows: Iterable[dict]) -> list[dict]:
    """Same ranking applied to raw dicts."""
    return sorted(
        rows,
        key=lambda r: (
            _TIER_ORDER.get(r.get("life_safety_tier", "efficiency"), 99),
            r.get("name", ""),
        ),
    )
