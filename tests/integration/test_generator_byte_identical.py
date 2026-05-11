"""Spec-039 T100 — every generator is byte-identical for the same seed.

Parametrises across all 14 deterministic generators under
``scripts/generators/`` and asserts that calling each one twice with the
same seed produces an identical record stream (FR-051, FR-052).
"""

from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

GENERATOR_NAMES = [
    "incidents", "coordination_tasks", "signals", "audit_entries",
    "risk_register", "public_alerts", "evacuee_registrations",
    "missing_persons", "triage_records", "volunteer_registrations",
    "vulnerable_categories", "hospital_capacity", "transport_assets",
    "utility_outages",
]


@pytest.mark.parametrize("name", GENERATOR_NAMES)
def test_generator_byte_identical_same_seed(name: str) -> None:
    mod = importlib.import_module(f"scripts.generators.{name}")
    a = mod.generate(seed=42, count=12)
    b = mod.generate(seed=42, count=12)
    # Compare canonicalised JSON to defeat any incidental dict ordering.
    sa = json.dumps(a, sort_keys=True)
    sb = json.dumps(b, sort_keys=True)
    assert sa == sb, f"{name}: byte drift between two runs with same seed"


@pytest.mark.parametrize("name", GENERATOR_NAMES)
def test_generator_records_are_tagged(name: str) -> None:
    mod = importlib.import_module(f"scripts.generators.{name}")
    records = mod.generate(seed=42, count=4)
    assert records, f"{name}: empty output"
    for r in records:
        assert r["fictitious"] is True
        assert r["residency"] == "AU"
        assert r["pspf"] == "OFFICIAL"
        assert r["licence"] == "CC-BY-4.0"
        assert r["generator_id"] == mod.GENERATOR_ID
        assert r["generator_version"] == mod.GENERATOR_VERSION


def test_all_14_generators_present() -> None:
    assert len(GENERATOR_NAMES) == 14
    gen_dir = _REPO / "scripts" / "generators"
    on_disk = {p.stem for p in gen_dir.glob("*.py") if not p.name.startswith("_")}
    on_disk.discard("__init__")
    assert on_disk == set(GENERATOR_NAMES), (
        f"generators on disk={on_disk}, expected={set(GENERATOR_NAMES)}"
    )
