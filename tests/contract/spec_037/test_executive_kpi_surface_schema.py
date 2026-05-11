"""T010 — schema contract test: executive-kpi-surface.

Citations: FR-009, FR-019, FR-020, FR-021, CHK030.
"""

from __future__ import annotations

CRITERIA = [
    "lives-saved",
    "response-time",
    "evacuation-lead-time",
    "logistics-efficiency",
    "economic-loss-reduction",
]


def _kpi(kpi_id: str, criterion: str, kind: str):
    return {
        "kpi_id": kpi_id,
        "capstone_criterion": criterion,
        "kind": kind,
        "name": f"KPI {kpi_id}",
        "owner": "Executive Leader",
        "refresh_cadence": "daily",
        "target_value": 100.0,
        "target_unit": "units",
        "threshold_band": {"green": ">=90", "amber": "70-89", "red": "<70"},
        "source_of_truth": {"kind": "telemetry_sink", "ref": "appinsights://test"},
        "consolidates": ["docs/governance-dashboard.md"],
        "back_citations": [{"kind": "spec", "ref": "specs/015-performance-benchmarks/spec.md"}],
        "provenance": {"tag": "automated", "source": "appinsights", "evidence_status": "Validated"},
    }


def test_minimal_valid_executive_kpi_surface_passes(executive_kpi_schema, base_metadata, validator_factory):
    rows = []
    idx = 1
    for crit in CRITERIA:
        rows.append(_kpi(f"KPI-CAP-{idx:03d}", crit, "leading"))
        idx += 1
        rows.append(_kpi(f"KPI-CAP-{idx:03d}", crit, "lagging"))
        idx += 1
    base_metadata["total_row_count"] = len(rows)
    artefact = {
        "artefact_id": "executive_kpi_surface",
        "schema_version": "1.0.0",
        "publication_id": "00000000-0000-0000-0000-000000000005",
        "published_at_utc": "2026-05-11T00:00:00Z",
        "published_by": "test",
        "metadata": base_metadata,
        "rows": rows,
    }
    validator = validator_factory(executive_kpi_schema)
    errors = list(validator.iter_errors(artefact))
    assert not errors, f"Unexpected: {errors}"


def test_invalid_kpi_surface_too_few_rows_fails(executive_kpi_schema, base_metadata, validator_factory):
    artefact = {
        "artefact_id": "executive_kpi_surface",
        "schema_version": "1.0.0",
        "publication_id": "00000000-0000-0000-0000-000000000006",
        "published_at_utc": "2026-05-11T00:00:00Z",
        "published_by": "test",
        "metadata": base_metadata,
        "rows": [_kpi("KPI-CAP-001", "lives-saved", "leading")],  # only 1 row, need ≥10
    }
    validator = validator_factory(executive_kpi_schema)
    errors = list(validator.iter_errors(artefact))
    assert errors, "Schema must enforce minItems=10"
