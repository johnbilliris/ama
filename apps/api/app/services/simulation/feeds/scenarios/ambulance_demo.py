"""Spec-039 T133 — ambulance demo scenario (FR-061, SC-008).

Mass-casualty triage with CAD feed, EPA air quality alerts and severe
weather context — exercises Ambulance VIC, NSW Ambulance and RFDS.
"""

from __future__ import annotations

from collections.abc import Iterator

from .. import ambulance_cad, bom_severe_weather_warning, epa_pm25
from .._models import CanonicalRecord
from ._base import compose

SCENARIO_ID = "demo-ambulance-v1"
DOMAIN_GROUP = "ambulance"
DEFAULT_SEED = 42
PARTICIPATING_PERSONAS = (
    "av", "nsw-ambulance", "rfds", "saas",
    "incident-commander",
)
PARTICIPATING_FEEDS = (
    ambulance_cad.SOURCE_SHAPE,
    epa_pm25.SOURCE_SHAPE,
    bom_severe_weather_warning.SOURCE_SHAPE,
)


def emit(seed: int = DEFAULT_SEED) -> Iterator[CanonicalRecord]:
    return compose(
        SCENARIO_ID, seed,
        feed_calls=[
            (ambulance_cad.emit, {"jurisdiction": "vic", "count": 5}),
            (epa_pm25.emit, {"jurisdiction": "vic", "count": 3}),
            (bom_severe_weather_warning.emit, {"jurisdiction": "vic", "count": 3}),
        ],
    )


__all__ = ["DEFAULT_SEED", "DOMAIN_GROUP", "PARTICIPATING_FEEDS",
           "PARTICIPATING_PERSONAS", "SCENARIO_ID", "emit"]
