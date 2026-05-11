"""Per-category signal-freshness configuration (feature 036, FR-008, plan-decision #9).

Maps each of the **9 FR-008 categories** to its freshness window in seconds:

| category              | window |
|-----------------------|--------|
| weather               |   5 min|
| fire-behaviour        |   5 min|
| hydrology             |  10 min|
| geohazard             |   5 min|
| utility               |  15 min|
| transport             |  15 min|
| evacuation            |  10 min|
| resource              |  30 min|
| comms-channel-state   |  10 min|

Wired into ``controller_service`` via DI — see ``apps/api/app/services/simulation/__init__.py``.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Final

FRESHNESS_WINDOW_SECONDS: Final[Mapping[str, int]] = {
    "weather": 300,
    "fire-behaviour": 300,
    "hydrology": 600,
    "geohazard": 300,
    "utility": 900,
    "transport": 900,
    "evacuation": 600,
    "resource": 1800,
    "comms-channel-state": 600,
}

DEFAULT_FRESHNESS_WINDOW_SECONDS: Final[int] = 600


def get_window(category: str) -> int:
    """Return freshness window seconds for ``category``; falls back to default."""

    return FRESHNESS_WINDOW_SECONDS.get(category, DEFAULT_FRESHNESS_WINDOW_SECONDS)


__all__ = [
    "DEFAULT_FRESHNESS_WINDOW_SECONDS",
    "FRESHNESS_WINDOW_SECONDS",
    "get_window",
    "is_signal_stale",
]


def is_signal_stale(
    *,
    category: str,
    observed_at: datetime,
    now: datetime | None = None,
) -> bool:
    """Return ``True`` if ``now - observed_at`` exceeds the category window."""
    from datetime import datetime

    current = now or datetime.now(UTC)
    if observed_at.tzinfo is None:
        observed_at = observed_at.replace(tzinfo=UTC)
    if current.tzinfo is None:
        current = current.replace(tzinfo=UTC)
    delta = (current - observed_at).total_seconds()
    return delta > get_window(category)
