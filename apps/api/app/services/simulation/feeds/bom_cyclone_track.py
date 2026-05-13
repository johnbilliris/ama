"""Spec-039 T081: BoM-shaped tropical cyclone track feed (FR-020, FR-046).

Fictitious emulation of BoM IDQ-format cyclone track points. NEVER touches
``*.bom.gov.au``. Warning-class — every record embeds the FR-046 marker.
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

SOURCE_SHAPE: Final[str] = "bom.cyclone_track.v1"
FEED_VERSION: Final[str] = "v1"


def _ficticious_name(rng) -> str:
    # Synthetic cyclone names — clearly fictional, no real Australian list.
    return rng.choice(
        [
            "Aurelia-X",
            "Bramble-X",
            "Currong-X",
            "Dalwood-X",
            "Eldoris-X",
            "Fjordan-X",
            "Galangal-X",
            "Hesperion-X",
        ]
    )


def emit(
    scenario_id: str,
    seed: int,
    *,
    jurisdiction: str = "qld",
    count: int = 5,
    params: FeedParams | None = None,
    clock: SimulatedClock | None = None,
) -> Iterator[CanonicalRecord]:
    j = validate_jurisdiction(jurisdiction)
    rng = seeded_rng(scenario_id, seed, SOURCE_SHAPE)
    clk = ensure_clock(clock, scenario_id, seed)
    name = _ficticious_name(rng)
    # Synthetic starting position offshore, deterministic per seed.
    lat = -10.0 - rng.uniform(0.0, 8.0)
    lon = 145.0 + rng.uniform(0.0, 10.0)
    for i in range(count):
        ts = clk.tick(30_000_000)
        lat += rng.uniform(-0.6, -0.1)  # drift south
        lon += rng.uniform(-0.4, 0.4)
        body = {
            "test_marker": WARNING_TEST_MARKER,
            "cyclone_name": f"FICTITIOUS-{name}",
            "track_point_id": f"{j.upper()}-CYC-{i:03d}",
            "category": rng.randint(1, 5),
            "central_pressure_hpa": 980 - rng.randint(0, 40),
            "max_wind_kmh": 120 + rng.randint(0, 100),
            "position": {"lat": round(lat, 4), "lon": round(lon, 4)},
            "movement_kmh": round(8 + rng.random() * 12, 1),
            "movement_bearing_deg": rng.randint(180, 270),
            "valid_at": ts,
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
