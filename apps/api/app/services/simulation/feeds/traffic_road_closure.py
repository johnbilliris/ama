"""Spec-039 T087: traffic / road-closure feed shape (FR-020).

Fictitious VicRoads / Live Traffic NSW-shaped road closure events. NEVER
touches a real traffic authority endpoint.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Final

from ._base import build_record, ensure_clock, validate_jurisdiction
from ._canonical import SimulatedClock
from ._models import CanonicalRecord, FeedParams
from ._seeded_random import seeded_rng

SOURCE_SHAPE: Final[str] = "traffic.road_closure.v1"
FEED_VERSION: Final[str] = "v1"


def emit(
    scenario_id: str,
    seed: int,
    *,
    jurisdiction: str = "nsw",
    count: int = 5,
    params: FeedParams | None = None,
    clock: SimulatedClock | None = None,
) -> Iterator[CanonicalRecord]:
    j = validate_jurisdiction(jurisdiction)
    rng = seeded_rng(scenario_id, seed, SOURCE_SHAPE)
    clk = ensure_clock(clock, scenario_id, seed)
    for i in range(count):
        ts = clk.tick(rng.randint(5_000_000, 90_000_000))
        body = {
            "incident_id": f"FICT-{j.upper()}-RC-{i:05d}",
            "road_name": f"Fictitious {j.upper()} Highway {rng.randint(1, 99)}",
            "segment_ref": f"{j}-segment-{rng.randint(1000, 9999)}",
            "closure_type": rng.choice([
                "full_closure", "lane_closure", "diversion", "speed_restriction"
            ]),
            "cause": rng.choice([
                "flooding", "bushfire", "crash", "fallen_tree",
                "structural_damage", "planned_event"
            ]),
            "estimated_clearance": ts,
            "advice": "Use alternative route — fictitious test data.",
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
