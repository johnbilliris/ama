"""Spec-038 T104 — every persona appears in the manifest (FR-060, SC-001).

Reads the canonical 68-persona inventory from
``tools.lint.build_test_data_manifest.PERSONA_ROSTERS`` and asserts every
ID resolves to ≥1 manifest entry's ``persona_bindings``.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))
_LINT = _REPO / "tools" / "lint"
if str(_LINT) not in sys.path:
    sys.path.insert(0, str(_LINT))

from build_test_data_manifest import PERSONA_ROSTERS  # noqa: E402

MANIFEST = _REPO / "docs" / "test-data" / "manifest.json"


def test_persona_inventory_totals_68() -> None:
    total = sum(len(v) for v in PERSONA_ROSTERS.values())
    assert total == 68, f"expected 68 personas, got {total}: {PERSONA_ROSTERS}"


def test_every_persona_appears_in_manifest() -> None:
    doc = json.loads(MANIFEST.read_text(encoding="utf-8"))
    bound: set[str] = set()
    for e in doc["entries"]:
        bound.update(e.get("persona_bindings", []))
    canonical: set[str] = set()
    for ps in PERSONA_ROSTERS.values():
        canonical.update(ps)
    missing = sorted(canonical - bound)
    assert not missing, (
        f"{len(missing)} personas have zero manifest entries: {missing}"
    )


def test_every_domain_group_has_entries() -> None:
    doc = json.loads(MANIFEST.read_text(encoding="utf-8"))
    groups: set[str] = {e.get("domain_group") for e in doc["entries"]}
    expected = set(PERSONA_ROSTERS.keys())
    assert expected.issubset(groups), f"missing domain groups: {expected - groups}"
