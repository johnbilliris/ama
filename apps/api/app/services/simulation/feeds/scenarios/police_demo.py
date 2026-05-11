"""Spec-038 T132 — police demo scenario (FR-061, SC-008).

Cross-jurisdictional public-order / evac-compliance scenario combining
traffic road closures with social-chatter signal and severe-weather
context.
"""

from __future__ import annotations

from collections.abc import Iterator

from .. import bom_severe_weather_warning, social_chatter, traffic_road_closure
from .._models import CanonicalRecord
from ._base import compose

SCENARIO_ID = "demo-police-v1"
DOMAIN_GROUP = "police"
DEFAULT_SEED = 42
PARTICIPATING_PERSONAS = (
    "nswpf", "vicpol", "afp-commonwealth",
    "operations-officer", "incident-commander",
)
PARTICIPATING_FEEDS = (
    traffic_road_closure.SOURCE_SHAPE,
    social_chatter.SOURCE_SHAPE,
    bom_severe_weather_warning.SOURCE_SHAPE,
)


def emit(seed: int = DEFAULT_SEED) -> Iterator[CanonicalRecord]:
    return compose(
        SCENARIO_ID, seed,
        feed_calls=[
            (traffic_road_closure.emit, {"jurisdiction": "nsw", "count": 5}),
            (social_chatter.emit, {"jurisdiction": "au", "count": 4}),
            (bom_severe_weather_warning.emit, {"jurisdiction": "nsw", "count": 3}),
        ],
    )


__all__ = ["DEFAULT_SEED", "DOMAIN_GROUP", "PARTICIPATING_FEEDS",
           "PARTICIPATING_PERSONAS", "SCENARIO_ID", "emit"]
