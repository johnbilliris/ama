"""Spec-039 T011: contract test for docs/test-data/manifest.schema.json.

Asserts:
  (a) the schema parses as JSON-Schema 2020-12,
  (b) ``cultural_review_required`` is required on every ManifestEntry,
  (c) the ``category=public ⇒ source_url≠"n/a"`` cross-check is encoded as
      an ``if/then`` clause in the schema (not just description prose).
"""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
SCHEMA_PATH = REPO_ROOT / "docs" / "test-data" / "manifest.schema.json"


@pytest.fixture(scope="module")
def schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def test_schema_file_exists():
    assert SCHEMA_PATH.exists(), f"Manifest schema missing: {SCHEMA_PATH}"


def test_schema_is_valid_2020_12(schema):
    # Must declare itself as 2020-12.
    assert (
        schema.get("$schema")
        == "https://json-schema.org/draft/2020-12/schema"
    )
    # Validator metaschema check.
    jsonschema.Draft202012Validator.check_schema(schema)


def test_cultural_review_required_is_required(schema):
    entry = schema["$defs"]["ManifestEntry"]
    assert "cultural_review_required" in entry["required"], (
        "FR-044/CL-6: cultural_review_required must be a required property "
        "on every ManifestEntry."
    )


def test_public_source_url_cross_check_encoded_as_if_then(schema):
    entry = schema["$defs"]["ManifestEntry"]
    all_of = entry.get("allOf", [])
    found = False
    for clause in all_of:
        if "if" not in clause or "then" not in clause:
            continue
        if_props = (clause["if"].get("properties") or {})
        if (
            if_props.get("category", {}).get("const") == "public"
            and "source_url" in (clause["then"].get("properties") or {})
        ):
            found = True
            break
    assert found, (
        "FR-031/CL-6: category=public must require source_url != 'n/a' "
        "via an if/then clause in the schema."
    )


def test_minimal_valid_manifest_validates(schema):
    doc = {
        "schema_version": "1.0.0",
        "generated_at": "2026-05-11T00:00:00Z",
        "entries": [
            {
                "id": "alert-template-bushfire-en-au",
                "name": "Alert template — bushfire — en-AU",
                "category": "alert-template",
                "path": "packages/domain/src/domain/seed/alert-templates/bushfire_en-AU.json",
                "version": "1.0.0",
                "content_hash": "0" * 64,
                "created_or_updated": "2026-05-11",
                "persona_bindings": ["nsw-rfs-incident-controller"],
                "domain_group": "fire",
                "fictitious": True,
                "pii": False,
                "pspf": "OFFICIAL",
                "residency": "AU",
                "licence": "CC-BY-4.0",
                "source_url": "n/a",
                "snapshot_date": "n/a",
                "dataset_version": "n/a",
                "refresh_policy": "static",
                "volume_tier": "small",
                "record_count": 5,
                "cultural_review_required": False,
            }
        ],
    }
    jsonschema.Draft202012Validator(schema).validate(doc)


def test_public_entry_without_provenance_fails(schema):
    doc = {
        "schema_version": "1.0.0",
        "generated_at": "2026-05-11T00:00:00Z",
        "entries": [
            {
                "id": "bom-warnings-public",
                "name": "BoM warnings public dataset",
                "category": "public",
                "path": "data/bom_warnings.json",
                "version": "1.0.0",
                "content_hash": "0" * 64,
                "created_or_updated": "2026-05-11",
                "persona_bindings": ["bom-duty-meteorologist"],
                "domain_group": "commonwealth",
                "fictitious": True,
                "pii": False,
                "pspf": "OFFICIAL",
                "residency": "AU",
                "licence": "CC-BY-4.0",
                "source_url": "n/a",
                "snapshot_date": "n/a",
                "dataset_version": "n/a",
                "refresh_policy": "refresh-on-public-dataset-update",
                "volume_tier": "medium",
                "record_count": 100,
                "cultural_review_required": False,
            }
        ],
    }
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.Draft202012Validator(schema).validate(doc)
