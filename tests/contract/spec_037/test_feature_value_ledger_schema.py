"""T012 — schema contract test: feature-value-ledger.

Citations: FR-009, FR-030, FR-031, FR-032, FR-033, CHK050.
"""

from __future__ import annotations


def _row(spec_id: str, contributing: bool = True):
    row = {
        "spec_id": spec_id,
        "spec_title": f"Spec {spec_id}",
        "tag": "capstone-contributing" if contributing else "delivery-hygiene",
        "cross_link_to_metric_trace": {
            "kind": "governance_hub",
            "ref": "specs/shared/capstone-metric-trace.md",
        },
        "provenance": {
            "tag": "manual",
            "source": "review",
            "evidence_status": "Validated",
            "owner": "Capstone Reviewer",
            "review_cadence": "quarterly",
            "automation_target": "none",
        },
    }
    if contributing:
        row["capstone_metrics"] = [
            {"metric_id": "lives-saved", "magnitude": 0.1, "direction": "+", "residual_gap_to_target": 0.0}
        ]
    return row


def _tradeoff(adr_id: str):
    return {
        "adr_id": adr_id,
        "adr_path": f"docs/aidr/decisions/{adr_id.lower()}.md",
        "bounding_features": ["001-disaster-response-hub"],
        "alternatives_considered": ["Alt A", "Alt B"],
        "rationale": "Test rationale",
        "synthesised_tension": "none",
        "provenance": {
            "tag": "manual",
            "source": "review",
            "evidence_status": "Validated",
            "owner": "Architect",
            "review_cadence": "quarterly",
            "automation_target": "none",
        },
    }


def test_minimal_valid_feature_value_ledger_passes(feature_value_schema, base_metadata, validator_factory):
    artefact = {
        "artefact_id": "feature_value_ledger",
        "schema_version": "1.0.0",
        "publication_id": "00000000-0000-0000-0000-000000000009",
        "published_at_utc": "2026-05-11T00:00:00Z",
        "published_by": "test",
        "metadata": base_metadata,
        "rows": [_row("001-disaster-response-hub")],
        "tradeoffs": [_tradeoff("ADR-036-001")],
    }
    validator = validator_factory(feature_value_schema)
    errors = list(validator.iter_errors(artefact))
    assert not errors, f"Unexpected: {errors}"


def test_contributing_row_missing_metrics_fails(feature_value_schema, base_metadata, validator_factory):
    row = _row("001-disaster-response-hub")
    row.pop("capstone_metrics")  # required for capstone-contributing
    artefact = {
        "artefact_id": "feature_value_ledger",
        "schema_version": "1.0.0",
        "publication_id": "00000000-0000-0000-0000-000000000010",
        "published_at_utc": "2026-05-11T00:00:00Z",
        "published_by": "test",
        "metadata": base_metadata,
        "rows": [row],
        "tradeoffs": [_tradeoff("ADR-036-001")],
    }
    validator = validator_factory(feature_value_schema)
    errors = list(validator.iter_errors(artefact))
    assert errors, "Schema must require capstone_metrics for contributing rows"
