"""Tests for spec-036 T-U01/T-U02 — Foundry carve-out registry & schema (FR-062).

The carve-out registry tracks any Azure AI Foundry feature, region, or SKU
used **outside** the AU East Foundry boundary. The registry seed at
``infra/foundry/carveout-registry.json`` ships **empty** by default; CI
(T-U03/T-U04, Wave 2) refuses to merge if code references a carve-out
marker (``# carveout:<id>``) that is not present in the registry.

Acceptance criteria from tasks.md §14 T-U01, T-U02:
- ``infra/foundry/carveout-registry.json`` exists with
  ``{"version":"1.0.0","carveouts":[]}``.
- ``infra/foundry/carveout-registry.schema.json`` defines a closed-set
  shape for entries: ``{id, region, sku, justification, expiry_date,
  owner, sli_impact[]}``.
- The empty seed validates against the schema.
"""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = REPO_ROOT / "infra" / "foundry" / "carveout-registry.json"
SCHEMA_PATH = REPO_ROOT / "infra" / "foundry" / "carveout-registry.schema.json"


@pytest.fixture(scope="module")
def schema() -> dict:
    """Load the carve-out registry JSON schema."""

    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def registry() -> dict:
    """Load the empty carve-out registry seed."""

    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


# --- T-U01 acceptance --------------------------------------------------------


def test_registry_seed_exists() -> None:
    """The empty registry seed file is committed at the canonical path."""

    assert REGISTRY_PATH.is_file(), (
        f"Expected registry seed at {REGISTRY_PATH.relative_to(REPO_ROOT)}; "
        f"this is required by ADR-036-009 / FR-062 / Plan-decision 16."
    )


def test_registry_seed_has_version_and_empty_carveouts(registry: dict) -> None:
    """Registry ships with version 1.0.0 and an empty carveouts array."""

    assert registry["version"] == "1.0.0"
    assert registry["carveouts"] == []


def test_registry_seed_validates_against_schema(schema: dict, registry: dict) -> None:
    """The empty seed satisfies the schema (T-U02 acceptance)."""

    jsonschema.validate(instance=registry, schema=schema)


# --- T-U02 acceptance --------------------------------------------------------


def test_schema_file_exists() -> None:
    """The schema is committed at the canonical path next to the registry."""

    assert SCHEMA_PATH.is_file()


def test_schema_is_valid_jsonschema(schema: dict) -> None:
    """The schema document itself is a valid JSON Schema."""

    jsonschema.Draft202012Validator.check_schema(schema)


def test_schema_root_requires_version_and_carveouts(schema: dict) -> None:
    """The root document requires the two top-level fields."""

    assert set(schema["required"]) >= {"version", "carveouts"}
    assert schema["properties"]["carveouts"]["type"] == "array"


def test_schema_carveout_required_fields(schema: dict) -> None:
    """Each carve-out entry exposes the seven canonical fields."""

    item_schema = schema["properties"]["carveouts"]["items"]
    expected = {
        "id",
        "region",
        "sku",
        "justification",
        "expiry_date",
        "owner",
        "sli_impact",
    }
    assert expected <= set(item_schema["required"]), (
        f"Carve-out item schema missing required fields: {expected - set(item_schema['required'])}"
    )


def test_schema_rejects_missing_required_field(schema: dict) -> None:
    """A carve-out missing ``justification`` is rejected (negative test)."""

    bad = {
        "version": "1.0.0",
        "carveouts": [
            {
                "id": "fy-foundry-region-east-us",
                "region": "eastus",
                "sku": "GPT-4o",
                "expiry_date": "2026-09-30",
                "owner": "platform-team@example.com",
                "sli_impact": ["latency_p95_chat"],
            }
        ],
    }
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(instance=bad, schema=schema)


def test_schema_accepts_well_formed_carveout(schema: dict) -> None:
    """A complete carve-out entry validates (positive test)."""

    good = {
        "version": "1.0.0",
        "carveouts": [
            {
                "id": "fy-foundry-region-east-us",
                "region": "eastus",
                "sku": "GPT-4o",
                "justification": "Capacity unavailable in australiaeast",
                "expiry_date": "2026-09-30",
                "owner": "platform-team@example.com",
                "sli_impact": ["latency_p95_chat", "data_residency"],
            }
        ],
    }
    jsonschema.validate(instance=good, schema=schema)


def test_schema_expiry_date_format(schema: dict) -> None:
    """Expiry dates must be ISO-8601 calendar dates (``YYYY-MM-DD``)."""

    item = schema["properties"]["carveouts"]["items"]
    assert item["properties"]["expiry_date"]["format"] == "date"


def test_schema_sli_impact_is_array_of_strings(schema: dict) -> None:
    """``sli_impact`` is a non-empty array of strings."""

    item = schema["properties"]["carveouts"]["items"]
    sli = item["properties"]["sli_impact"]
    assert sli["type"] == "array"
    assert sli.get("minItems", 0) >= 1
    assert sli["items"]["type"] == "string"
