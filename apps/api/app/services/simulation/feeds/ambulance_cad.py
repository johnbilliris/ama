"""Spec-039 T089: ambulance Computer-Aided Dispatch (CAD) feed (FR-020).

Fictitious ambulance CAD job events. Categories aligned to standard
CAD priority codes (P1..P5) but with no real callers, no real addresses,
no real PII.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Final

from ._base import build_record, ensure_clock, validate_jurisdiction
from ._canonical import SimulatedClock
from ._models import CanonicalRecord, FeedParams
from ._seeded_random import seeded_rng

SOURCE_SHAPE: Final[str] = "ambulance.cad.v1"
FEED_VERSION: Final[str] = "v1"


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
        ts = clk.tick(rng.randint(2_000_000, 60_000_000))
        body = {
            "job_id": f"FICT-{j.upper()}-CAD-{i:06d}",
            "priority": rng.choice(["P1", "P2", "P3", "P4", "P5"]),
            "incident_type": rng.choice(
                ["trauma", "cardiac", "respiratory", "obstetric", "psychiatric", "mass_casualty", "transport"]
            ),
            "dispatch_time": ts,
            "vehicle_callsign": f"FICT-{j.upper()}-{rng.randint(100, 999)}",
            "destination_facility_ref": f"fictitious-{j}-hospital-{rng.randint(1, 20)}",
            "patient_count": rng.randint(1, 8),
            "patient_demographics": {"age_band": rng.choice(["0-4", "5-12", "13-17", "18-39", "40-64", "65+"])},
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
