"""T173 — Contract test for FR-RAG-AG-04 agency disambiguation
(SC-013; ADR-13; Plan §F-A1.5).

Validates that the chunk-metadata schema + golden-set fixture together
exercise the agency-disambiguation surface. The full retrieval-time
behaviour (≥95% correct agency classification on 50-query persona-driven
set) is measured by T220 / F-A10 once the corpus rebuild lands; this test
asserts the **contract** today:

* The fixture has at least 5 ``agency_disambiguation`` entries.
* Every entry pairs ``expected_agency`` + ``expected_agency_role``.
* ``expected_agency_role`` is one of the schema-permitted enum values.
* No two entries within the same jurisdiction share the same
  (agency, agency_role) — would mean the disambiguation has nothing to do.
* The chunk-metadata schema enumerates the same agency-role values.
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


def _agency_disambig_entries(golden: dict) -> list[dict]:
    return [e for e in golden["entries"] if e.get("scenario") == "agency_disambiguation"]


def test_at_least_five_agency_disambiguation_entries(golden_set: dict) -> None:
    entries = _agency_disambig_entries(golden_set)
    assert len(entries) >= 5, (
        f"agency-disambiguation cohort too small: {len(entries)} < 5. "
        "Plan §F-A1.5 requires ≥20 entries; the F-A1+A3 commit seeds 5; "
        "T220 (F-A10) consolidates to 20+."
    )


def test_every_entry_pairs_agency_and_role(golden_set: dict) -> None:
    for entry in _agency_disambig_entries(golden_set):
        assert "expected_agency" in entry, f"missing expected_agency: {entry['id']}"
        assert "expected_agency_role" in entry, f"missing expected_agency_role: {entry['id']}"


def test_role_values_match_schema_enum(golden_set: dict, schema: dict) -> None:
    role_enum = schema["properties"]["agency_role"]["enum"]
    for entry in _agency_disambig_entries(golden_set):
        role = entry["expected_agency_role"]
        assert role in role_enum, f"entry {entry['id']!r} expected_agency_role={role!r} not in schema enum {role_enum}"


def test_no_dup_agency_role_within_jurisdiction(golden_set: dict) -> None:
    seen: dict[tuple[str, str, str], str] = {}
    for entry in _agency_disambig_entries(golden_set):
        key = (entry["jurisdiction"], entry["expected_agency"], entry["expected_agency_role"])
        if key in seen:
            pytest.fail(
                f"duplicate ({key[0]}, {key[1]}, {key[2]}) — entries "
                f"{seen[key]!r} and {entry['id']!r} both target the same agency. "
                "Disambiguation cohort must be discriminative."
            )
        seen[key] = entry["id"]


def test_schema_enumerates_required_role_values(schema: dict) -> None:
    """Schema MUST list the canonical agency_role values used by the fixture."""
    role_enum = schema["properties"]["agency_role"]["enum"]
    required = {"urban-fire", "rural-fire", "ses", "combined"}
    missing = required - set(role_enum)
    assert not missing, f"schema enum missing canonical roles: {missing}"
