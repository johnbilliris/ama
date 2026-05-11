"""Contradiction detector (T-C15 / FR-013).

Reads recent signals within the per-category freshness window (T-A08 /
plan-decision #9) and tags the new signal's ``parameters.contradicts``
field with the offending prior signal IDs.

Conflict heuristic — intentionally conservative:
* Same ``category`` AND same ``simulation_id`` AND opposing
  ``parameters.direction`` (e.g. *increasing* vs *decreasing*) OR
* Numeric ``parameters.value`` differs by > 50 % within the window.

The detector is pure: it accepts an injected ``recent_signals`` iterable so
tests can pin behaviour without a Cosmos round-trip.
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime, timedelta

from packages.domain.src.domain.models.synthetic_signal import SyntheticSignal

OPPOSING_DIRECTIONS: dict[str, str] = {
    "increasing": "decreasing",
    "decreasing": "increasing",
    "rising": "falling",
    "falling": "rising",
    "open": "closed",
    "closed": "open",
}


def _is_within_window(candidate: SyntheticSignal, prior: SyntheticSignal, *, now: datetime) -> bool:
    if prior.category != candidate.category:
        return False
    age = now - prior.observed_at
    return age <= timedelta(seconds=candidate.freshness_window_seconds)


def _detect_direction_conflict(candidate: SyntheticSignal, prior: SyntheticSignal) -> bool:
    cand_dir = str(candidate.parameters.get("direction", "")).lower()
    prior_dir = str(prior.parameters.get("direction", "")).lower()
    if not cand_dir or not prior_dir:
        return False
    return OPPOSING_DIRECTIONS.get(cand_dir) == prior_dir


def _detect_value_conflict(candidate: SyntheticSignal, prior: SyntheticSignal) -> bool:
    try:
        c_val = float(candidate.parameters.get("value"))
        p_val = float(prior.parameters.get("value"))
    except (TypeError, ValueError):
        return False
    if p_val == 0:
        return False
    return abs(c_val - p_val) / abs(p_val) > 0.5


def detect(
    *,
    candidate: SyntheticSignal,
    recent_signals: Iterable[SyntheticSignal],
    now: datetime | None = None,
) -> list[str]:
    """Return prior-signal IDs that *candidate* contradicts (possibly empty)."""
    when = now or datetime.now(candidate.observed_at.tzinfo)
    contradicts: list[str] = []
    for prior in recent_signals:
        if prior.signal_id == candidate.signal_id:
            continue
        if not _is_within_window(candidate, prior, now=when):
            continue
        if _detect_direction_conflict(candidate, prior) or _detect_value_conflict(candidate, prior):
            contradicts.append(prior.signal_id)
    return contradicts
