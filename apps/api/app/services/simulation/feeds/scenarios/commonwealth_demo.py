"""Spec-039 T136 — commonwealth demo scenario (FR-061, SC-008).

NEMA + ADF DACC + BoM cyclone-track composition. Drives the national
coordination hand-off.
"""

from __future__ import annotations

from collections.abc import Iterator

from .. import bom_cyclone_track, bom_severe_weather_warning, sensor_telemetry
from .._models import CanonicalRecord
from ._base import compose

SCENARIO_ID = "demo-commonwealth-v1"
DOMAIN_GROUP = "commonwealth"
DEFAULT_SEED = 42
PARTICIPATING_PERSONAS = (
    "nema", "adf", "bom-national", "ga-national", "arc",
)
PARTICIPATING_FEEDS = (
    bom_cyclone_track.SOURCE_SHAPE,
    bom_severe_weather_warning.SOURCE_SHAPE,
    sensor_telemetry.SOURCE_SHAPE,
)


def emit(seed: int = DEFAULT_SEED) -> Iterator[CanonicalRecord]:
    return compose(
        SCENARIO_ID, seed,
        feed_calls=[
            (bom_cyclone_track.emit, {"jurisdiction": "qld", "count": 5}),
            (bom_severe_weather_warning.emit, {"jurisdiction": "qld", "count": 3}),
            (sensor_telemetry.emit, {"jurisdiction": "nt", "count": 4}),
        ],
    )


__all__ = ["DEFAULT_SEED", "DOMAIN_GROUP", "PARTICIPATING_FEEDS",
           "PARTICIPATING_PERSONAS", "SCENARIO_ID", "emit"]
