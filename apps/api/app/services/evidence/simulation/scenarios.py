"""Pillar C — Canonical scenario registry (T-C09, FR-011, CHK022).

String registry only — actual scenario assets owned by spec 007.
"""

from __future__ import annotations

from typing import Literal

ScenarioId = Literal[
    "bushfire",
    "flood",
    "cyclone",
    "urban_fire",
    "mass_casualty",
    "hazmat",
    "marine_sar",
]

SCENARIOS: tuple[ScenarioId, ...] = (
    "bushfire",
    "flood",
    "cyclone",
    "urban_fire",
    "mass_casualty",
    "hazmat",
    "marine_sar",
)
