"""Spec-038 T088: utility outage feed shape (FR-020).

Fictitious electricity / water / gas / telecoms outage notifications.
NEVER touches a real utility provider endpoint.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Final

from ._base import build_record, ensure_clock, validate_jurisdiction
from ._canonical import SimulatedClock
from ._models import CanonicalRecord, FeedParams
from ._seeded_random import seeded_rng

SOURCE_SHAPE: Final[str] = "utility.outage.v1"
FEED_VERSION: Final[str] = "v1"


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
    for i in range(count):
        ts = clk.tick(rng.randint(10_000_000, 120_000_000))
        utility = rng.choice(["electricity", "water", "gas", "telecoms"])
        body = {
            "outage_id": f"FICT-{j.upper()}-{utility[:3].upper()}-{i:05d}",
            "utility_type": utility,
            "provider": f"Fictitious {j.upper()} {utility.title()} Co.",
            "affected_customers_estimate": rng.randint(50, 25_000),
            "affected_postcodes": [
                f"{rng.randint(2000, 7999):04d}" for _ in range(rng.randint(1, 4))
            ],
            "cause": rng.choice([
                "storm_damage", "bushfire_damage", "planned_maintenance",
                "equipment_failure", "third_party_dig_in"
            ]),
            "etr": ts,
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
