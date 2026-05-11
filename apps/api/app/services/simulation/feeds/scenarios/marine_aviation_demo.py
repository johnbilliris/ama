"""Spec-038 T135 — marine/aviation demo scenario (FR-061, SC-008, US4).

RFDS aeromedical retrieval + Surf Life Saving + AMSA tsunami threat —
deliberately covers the user-flagged silent-gap personas.
"""

from __future__ import annotations

from collections.abc import Iterator

from .. import ambulance_cad, ga_tsunami_threat, sensor_telemetry
from .._models import CanonicalRecord
from ._base import compose

SCENARIO_ID = "demo-marine-aviation-v1"
DOMAIN_GROUP = "marine-aviation"
DEFAULT_SEED = 42
PARTICIPATING_PERSONAS = (
    "rfds", "surf-lifesaving", "mrnsw", "abf", "asa",
)
PARTICIPATING_FEEDS = (
    ga_tsunami_threat.SOURCE_SHAPE,
    ambulance_cad.SOURCE_SHAPE,
    sensor_telemetry.SOURCE_SHAPE,
)


def emit(seed: int = DEFAULT_SEED) -> Iterator[CanonicalRecord]:
    return compose(
        SCENARIO_ID, seed,
        feed_calls=[
            (ga_tsunami_threat.emit, {"jurisdiction": "nsw", "count": 4}),
            (ambulance_cad.emit, {"jurisdiction": "nsw", "count": 3}),
            (sensor_telemetry.emit, {"jurisdiction": "nsw", "count": 4}),
        ],
    )


__all__ = ["DEFAULT_SEED", "DOMAIN_GROUP", "PARTICIPATING_FEEDS",
           "PARTICIPATING_PERSONAS", "SCENARIO_ID", "emit"]
