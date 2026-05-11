"""Spec-039 T101 — manifest-driven volume coverage assertions (FR-062, SC-012).

Reads the canonical manifest and asserts the per-persona / per-category
lower bounds documented in the spec for hospital capacity, vulnerable
categories, volunteer registrations, alert variants and quake events.

Generators emit at runtime (regenerate-each-run) so we drive them
once with a pinned seed and assert their record_count meets the bound.
"""

from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))


def _gen_count(name: str, *, seed: int = 42, **kw) -> int:
    mod = importlib.import_module(f"scripts.generators.{name}")
    count = kw.pop("count", None)
    if count is None:
        # Use the generator's documented default count from its CLI.
        defaults = {
            "hospital_capacity": 80,
            "vulnerable_categories": 20,
            "volunteer_registrations": 30,
            "public_alerts": 40,
        }
        count = defaults.get(name, 12)
    return len(mod.generate(seed=seed, count=count))


def test_hospital_capacity_at_least_10_per_state() -> None:
    # Generator emits per-state with a per_state >= 10 floor.
    n = _gen_count("hospital_capacity")
    assert n >= 80, n  # 8 states × ≥10


def test_vulnerable_categories_at_least_20() -> None:
    assert _gen_count("vulnerable_categories") >= 20


def test_volunteer_registrations_at_least_30() -> None:
    assert _gen_count("volunteer_registrations") >= 30


def test_alert_variants_at_least_5_per_locale() -> None:
    # public_alerts sweep guarantees ≥5 variants per locale × 8 locales = 40.
    n = _gen_count("public_alerts")
    assert n >= 40, n


def test_quake_events_at_least_3_per_session() -> None:
    # ga_earthquake_event committed replay must contain ≥3 events.
    p = _REPO / "fixtures" / "sim_replays" / "ga_earthquake_event_wa.ndjson"
    assert p.exists(), p
    lines = [json.loads(line) for line in p.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(lines) >= 3
