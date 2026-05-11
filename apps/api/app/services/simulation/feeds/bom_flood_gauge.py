"""Spec-038 T083: BoM-shaped river / flood gauge readings (FR-020).

Fictitious river-gauge readings. NEVER touches ``*.bom.gov.au``.
Sensor-class — no warning marker required.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Final

from ._base import build_record, ensure_clock, validate_jurisdiction
from ._canonical import SimulatedClock
from ._models import CanonicalRecord, FeedParams
from ._seeded_random import seeded_rng

SOURCE_SHAPE: Final[str] = "bom.flood_gauge.v1"
FEED_VERSION: Final[str] = "v1"


def _flood_class(level: float, minor: float, moderate: float, major: float) -> str:
    if level >= major:
        return "major"
    if level >= moderate:
        return "moderate"
    if level >= minor:
        return "minor"
    return "below_minor"


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
    minor, moderate, major = 5.0, 7.5, 10.0
    level = round(rng.uniform(2.0, 8.0), 2)
    for i in range(count):
        ts = clk.tick(15 * 60 * 1_000_000)
        level = round(max(0.0, level + rng.uniform(-0.4, 0.6)), 2)
        body = {
            "gauge_id": f"FICT-{j.upper()}-GAUGE-{rng.randint(100, 999)}",
            "gauge_name": f"Fictitious {j.upper()} River Gauge",
            "river_basin": f"fictitious-{j}-basin-{rng.randint(1, 9)}",
            "observed_at": ts,
            "level_m": level,
            "rate_of_rise_m_per_hr": round(rng.uniform(-0.5, 1.2), 3),
            "minor_threshold_m": minor,
            "moderate_threshold_m": moderate,
            "major_threshold_m": major,
            "flood_class": _flood_class(level, minor, moderate, major),
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
