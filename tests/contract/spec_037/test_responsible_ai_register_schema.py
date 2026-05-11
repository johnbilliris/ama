"""T011 — schema contract test: responsible-ai-register.

Citations: FR-009, FR-024, FR-025, FR-026, FR-027, CHK040.
"""

from __future__ import annotations


def _cell(posture: str = "compliant"):
    cell = {
        "posture": posture,
        "summary": "Test summary",
        "evidence": [
            {"kind": "spec", "ref": "specs/030-llm-eval-framework/spec.md"}
        ],
    }
    if posture == "not-applicable":
        cell["na_justification"] = "Genuinely not applicable for this component"
    return cell


def _frameworks():
    return {
        "au_ai_ethics_8_principles": _cell(),
        "iso_42001": _cell(),
        "iso_23894": _cell(),
        "nist_ai_rmf": {
            "govern": _cell(),
            "map": _cell(),
            "measure": _cell(),
            "manage": _cell(),
        },
    }


def _principles():
    return {
        k: _cell()
        for k in (
            "human_oversight",
            "fairness",
            "accountability",
            "transparency",
            "privacy",
            "safety",
            "contestability",
            "reliability",
        )
    }


def _row():
    return {
        "component_id": "agent.communication",
        "component_kind": "sub-agent",
        "spec_refs": [{"kind": "spec", "ref": "specs/008-communication-agent/spec.md"}],
        "frameworks": _frameworks(),
        "principles": _principles(),
        "eval_evidence_refs": [
            {"kind": "spec", "ref": "specs/030-llm-eval-framework/spec.md"}
        ],
        "provenance": {"tag": "manual", "source": "review", "evidence_status": "Validated",
                       "owner": "Compliance Auditor", "review_cadence": "quarterly",
                       "automation_target": "none"},
    }


def test_minimal_valid_rai_register_passes(rai_register_schema, base_metadata, validator_factory):
    artefact = {
        "artefact_id": "rai_register",
        "schema_version": "1.0.0",
        "publication_id": "00000000-0000-0000-0000-000000000007",
        "published_at_utc": "2026-05-11T00:00:00Z",
        "published_by": "test",
        "metadata": base_metadata,
        "rows": [_row()],
    }
    validator = validator_factory(rai_register_schema)
    errors = list(validator.iter_errors(artefact))
    assert not errors, f"Unexpected: {errors}"


def test_invalid_rai_register_blank_principle_fails(
    rai_register_schema, base_metadata, validator_factory
):
    row = _row()
    del row["principles"]["fairness"]  # required field
    artefact = {
        "artefact_id": "rai_register",
        "schema_version": "1.0.0",
        "publication_id": "00000000-0000-0000-0000-000000000008",
        "published_at_utc": "2026-05-11T00:00:00Z",
        "published_by": "test",
        "metadata": base_metadata,
        "rows": [row],
    }
    validator = validator_factory(rai_register_schema)
    errors = list(validator.iter_errors(artefact))
    assert errors, "Schema must reject blank principle cells (FR-027)"
