"""Spec-038 T091: IoT sensor telemetry feed (FR-020).

Generic IoT sensor telemetry envelope — smoke, temperature, water level
sensors at fictitious deployment sites. NEVER touches a real telemetry
endpoint.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Final

from ._base import build_record, ensure_clock, validate_jurisdiction
from ._canonical import SimulatedClock
from ._models import CanonicalRecord, FeedParams
from ._seeded_random import seeded_rng

SOURCE_SHAPE: Final[str] = "sensor.telemetry.v1"
FEED_VERSION: Final[str] = "v1"


def emit(
    scenario_id: str,
    seed: int,
    *,
    jurisdiction: str = "nt",
    count: int = 5,
    params: FeedParams | None = None,
    clock: SimulatedClock | None = None,
) -> Iterator[CanonicalRecord]:
    j = validate_jurisdiction(jurisdiction)
    rng = seeded_rng(scenario_id, seed, SOURCE_SHAPE)
    clk = ensure_clock(clock, scenario_id, seed)
    sensor_kind = rng.choice(["smoke", "temperature", "water_level", "humidity"])
    for i in range(count):
        ts = clk.tick(rng.randint(10_000_000, 60_000_000))
        if sensor_kind == "smoke":
            value, unit = round(rng.uniform(0, 500), 1), "ug_m3"
        elif sensor_kind == "temperature":
            value, unit = round(rng.uniform(-5, 50), 1), "celsius"
        elif sensor_kind == "water_level":
            value, unit = round(rng.uniform(0, 6), 2), "metres"
        else:
            value, unit = round(rng.uniform(10, 100), 1), "percent_rh"
        body = {
            "device_id": f"fict-{j}-{sensor_kind}-{rng.randint(1000, 9999):04d}",
            "sensor_kind": sensor_kind,
            "deployment_site": f"fictitious-{j}-site-{rng.randint(1, 50):03d}",
            "observed_at": ts,
            "value": value,
            "unit": unit,
            "battery_pct": rng.randint(20, 100),
            "signal_dbm": rng.randint(-110, -60),
            "alert_threshold_breached": rng.random() < 0.1,
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
