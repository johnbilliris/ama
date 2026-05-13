"""Spec-039 T130 — operational demo scenario (FR-061, SC-008).

Composes BoM severe weather + Geoscience earthquake + sensor telemetry
to drive a generic operational rehearsal exercising the SCC duty officer,
incident commander and operations officer chain.
"""

from __future__ import annotations

from collections.abc import Iterator

from .. import bom_severe_weather_warning, ga_earthquake_event, sensor_telemetry
from .._models import CanonicalRecord
from ._base import compose

SCENARIO_ID = "demo-operational-v1"
DOMAIN_GROUP = "operational"
DEFAULT_SEED = 42
PARTICIPATING_PERSONAS = (
    "incident-commander",
    "operations-officer",
    "planning-officer",
    "logistics-officer",
    "executive-leader",
)
PARTICIPATING_FEEDS = (
    bom_severe_weather_warning.SOURCE_SHAPE,
    ga_earthquake_event.SOURCE_SHAPE,
    sensor_telemetry.SOURCE_SHAPE,
)


def emit(seed: int = DEFAULT_SEED) -> Iterator[CanonicalRecord]:
    return compose(
        SCENARIO_ID,
        seed,
        feed_calls=[
            (bom_severe_weather_warning.emit, {"jurisdiction": "nsw", "count": 4}),
            (ga_earthquake_event.emit, {"jurisdiction": "nsw", "count": 3}),
            (sensor_telemetry.emit, {"jurisdiction": "nsw", "count": 5}),
        ],
    )


__all__ = ["DEFAULT_SEED", "DOMAIN_GROUP", "PARTICIPATING_FEEDS", "PARTICIPATING_PERSONAS", "SCENARIO_ID", "emit"]
