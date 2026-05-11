"""T008 — schema contract test: risk-register.

Citations: FR-009, FR-010, FR-011, CHK010.
"""

from __future__ import annotations

from typing import Any


def _row(category: str, idx: int, manual: bool = False) -> dict[str, Any]:
    return {
        "id": f"RISK-TEST-{idx:03d}",
        "title": f"Test risk {idx}",
        "category": category,
        "description": "Test description",
        "likelihood": 3,
        "consequence": 3,
        "inherent_score": 9,
        "treatment": "Test treatment",
        "owner": "Test Owner",
        "residual_likelihood": 2,
        "residual_consequence": 2,
        "residual_score": 4,
        "next_review_date": "2027-01-01",
        "back_citations": [{"kind": "spec", "ref": "specs/037-capstone-evidence-pack/spec.md"}],
        "provenance": {
            "tag": "manual" if manual else "automated",
            "source": "test",
            "evidence_status": "Validated",
            **({"owner": "Test Owner", "review_cadence": "quarterly", "automation_target": "none"} if manual else {}),
        },
    }


def test_minimal_valid_risk_register_passes(risk_register_schema, base_metadata, validator_factory):
    """All 6 categories represented, all schema constraints satisfied."""
    categories = ["Platform", "AI", "Operational", "Jurisdictional", "Data", "Supply-chain"]
    rows = [_row(cat, i + 1) for i, cat in enumerate(categories)]
    base_metadata["total_row_count"] = len(rows)
    artefact = {
        "artefact_id": "risk_register",
        "schema_version": "1.0.0",
        "publication_id": "00000000-0000-0000-0000-000000000001",
        "published_at_utc": "2026-05-11T00:00:00Z",
        "published_by": "test",
        "metadata": base_metadata,
        "rows": rows,
    }
    validator = validator_factory(risk_register_schema)
    errors = list(validator.iter_errors(artefact))
    assert not errors, f"Unexpected schema errors: {errors}"


def test_invalid_risk_register_missing_required_field_fails(risk_register_schema, base_metadata, validator_factory):
    row = _row("Platform", 1)
    row.pop("treatment")  # required
    artefact = {
        "artefact_id": "risk_register",
        "schema_version": "1.0.0",
        "publication_id": "00000000-0000-0000-0000-000000000002",
        "published_at_utc": "2026-05-11T00:00:00Z",
        "published_by": "test",
        "metadata": base_metadata,
        "rows": [row],
    }
    validator = validator_factory(risk_register_schema)
    errors = list(validator.iter_errors(artefact))
    assert errors, "Schema should reject row missing required field"
