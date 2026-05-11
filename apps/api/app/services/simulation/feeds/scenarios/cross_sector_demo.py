"""Spec-039 T137 — cross-sector demo scenario (FR-061, SC-008).

NSW request → VIC fulfilment cross-state resource sharing — exercises
state government, transport sector and utility sector hand-offs.
"""

from __future__ import annotations

from collections.abc import Iterator

from .. import bom_severe_weather_warning, traffic_road_closure, utility_outage
from .._models import CanonicalRecord
from ._base import compose

SCENARIO_ID = "demo-cross-sector-v1"
DOMAIN_GROUP = "cross-sector"
DEFAULT_SEED = 42
PARTICIPATING_PERSONAS = (
    "state-government", "transport", "utility",
    "community-ngos", "local-government",
)
PARTICIPATING_FEEDS = (
    traffic_road_closure.SOURCE_SHAPE,
    utility_outage.SOURCE_SHAPE,
    bom_severe_weather_warning.SOURCE_SHAPE,
)


def emit(seed: int = DEFAULT_SEED) -> Iterator[CanonicalRecord]:
    return compose(
        SCENARIO_ID, seed,
        feed_calls=[
            (traffic_road_closure.emit, {"jurisdiction": "nsw", "count": 4}),
            (utility_outage.emit, {"jurisdiction": "vic", "count": 4}),
            (bom_severe_weather_warning.emit, {"jurisdiction": "nsw", "count": 3}),
        ],
    )


__all__ = ["DEFAULT_SEED", "DOMAIN_GROUP", "PARTICIPATING_FEEDS",
           "PARTICIPATING_PERSONAS", "SCENARIO_ID", "emit"]
