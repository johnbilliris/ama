"""Spec-038 T134 — SES demo scenario (FR-061, SC-008).

VIC riverine flood, multi-LGA progression: BoM flood gauge + severe
weather warning + utility outages. Exercises VIC SES, NSW SES (mutual
aid) and the SCC operations chain.
"""

from __future__ import annotations

from collections.abc import Iterator

from .. import bom_flood_gauge, bom_severe_weather_warning, utility_outage
from .._models import CanonicalRecord
from ._base import compose

SCENARIO_ID = "demo-ses-v1"
DOMAIN_GROUP = "ses"
DEFAULT_SEED = 42
PARTICIPATING_PERSONAS = (
    "ses-vic", "ses-nsw", "ses-qld",
    "operations-officer", "logistics-officer",
)
PARTICIPATING_FEEDS = (
    bom_flood_gauge.SOURCE_SHAPE,
    bom_severe_weather_warning.SOURCE_SHAPE,
    utility_outage.SOURCE_SHAPE,
)


def emit(seed: int = DEFAULT_SEED) -> Iterator[CanonicalRecord]:
    return compose(
        SCENARIO_ID, seed,
        feed_calls=[
            (bom_flood_gauge.emit, {"jurisdiction": "vic", "count": 5}),
            (bom_severe_weather_warning.emit, {"jurisdiction": "vic", "count": 3}),
            (utility_outage.emit, {"jurisdiction": "vic", "count": 4}),
        ],
    )


__all__ = ["DEFAULT_SEED", "DOMAIN_GROUP", "PARTICIPATING_FEEDS",
           "PARTICIPATING_PERSONAS", "SCENARIO_ID", "emit"]
