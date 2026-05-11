"""Spec-038 T092: synthetic fallback feed (FR-025).

Generic fallback shape used when a persona has no public-data analogue.
Emits a clearly-labelled synthetic envelope so downstream consumers can
exercise the no-public-data path without crashing.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Final

from ._base import build_record, ensure_clock, validate_jurisdiction
from ._canonical import SimulatedClock
from ._models import CanonicalRecord, FeedParams
from ._seeded_random import seeded_rng

SOURCE_SHAPE: Final[str] = "synthetic.fallback.v1"
FEED_VERSION: Final[str] = "v1"


def emit(
    scenario_id: str,
    seed: int,
    *,
    jurisdiction: str = "au",
    count: int = 5,
    params: FeedParams | None = None,
    clock: SimulatedClock | None = None,
) -> Iterator[CanonicalRecord]:
    j = validate_jurisdiction(jurisdiction)
    rng = seeded_rng(scenario_id, seed, SOURCE_SHAPE)
    clk = ensure_clock(clock, scenario_id, seed)
    for i in range(count):
        ts = clk.tick(rng.randint(1_000_000, 60_000_000))
        body = {
            "synthetic_id": f"fict-fallback-{j}-{i:06d}",
            "kind": "synthetic_fallback",
            "category_hint": rng.choice([
                "operational", "logistics", "communications",
                "welfare", "intelligence", "policy"
            ]),
            "summary": (
                "Fictitious synthetic-fallback record (FR-025) — used when "
                "no public-dataset analogue exists for the target persona."
            ),
            "value_score": round(rng.uniform(0, 1), 4),
            "tags": sorted({rng.choice([
                "low-frequency", "exploratory", "edge-case",
                "no-public-analogue", "internal-only"
            ]) for _ in range(rng.randint(1, 3))}),
            "observed_at": ts,
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
