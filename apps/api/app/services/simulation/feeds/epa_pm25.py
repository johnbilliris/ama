"""Spec-039 T086: EPA-shaped PM2.5 air-quality feed (FR-020).

Fictitious PM2.5 readings shaped like a state EPA jurisdiction feed.
NEVER touches a real EPA endpoint. Sensor-class — no warning marker.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Final

from ._base import build_record, ensure_clock, validate_jurisdiction
from ._canonical import SimulatedClock
from ._models import CanonicalRecord, FeedParams
from ._seeded_random import seeded_rng

SOURCE_SHAPE: Final[str] = "epa.pm25.v1"
FEED_VERSION: Final[str] = "v1"


def _aqi_band(pm: float) -> str:
    if pm >= 250:
        return "hazardous"
    if pm >= 150:
        return "very_poor"
    if pm >= 80:
        return "poor"
    if pm >= 35:
        return "fair"
    if pm >= 12:
        return "good"
    return "very_good"


def emit(
    scenario_id: str,
    seed: int,
    *,
    jurisdiction: str = "vic",
    count: int = 5,
    params: FeedParams | None = None,
    clock: SimulatedClock | None = None,
) -> Iterator[CanonicalRecord]:
    j = validate_jurisdiction(jurisdiction)
    rng = seeded_rng(scenario_id, seed, SOURCE_SHAPE)
    clk = ensure_clock(clock, scenario_id, seed)
    pm = round(rng.uniform(5, 60), 1)
    for i in range(count):
        ts = clk.tick(60 * 60 * 1_000_000)
        pm = round(max(0.0, pm + rng.uniform(-15, 25)), 1)
        body = {
            "station_id": f"FICT-{j.upper()}-AQ-{rng.randint(100, 999)}",
            "station_name": f"Fictitious {j.upper()} Air Monitoring Site",
            "observed_at": ts,
            "pm25_ug_m3": pm,
            "aqi_band": _aqi_band(pm),
            "source_attribution": rng.choice([
                "bushfire_smoke", "industrial", "transport", "background"
            ]),
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
