"""Spec-039 T103 — every demo scenario participates ≥3 personas, ≥2 feeds.

Imports each scenario module and asserts the contract surface plus a
live ``emit()`` call returns at least one record per feed shape.
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))
_API = _REPO / "apps" / "api"
if str(_API) not in sys.path:
    sys.path.insert(0, str(_API))

DEMO_SCENARIOS = [
    "operational_demo",
    "fire_demo",
    "police_demo",
    "ambulance_demo",
    "ses_demo",
    "marine_aviation_demo",
    "commonwealth_demo",
    "cross_sector_demo",
]


@pytest.mark.parametrize("name", DEMO_SCENARIOS)
def test_demo_scenario_contract(name: str) -> None:
    mod = importlib.import_module(f"apps.api.app.services.simulation.feeds.scenarios.{name}")
    assert isinstance(mod.SCENARIO_ID, str) and mod.SCENARIO_ID.startswith("demo-")
    assert mod.DOMAIN_GROUP in {
        "operational",
        "fire",
        "police",
        "ambulance",
        "ses",
        "marine-aviation",
        "commonwealth",
        "cross-sector",
    }
    assert isinstance(mod.PARTICIPATING_PERSONAS, tuple)
    assert len(mod.PARTICIPATING_PERSONAS) >= 3, f"{name}: needs ≥3 participating personas (FR-061)"
    assert isinstance(mod.PARTICIPATING_FEEDS, tuple)
    assert len(mod.PARTICIPATING_FEEDS) >= 2, f"{name}: needs ≥2 distinct feed shapes"
    # Live emit must be deterministic and yield records from every feed.
    records = list(mod.emit(seed=42))
    assert records, f"{name}: emit produced no records"
    seen_shapes = {r.source_shape for r in records}
    assert set(mod.PARTICIPATING_FEEDS).issubset(seen_shapes), (
        f"{name}: missing emissions for {set(mod.PARTICIPATING_FEEDS) - seen_shapes}"
    )
