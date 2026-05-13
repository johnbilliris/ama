"""Spec-039 T080: BoM-shaped severe weather warning feed (FR-020, FR-046).

Fictitious emulation of the Bureau of Meteorology severe weather warning
shape (cyclone, storm, fire weather). NEVER touches ``*.bom.gov.au``.
Warning-class — every body embeds the FR-046 ``test_marker``.
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

SOURCE_SHAPE: Final[str] = "bom.severe_weather_warning.v1"
FEED_VERSION: Final[str] = "v1"

_HAZARD_TYPES: Final[tuple[str, ...]] = ("cyclone", "severe_storm", "fire_weather", "heatwave", "damaging_wind")
_PRODUCT_PREFIX: Final[dict[str, str]] = {
    "nsw": "IDN",
    "vic": "IDV",
    "qld": "IDQ",
    "wa": "IDW",
    "sa": "IDS",
    "tas": "IDT",
    "nt": "IDD",
    "act": "IDA",
    "au": "IDZ",
}


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
        ts = clk.tick(60_000_000 + rng.randint(0, 30_000_000))
        hazard = _HAZARD_TYPES[rng.randrange(len(_HAZARD_TYPES))]
        body = {
            "test_marker": WARNING_TEST_MARKER,
            "product_id": f"{_PRODUCT_PREFIX[j]}{10000 + i:05d}",
            "hazard_type": hazard,
            "severity": rng.choice(["minor", "moderate", "major", "extreme"]),
            "issuing_office": f"BoM-{j.upper()}-FICTITIOUS",
            "areas_affected": [f"{j}-fictitious-region-{rng.randint(1, 12):02d}"],
            "headline": f"FICTITIOUS {hazard.replace('_', ' ').upper()} WARNING — TEST DATA",
            "valid_from": ts,
            "valid_until": clk.now_iso(),
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
