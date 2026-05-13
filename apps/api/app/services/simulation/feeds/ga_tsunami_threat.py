"""Spec-039 T085: Geoscience Australia-shaped tsunami threat advisory feed.

Warning-class — every record MUST embed FR-046 / F-001 ``test_marker``.
NEVER touches ``*.ga.gov.au`` or the Joint Australian Tsunami Warning Centre.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Final

from ._base import (
    WARNING_TEST_MARKER,
    build_record,
    ensure_clock,
    validate_jurisdiction,
)
from ._canonical import SimulatedClock
from ._models import CanonicalRecord, FeedParams
from ._seeded_random import seeded_rng

SOURCE_SHAPE: Final[str] = "ga.tsunami_threat.v1"
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
        ts = clk.tick(15 * 60 * 1_000_000)
        body = {
            "test_marker": WARNING_TEST_MARKER,
            "advisory_id": f"FICT-JATWC-{j.upper()}-{i:05d}",
            "threat_level": rng.choice(["no_threat", "marine_threat", "land_threat", "major_land_threat"]),
            "trigger_event": {
                "magnitude": round(rng.uniform(6.5, 9.2), 1),
                "depth_km": round(rng.uniform(5.0, 60.0), 1),
                "epicentre_region": "fictitious-pacific-rim-zone",
            },
            "estimated_arrival": ts,
            "coastal_zones": [f"{j}-fictitious-coastal-zone-{rng.randint(1, 9)}"],
            "headline": "FICTITIOUS TSUNAMI ADVISORY — TEST DATA — DO NOT BROADCAST",
            "issuing_office": "JATWC-FICTITIOUS",
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
