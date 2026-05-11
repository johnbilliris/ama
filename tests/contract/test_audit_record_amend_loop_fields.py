"""T156 — Schema-mirror test for the F-A5 audit-shape extension (FR-RAG-AG-02 ext;
Cluster A5; ADR-14; Plan §F-A5.1).

Asserts the post-extension ``packages/schemas/spec_036/audit-record-llm-call.json``
exposes the 8 new optional fields landed by the F-A5 amend-loop and that the
mirror is byte-equal with the spec contract.

Fields (Pass 2 Q-P2-01 additive-nullable migration):

1. ``operator_override_rationale``       — string|null (max 2048 chars)
2. ``approval_workflow_state``           — enum {pending, approved, rejected, null}
3. ``approval_authority``                — string|null (Entra ID)
4. ``downgrade_justification``           — string|null
5. ``retrieval_index_name``              — string|null (corpus-vN or corpus-test-...)
6. ``field_coordinator_offline_decision``— string|null
7. ``conflict_group_id``                 — string|null (UUID)
8. ``precedence_tiebreak_applied[]``     — array of enum tiers

All fields are nullable to keep the migration purely additive — legacy rows
written before F-A5 land remain valid (R18 mitigation).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SPEC_PATH = ROOT / "specs" / "036-foundry-rag-grounding" / "contracts" / "audit-record-llm-call.json"
MIRROR_PATH = ROOT / "packages" / "schemas" / "spec_036" / "audit-record-llm-call.json"

NEW_FIELDS = (
    "operator_override_rationale",
    "approval_workflow_state",
    "approval_authority",
    "downgrade_justification",
    "retrieval_index_name",
    "field_coordinator_offline_decision",
    "conflict_group_id",
    "precedence_tiebreak_applied",
)


@pytest.fixture(scope="module")
def schema() -> dict:
    return json.loads(MIRROR_PATH.read_text(encoding="utf-8"))


def test_spec_and_mirror_byte_equal() -> None:
    """Mirror MUST byte-equal the spec contract (T005 pattern, extended for F-A5)."""
    assert SPEC_PATH.read_bytes() == MIRROR_PATH.read_bytes(), (
        "audit-record-llm-call.json mirror drift; re-mirror spec → packages/schemas/spec_036/."
    )


@pytest.mark.parametrize("field_name", NEW_FIELDS)
def test_new_field_present_in_schema(schema: dict, field_name: str) -> None:
    """Each F-A5 NEW field MUST appear in the schema's properties block."""
    assert field_name in schema["properties"], f"FR-RAG-AG-02 ext — schema missing F-A5 field {field_name!r}"


@pytest.mark.parametrize("field_name", NEW_FIELDS)
def test_new_field_is_nullable(schema: dict, field_name: str) -> None:
    """Every F-A5 field is nullable (additive-nullable per Pass 2 Q-P2-01)."""
    prop = schema["properties"][field_name]
    types = prop.get("type")
    if isinstance(types, list):
        assert "null" in types, f"{field_name!r} type={types!r} must include 'null'"
    elif field_name == "precedence_tiebreak_applied":
        # Array fields are 'nullable' by virtue of being absent (not required).
        assert types == "array", f"{field_name!r} expected array type, got {types!r}"
    else:
        assert types == "array" or "null" in (types or ""), f"{field_name!r} expected nullable type, got {types!r}"


def test_no_new_field_in_required_block(schema: dict) -> None:
    """None of the 8 new fields are unconditionally required — they are
    additive-nullable. Conditional required is enforced by the allOf invariants
    (e.g. retrieval_index_name when rag_used == true)."""
    required = set(schema.get("required", []))
    for field_name in NEW_FIELDS:
        assert field_name not in required, (
            f"F-A5 invariant: {field_name!r} MUST NOT be in the unconditional required[] block"
        )


def test_approval_workflow_state_enum(schema: dict) -> None:
    enum = schema["properties"]["approval_workflow_state"]["enum"]
    assert set(enum) == {"pending", "approved", "rejected", None}


def test_precedence_tiebreak_applied_item_enum(schema: dict) -> None:
    item_enum = schema["properties"]["precedence_tiebreak_applied"]["items"]["enum"]
    assert set(item_enum) == {"recency", "licence_mode", "embedding_model_id", "chunk_id"}


def test_invariant_retrieval_index_name_required_when_rag_used(schema: dict) -> None:
    """Invariant 6 (ADR-16): rag_used == true → retrieval_index_name required."""
    invariants = schema.get("allOf") or []
    found = False
    for inv in invariants:
        if inv.get("if", {}).get("properties", {}).get("rag_used", {}).get(
            "const"
        ) is True and "retrieval_index_name" in (inv.get("then", {}).get("required") or []):
            found = True
            break
    assert found, "ADR-16 invariant: rag_used → retrieval_index_name required, missing from allOf"


def test_invariant_approval_authority_required_when_state_terminal(schema: dict) -> None:
    """Invariant 7 (ADR-14): approval_workflow_state in (approved, rejected) →
    approval_authority required."""
    invariants = schema.get("allOf") or []
    found = False
    for inv in invariants:
        cond = inv.get("if", {}).get("properties", {}).get("approval_workflow_state", {})
        if cond.get("enum") == ["approved", "rejected"]:
            then = inv.get("then", {})
            if "approval_authority" in (then.get("required") or []):
                found = True
                break
    assert found, "ADR-14 invariant: terminal state → approval_authority required, missing from allOf"
