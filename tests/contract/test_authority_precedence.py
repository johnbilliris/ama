"""T174 — Contract test for FR-RAG-AG-04 + FR-RAG-AC-01 authority precedence
(SC-015; ADR-13; Plan §F-A3.6).

Validates the authority-precedence golden-set cohort and the chunk-metadata
schema together. The retrieval-time behaviour (≥95% Commonwealth-first on
ACT national-institution queries) is measured by T220 / F-A10 once the
corpus rebuild lands; this test asserts the **contract** today:

* The fixture has at least 4 ``authority_precedence`` entries covering
  Parliament House, Defence, embassies, and AIATSIS (national institutions).
* Every entry's ``expected_authority_level`` matches a schema enum value.
* Every Commonwealth entry pairs ``expected_precedence_rank: 1``.
* At least one ``state-territory`` entry exists in ACT (proves the
  contrast — Belconnen residential queries should NOT elevate Commonwealth).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
GOLDEN_SET_PATH = ROOT / "tests" / "fixtures" / "golden-set-v1.json"
SCHEMA_PATH = ROOT / "specs" / "036-foundry-rag-grounding" / "contracts" / "chunk-metadata.schema.json"


@pytest.fixture(scope="module")
def golden_set() -> dict:
    return json.loads(GOLDEN_SET_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _precedence_entries(golden: dict) -> list[dict]:
    return [e for e in golden["entries"] if e.get("scenario") == "authority_precedence"]


def test_at_least_four_precedence_entries(golden_set: dict) -> None:
    entries = _precedence_entries(golden_set)
    assert len(entries) >= 4, (
        f"authority-precedence cohort too small: {len(entries)} < 4. "
        "Plan §F-A3.6 targets ≥20; the F-A1+A3 commit seeds 4 covering "
        "Parliament/Defence/embassies/AIATSIS; T220 consolidates to 20+."
    )


def test_authority_level_matches_schema(golden_set: dict, schema: dict) -> None:
    enum_vals = schema["properties"]["authority_level"]["enum"]
    for entry in _precedence_entries(golden_set):
        level = entry["expected_authority_level"]
        assert level in enum_vals, (
            f"entry {entry['id']!r} expected_authority_level={level!r} "
            f"not in schema enum {enum_vals}"
        )


def test_precedence_rank_within_bounds(golden_set: dict, schema: dict) -> None:
    bounds = schema["properties"]["precedence_rank"]
    minimum, maximum = bounds["minimum"], bounds["maximum"]
    for entry in _precedence_entries(golden_set):
        rank = entry["expected_precedence_rank"]
        assert minimum <= rank <= maximum, (
            f"entry {entry['id']!r} precedence_rank={rank} outside "
            f"[{minimum}, {maximum}]"
        )


def test_commonwealth_entries_rank_first(golden_set: dict) -> None:
    """All ``commonwealth``-level entries MUST carry ``precedence_rank == 1``."""
    for entry in _precedence_entries(golden_set):
        if entry["expected_authority_level"] == "commonwealth":
            assert entry["expected_precedence_rank"] == 1, (
                f"entry {entry['id']!r} authority_level=commonwealth but "
                f"precedence_rank={entry['expected_precedence_rank']} (must be 1 "
                "per ADR-13 + FR-RAG-AC-01)."
            )


def test_act_state_territory_contrast_present(golden_set: dict) -> None:
    """At least one ACT ``state-territory`` entry — proves that Commonwealth
    elevation only applies to national-institution queries, not blanket ACT."""
    contrast_present = any(
        e["jurisdiction"] == "act" and e["expected_authority_level"] == "state-territory"
        for e in _precedence_entries(golden_set)
    )
    assert contrast_present, (
        "missing ACT state-territory entry. Without a contrast case the "
        "cohort cannot detect false-positive elevation."
    )


def test_national_institution_coverage(golden_set: dict) -> None:
    """The Commonwealth cohort MUST mention Parliament, Defence, embassies, AIATSIS."""
    entries = _precedence_entries(golden_set)
    blob = " ".join(e["query"] for e in entries).lower()
    for keyword in ("parliament", "defence", "yarralumla", "aiatsis"):
        assert keyword in blob, (
            f"authority-precedence cohort missing coverage of {keyword!r} "
            "(Plan §F-A3.6 requires Parliament/Defence/embassies/AIATSIS)."
        )
