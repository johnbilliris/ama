from __future__ import annotations

import dataclasses
import json
from copy import deepcopy

import pytest

HEX_A = "a" * 64
HEX_B = "b" * 64


def _valid_local_entry() -> dict[str, object]:
    return {
        "id": "installed-extension",
        "fallback_identity": None,
        "source_locations": [".specify/extensions/installed-extension"],
        "name": "Installed extension",
        "description": None,
        "version": "1.0.0",
        "priority": 10,
        "enabled": True,
        "source": {"kind": "local"},
        "evidence": [
            {
                "kind": "local",
                "source_sha256": HEX_A,
                "source_ordinal": 0,
                "record_sha256": HEX_B,
            }
        ],
        "provides": {"commands": 1, "templates": 0, "scripts": 0, "hooks": 0},
        "install_allowed": None,
        "installed": True,
        "installed_version": "1.0.0",
        "available_versions": [],
        "activation_state": "inactive",
        "activation_diagnostic": None,
        "health": {"state": "healthy", "diagnostics": []},
        "conflict": False,
        "conflict_reasons": [],
        "catalog_sources": [],
    }


def test_projection_contract_source_evidence_allowlist_is_closed() -> None:
    from specify_cli.extensions.models import SourceEvidence

    assert {field.name for field in dataclasses.fields(SourceEvidence)} == {
        "kind",
        "source_sha256",
        "source_ordinal",
        "record_sha256",
    }

    prohibited = ("source", "author", "canonical_record", "description", "absolute_path")
    for field_name in prohibited:
        evidence = _valid_local_entry()["evidence"]
        assert isinstance(evidence, list)
        value = evidence[0]
        assert isinstance(value, dict)
        with pytest.raises((TypeError, ValueError)):
            SourceEvidence.from_mapping({**value, field_name: "private"})


def test_projection_contract_sole_serializer_emits_one_top_level_array() -> None:
    from specify_cli.extensions.models import project_entry, serialize_entries

    entry = project_entry(_valid_local_entry())
    encoded = serialize_entries([entry])

    assert encoded.endswith("\n")
    assert json.loads(encoded) == [_valid_local_entry()]
    assert "source_locations" in encoded
    assert "fallback_identity" in encoded


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (lambda row: row["health"].update(state="invalid"), "invalid health requires diagnostics"),
        (lambda row: row.update(conflict=True), "conflict requires reasons"),
        (lambda row: row.update(activation_diagnostic="unexpected"), "activation diagnostic"),
        (lambda row: row["source"].update(kind="catalog"), "catalog source cannot be installed"),
        (lambda row: row["evidence"][0].update(kind="catalog"), "evidence kind"),
        (lambda row: row["source_locations"].append("C:/private/extension"), "project-relative"),
    ],
)
def test_projection_contract_rejects_cross_field_contradictions(mutate: object, message: str) -> None:
    from specify_cli.extensions.models import project_entry

    row = deepcopy(_valid_local_entry())
    assert callable(mutate)
    mutate(row)

    with pytest.raises(ValueError, match=message):
        project_entry(row)


def test_projection_contract_fallback_identity_remains_outside_evidence() -> None:
    from specify_cli.extensions.models import project_entry

    row = _valid_local_entry()
    row.update(id=None, fallback_identity=".specify/extensions/broken", version="unknown")
    row["health"] = {
        "state": "invalid",
        "diagnostics": [
            {
                "code": "missing-stable-id",
                "message": "Stable identifier is missing.",
                "source": ".specify/extensions/broken",
            }
        ],
    }

    entry = project_entry(row)

    assert entry.fallback_identity == ".specify/extensions/broken"
    assert dataclasses.asdict(entry.evidence[0]) == {
        "kind": "local",
        "source_sha256": HEX_A,
        "source_ordinal": 0,
        "record_sha256": HEX_B,
    }


def test_projection_contract_rejects_malformed_nested_shapes() -> None:
    from specify_cli.extensions.models import (
        CapabilityCounts,
        Diagnostic,
        HealthAssessment,
        SourceDescriptor,
        SourceEvidence,
        project_entry,
    )

    with pytest.raises(ValueError, match="code and message"):
        Diagnostic.from_mapping({"code": "", "message": "message", "source": None})
    with pytest.raises(ValueError, match="string or null"):
        Diagnostic.from_mapping({"code": "code", "message": "message", "source": 7})
    with pytest.raises(ValueError, match="project-relative"):
        Diagnostic.from_mapping({"code": "code", "message": "message", "source": "C:/private"})

    diagnostic = {"code": "code", "message": "message", "source": None}
    with pytest.raises(ValueError, match="shape"):
        HealthAssessment.from_mapping({"state": "unknown", "diagnostics": []})
    with pytest.raises(ValueError, match="shape"):
        HealthAssessment.from_mapping({"state": "healthy", "diagnostics": "invalid"})
    with pytest.raises(ValueError, match="healthy"):
        HealthAssessment.from_mapping({"state": "healthy", "diagnostics": [diagnostic]})
    with pytest.raises(ValueError, match="requires diagnostics"):
        HealthAssessment.from_mapping({"state": "invalid", "diagnostics": []})
    with pytest.raises(ValueError, match="unique"):
        HealthAssessment.from_mapping({"state": "invalid", "diagnostics": [diagnostic, diagnostic]})

    with pytest.raises(ValueError, match="source kind"):
        SourceDescriptor.from_mapping({"kind": "remote"})
    with pytest.raises(ValueError, match="evidence kind"):
        SourceEvidence.from_mapping(
            {"kind": "combined", "source_sha256": HEX_A, "source_ordinal": 0, "record_sha256": HEX_B}
        )
    for invalid_digest in (None, "a" * 63, "A" * 64):
        with pytest.raises(ValueError, match="lowercase SHA-256"):
            SourceEvidence.from_mapping(
                {
                    "kind": "local",
                    "source_sha256": invalid_digest,
                    "source_ordinal": 0,
                    "record_sha256": HEX_B,
                }
            )
    for invalid_ordinal in (True, -1, "0"):
        with pytest.raises(ValueError, match="non-negative"):
            SourceEvidence.from_mapping(
                {
                    "kind": "local",
                    "source_sha256": HEX_A,
                    "source_ordinal": invalid_ordinal,
                    "record_sha256": HEX_B,
                }
            )

    for invalid_count in (True, -1, "1"):
        with pytest.raises(ValueError, match="non-negative integers"):
            CapabilityCounts.from_mapping({"commands": invalid_count, "templates": 0, "scripts": 0, "hooks": 0})

    for field, value, message in (
        ("evidence", [], "non-empty"),
        ("source_locations", "not-an-array", "array of strings"),
        ("source_locations", ["duplicate", "duplicate"], "unique"),
        ("id", 7, "string or null"),
        ("fallback_identity", 7, "string or null"),
    ):
        row = _valid_local_entry()
        row[field] = value
        with pytest.raises(ValueError, match=message):
            project_entry(row)


@pytest.mark.parametrize(
    "mutate",
    [
        lambda row: row.update(conflict_reasons=["unexpected"]),
        lambda row: row.update(conflict=True, conflict_reasons=["single-source"]),
        lambda row: row.update(activation_state="activation-failed"),
        lambda row: row.update(installed=False),
        lambda row: row.update(catalog_sources=["catalog"]),
        lambda row: row.update(install_allowed=True),
        lambda row: row["source"].update(kind="combined"),
        lambda row: row.update(id=None, fallback_identity=None),
        lambda row: row.update(fallback_identity="unexpected"),
    ],
)
def test_projection_contract_rejects_remaining_cross_field_branches(mutate: object) -> None:
    from specify_cli.extensions.models import project_entry

    row = deepcopy(_valid_local_entry())
    assert callable(mutate)
    mutate(row)

    with pytest.raises(ValueError):
        project_entry(row)
