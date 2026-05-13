"""Spec-039 T084: Geoscience Australia-shaped earthquake event feed (FR-020).

Fictitious GA earthquake event-shape. NEVER touches ``*.ga.gov.au``.
Event-class — no warning marker.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Final

from ._base import build_record, ensure_clock, validate_jurisdiction
from ._canonical import SimulatedClock
from ._models import CanonicalRecord, FeedParams
from ._seeded_random import seeded_rng

SOURCE_SHAPE: Final[str] = "ga.earthquake_event.v1"
FEED_VERSION: Final[str] = "v1"

# Approximate centroids (deg) for synthetic event placement only — NOT a
# real seismic catalogue.
_J_CENTROID: Final[dict[str, tuple[float, float]]] = {
    "nsw": (-32.5, 147.5),
    "vic": (-37.0, 144.5),
    "qld": (-22.0, 145.0),
    "wa": (-26.0, 121.0),
    "sa": (-32.0, 135.0),
    "tas": (-42.0, 146.5),
    "nt": (-19.0, 134.0),
    "act": (-35.5, 149.0),
    "au": (-25.0, 134.0),
}


def emit(
    scenario_id: str,
    seed: int,
    *,
    jurisdiction: str = "wa",
    count: int = 5,
    params: FeedParams | None = None,
    clock: SimulatedClock | None = None,
) -> Iterator[CanonicalRecord]:
    j = validate_jurisdiction(jurisdiction)
    rng = seeded_rng(scenario_id, seed, SOURCE_SHAPE)
    clk = ensure_clock(clock, scenario_id, seed)
    cx, cy = _J_CENTROID[j]
    for i in range(count):
        ts = clk.tick(rng.randint(60_000_000, 600_000_000))
        body = {
            "event_id": f"FICT-GA-{j.upper()}-{i:05d}",
            "magnitude": round(rng.uniform(2.0, 6.5), 1),
            "magnitude_type": "ML",
            "depth_km": round(rng.uniform(2.0, 35.0), 1),
            "origin_time": ts,
            "epicentre": {
                "lat": round(cx + rng.uniform(-1.5, 1.5), 4),
                "lon": round(cy + rng.uniform(-1.5, 1.5), 4),
            },
            "felt_reports_count": rng.randint(0, 250),
            "review_status": rng.choice(["automatic", "manual"]),
            "jurisdiction": j,
        }
        yield build_record(
            scenario_id=scenario_id,
            seed=seed,
            source_shape=SOURCE_SHAPE,
            feed_version=FEED_VERSION,
            timestamp=ts,
            ordinal=i,
            body=body,
        )


__all__ = ["FEED_VERSION", "SOURCE_SHAPE", "emit"]
