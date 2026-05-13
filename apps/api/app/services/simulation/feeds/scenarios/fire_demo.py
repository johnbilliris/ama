"""Spec-039 T131 — fire demo scenario (FR-061, SC-008).

NSW Black-Summer-shaped bushfire progression: BoM fire weather + severe
weather warning + sensor telemetry chain. Fictitious — no live BoM
endpoints or jurisdictional product IDs.
"""

from __future__ import annotations

from collections.abc import Iterator

from .. import bom_fire_weather_fdi, bom_severe_weather_warning, sensor_telemetry
from .._models import CanonicalRecord
from ._base import compose

SCENARIO_ID = "demo-fire-v1"
DOMAIN_GROUP = "fire"
DEFAULT_SEED = 42
PARTICIPATING_PERSONAS = (
    "nsw-rfs",
    "frnsw",
    "cfa-vic",
    "incident-commander",
    "operations-officer",
)
PARTICIPATING_FEEDS = (
    bom_fire_weather_fdi.SOURCE_SHAPE,
    bom_severe_weather_warning.SOURCE_SHAPE,
    sensor_telemetry.SOURCE_SHAPE,
)


def emit(seed: int = DEFAULT_SEED) -> Iterator[CanonicalRecord]:
    return compose(
        SCENARIO_ID,
        seed,
        feed_calls=[
            (bom_fire_weather_fdi.emit, {"jurisdiction": "nsw", "count": 5}),
            (bom_severe_weather_warning.emit, {"jurisdiction": "nsw", "count": 3}),
            (sensor_telemetry.emit, {"jurisdiction": "nsw", "count": 4}),
        ],
    )


__all__ = ["DEFAULT_SEED", "DOMAIN_GROUP", "PARTICIPATING_FEEDS", "PARTICIPATING_PERSONAS", "SCENARIO_ID", "emit"]
