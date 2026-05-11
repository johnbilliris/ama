"""T009 — schema contract test: adoption-roadmap.

Citations: FR-009, FR-015, FR-016, FR-017, FR-018, CHK020.
"""

from __future__ import annotations

import pytest


def _wave(wave_id: str, jurisdictions, cohort: str = "state-lead"):
    return {
        "wave_id": wave_id,
        "cohort": cohort,
        "jurisdictions": jurisdictions,
        "lead_agency": {j: f"Lead-{j}" for j in jurisdictions},
        "readiness_gates": ["Spec-001 complete"],
        "training_exercise_cadence": {
            "frequency": "quarterly",
            "cite": [{"kind": "spec", "ref": "specs/024-simulation-control-chat/spec.md"}],
        },
        "change_management_artefacts": ["Comms plan"],
        "decommission_rollback_criteria": [
            "Preserve life-safety defaults; degrade to manual without data loss"
        ],
        "back_citations": [{"kind": "spec", "ref": "specs/037-capstone-evidence-pack/spec.md"}],
        "provenance": {"tag": "automated", "source": "test", "evidence_status": "Validated"},
    }


def test_minimal_valid_adoption_roadmap_passes(
    adoption_roadmap_schema, base_metadata, validator_factory
):
    waves = [
        _wave("WAVE-01", ["NSW", "VIC", "QLD"]),
        _wave("WAVE-02", ["WA", "SA", "TAS"]),
        _wave("WAVE-03", ["ACT", "NT"]),
        _wave("WAVE-04", ["Commonwealth"], cohort="commonwealth"),
    ]
    base_metadata["total_row_count"] = len(waves)
    artefact = {
        "artefact_id": "adoption_roadmap",
        "schema_version": "1.0.0",
        "publication_id": "00000000-0000-0000-0000-000000000003",
        "published_at_utc": "2026-05-11T00:00:00Z",
        "published_by": "test",
        "metadata": base_metadata,
        "rows": waves,
    }
    validator = validator_factory(adoption_roadmap_schema)
    errors = list(validator.iter_errors(artefact))
    assert not errors, f"Unexpected schema errors: {errors}"


def test_invalid_adoption_roadmap_missing_rollback_fails(
    adoption_roadmap_schema, base_metadata, validator_factory
):
    wave = _wave("WAVE-01", ["NSW"])
    wave.pop("decommission_rollback_criteria")
    artefact = {
        "artefact_id": "adoption_roadmap",
        "schema_version": "1.0.0",
        "publication_id": "00000000-0000-0000-0000-000000000004",
        "published_at_utc": "2026-05-11T00:00:00Z",
        "published_by": "test",
        "metadata": base_metadata,
        "rows": [wave],
    }
    validator = validator_factory(adoption_roadmap_schema)
    errors = list(validator.iter_errors(artefact))
    assert errors, "Schema should reject wave missing rollback criteria"
