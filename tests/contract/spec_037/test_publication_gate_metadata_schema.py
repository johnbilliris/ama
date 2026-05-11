"""T013 — schema contract test: publication-gate-metadata.

Citations: FR-009, FR-037, FR-038, SC-011, CHK060.
"""

from __future__ import annotations


def test_under_cap_no_signoff_passes(publication_gate_schema, validator_factory):
    meta = {
        "manual_row_count": 2,
        "total_row_count": 10,
        "manual_row_ratio": 0.2,
        "link_check_status": "passed",
        "last_gate_run_utc": "2026-05-11T00:00:00Z",
    }
    validator = validator_factory(publication_gate_schema)
    errors = list(validator.iter_errors(meta))
    assert not errors, f"Unexpected: {errors}"


def test_over_cap_with_complete_signoff_passes(publication_gate_schema, validator_factory):
    meta = {
        "manual_row_count": 8,
        "total_row_count": 10,
        "manual_row_ratio": 0.8,
        "link_check_status": "passed",
        "last_gate_run_utc": "2026-05-11T00:00:00Z",
        "auditor_signoff": {
            "name": "Jane Doe",
            "role": "Compliance Auditor",
            "signoff_date_utc": "2026-05-11T00:00:00Z",
            "basis": "ISO/IEC 23894 §7.4 risk evaluation under uncertainty",
        },
    }
    validator = validator_factory(publication_gate_schema)
    errors = list(validator.iter_errors(meta))
    assert not errors, f"Unexpected: {errors}"


def test_over_cap_missing_signoff_fails(publication_gate_schema, validator_factory):
    meta = {
        "manual_row_count": 8,
        "total_row_count": 10,
        "manual_row_ratio": 0.8,
        "link_check_status": "passed",
        "last_gate_run_utc": "2026-05-11T00:00:00Z",
    }
    validator = validator_factory(publication_gate_schema)
    errors = list(validator.iter_errors(meta))
    assert errors, "Schema must require auditor_signoff when ratio > 0.5"


def test_ratio_out_of_range_fails(publication_gate_schema, validator_factory):
    meta = {
        "manual_row_count": 5,
        "total_row_count": 10,
        "manual_row_ratio": 1.5,
        "link_check_status": "passed",
        "last_gate_run_utc": "2026-05-11T00:00:00Z",
    }
    validator = validator_factory(publication_gate_schema)
    errors = list(validator.iter_errors(meta))
    assert errors, "manual_row_ratio must be in [0, 1]"
