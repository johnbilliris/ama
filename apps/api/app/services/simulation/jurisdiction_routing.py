"""Jurisdiction × hazard × agency routing — spec-036 Phase X (T-X01) / FR-021.

Replaces the coarse jurisdiction-only routing flagged by the sectors
cohort (Step 8 finding C8 / multi-jurisdiction.md J01–J31) with a
fine-grained tuple service.

Public API
----------
* :func:`route(jurisdiction, hazard, agency_hint=None) -> RoutingDecision`
* :class:`RoutingDecision` — frozen Pydantic model exposing the resolved
  ``jurisdiction``, ``hazard``, and ordered ``agencies`` tuple.
* :class:`UnknownRouteError` — raised when no tuple matches; callers MUST
  surface a fail-closed audit per constitution invariant.

The fixture data lives at
``apps/api/app/services/simulation/data/jurisdiction_routes.json`` and
is loaded once via :func:`load_routes` (LRU-cached). Wave-3 follow-ups
T-X02..X07 will tighten the per-jurisdiction details; T-X08 carries the
full multi-jurisdiction.md J01–J31 integration coverage.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Final

from pydantic import BaseModel, ConfigDict, Field

DEFAULT_PATH: Final[Path] = (
    Path(__file__).resolve().parent / "data" / "jurisdiction_routes.json"
)


class UnknownRouteError(LookupError):
    """No routing tuple exists for the requested (jurisdiction, hazard)."""


class _RouteEntry(BaseModel):
    """Single (jurisdiction × hazard × agencies) tuple as stored on disk."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    jurisdiction: str
    hazard: str
    agencies: tuple[str, ...]


class RoutingDecision(BaseModel):
    """Resolved routing decision returned by :func:`route`."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    jurisdiction: str
    hazard: str
    agencies: tuple[str, ...] = Field(min_length=1)


@lru_cache(maxsize=1)
def load_routes(path: Path | None = None) -> tuple[_RouteEntry, ...]:
    """Load and cache routing tuples from ``jurisdiction_routes.json``."""

    target = path or DEFAULT_PATH
    payload = json.loads(target.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError(
            f"jurisdiction_routes.json at {target} must be a JSON array."
        )
    return tuple(_RouteEntry.model_validate(entry) for entry in payload)


def route(
    jurisdiction: str,
    hazard: str,
    agency_hint: str | None = None,
) -> RoutingDecision:
    """Resolve the agency tuple for a given ``(jurisdiction, hazard)``.

    When multiple agencies match and ``agency_hint`` is provided, the
    decision is narrowed to that single agency (e.g. VIC fire with
    ``agency_hint="FRV"`` returns just ``("FRV",)``). When the hint does
    not match any of the candidates, the full tuple is returned (the
    caller treats the hint as advisory).
    """

    candidates = [
        e
        for e in load_routes()
        if e.jurisdiction == jurisdiction and e.hazard == hazard
    ]
    if not candidates:
        raise UnknownRouteError(
            f"No routing tuple for jurisdiction={jurisdiction!r}, hazard={hazard!r}"
        )

    # The fixture is single-row per (jurisdiction, hazard) today; future
    # tasks T-X02..X07 may introduce splits, so we guard against duplicates.
    agencies: tuple[str, ...] = candidates[0].agencies
    if agency_hint is not None and agency_hint in agencies:
        agencies = (agency_hint,)

    return RoutingDecision(
        jurisdiction=jurisdiction,
        hazard=hazard,
        agencies=agencies,
    )


__all__ = [
    "DEFAULT_PATH",
    "RoutingDecision",
    "UnknownRouteError",
    "load_routes",
    "route",
]
