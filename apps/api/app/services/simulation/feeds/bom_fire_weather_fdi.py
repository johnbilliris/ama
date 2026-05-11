"""Spec-038 T082: BoM-shaped Fire Danger Index (FDI) feed (FR-020).

Fictitious hourly Forest Fire Danger Index observations.
NEVER touches ``*.bom.gov.au``. Index-class — no warning marker required.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Final

from ._base import build_record, ensure_clock, validate_jurisdiction
from ._canonical import SimulatedClock
from ._models import CanonicalRecord, FeedParams
from ._seeded_random import seeded_rng

SOURCE_SHAPE: Final[str] = "bom.fire_weather_fdi.v1"
FEED_VERSION: Final[str] = "v1"


def _fdi_rating(value: float) -> str:
    if value >= 100:
        return "catastrophic"
    if value >= 75:
        return "extreme"
    if value >= 50:
        return "severe"
    if value >= 25:
        return "very_high"
    if value >= 12:
        return "high"
    return "low_moderate"


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
    for i in range(count):
        ts = clk.tick(60 * 60 * 1_000_000)  # hourly
        fdi = round(rng.uniform(5, 110), 1)
        body = {
            "station_id": f"FICT-{j.upper()}-FDI-{rng.randint(100, 999)}",
            "station_name": f"Fictitious {j.upper()} Fire Weather Station",
            "observed_at": ts,
            "temp_c": round(rng.uniform(20, 44), 1),
            "rh_pct": round(rng.uniform(5, 70), 1),
            "wind_kmh": round(rng.uniform(0, 80), 1),
            "wind_dir_deg": rng.randint(0, 359),
            "drought_factor": round(rng.uniform(2, 10), 1),
            "fdi": fdi,
            "rating": _fdi_rating(fdi),
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
