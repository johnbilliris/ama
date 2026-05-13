"""Spec-039 T012: contract test for packages/domain/src/domain/seed/seed_record.schema.json.

Asserts SeedRecord requires fictitious=true, residency=AU, and that pspf
caps at OFFICIAL: SENSITIVE; FixtureWrapper requires licence + schema_version.
"""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
SCHEMA_PATH = REPO_ROOT / "packages" / "domain" / "src" / "domain" / "seed" / "seed_record.schema.json"


@pytest.fixture(scope="module")
def schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def test_schema_file_exists():
    assert SCHEMA_PATH.exists()


def test_seed_record_requires_fictitious_residency(schema):
    rec = schema["$defs"]["SeedRecord"]
    assert "fictitious" in rec["required"]
    assert "residency" in rec["required"]
    assert rec["properties"]["fictitious"]["const"] is True
    assert rec["properties"]["residency"]["const"] == "AU"


def test_seed_record_pspf_capped_at_official_sensitive(schema):
    rec = schema["$defs"]["SeedRecord"]
    enum = rec["properties"]["pspf"]["enum"]
    assert "OFFICIAL: SENSITIVE" in enum
    assert "PROTECTED" not in enum
    assert "SECRET" not in enum
    assert "TOP SECRET" not in enum


def test_fixture_wrapper_requires_licence(schema):
    wrap = schema["$defs"]["FixtureWrapper"]
    for k in ("fictitious", "residency", "licence", "schema_version"):
        assert k in wrap["required"]


def test_valid_seed_file_validates(schema):
    doc = {
        "_fixture": {
            "fictitious": True,
            "residency": "AU",
            "licence": "CC-BY-4.0",
            "schema_version": "1",
        },
        "records": [
            {
                "id": "alert-bushfire-001",
                "fictitious": True,
                "residency": "AU",
                "pspf": "OFFICIAL",
                "licence": "CC-BY-4.0",
                "body": "TEST — DO NOT BROADCAST",
            }
        ],
    }
    # The top-level oneOf needs exactly one branch to match — SeedFile here.
    jsonschema.Draft202012Validator(schema).validate(doc)


def test_protected_pspf_rejected(schema):
    bad = {
        "id": "x-protected",
        "fictitious": True,
        "residency": "AU",
        "pspf": "PROTECTED",
        "licence": "CC-BY-4.0",
    }
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.Draft202012Validator(schema["$defs"]["SeedRecord"]).validate(bad)


def test_missing_fictitious_rejected(schema):
    bad = {"id": "x", "residency": "AU"}
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.Draft202012Validator(schema["$defs"]["SeedRecord"]).validate(bad)
