"""Shared fixtures for spec-037 schema-contract tests.

Loads the canonical JSON Schemas from `packages/schemas/spec_037/` and constructs
minimal valid + invalid example envelopes per artefact. Tests fail until the
mirror schemas exist (T004) and Pydantic models exist (T026..T032).

Citations: FR-009, RES-01, PD-037-01.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
SCHEMA_DIR = REPO_ROOT / "packages" / "schemas" / "spec_037"


def _load_schema(name: str) -> dict[str, Any]:
    path = SCHEMA_DIR / name
    if not path.exists():
        pytest.skip(f"Schema mirror not yet wired: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def schema_dir() -> Path:
    return SCHEMA_DIR


@pytest.fixture(scope="session")
def risk_register_schema() -> dict[str, Any]:
    return _load_schema("risk-register.schema.json")


@pytest.fixture(scope="session")
def adoption_roadmap_schema() -> dict[str, Any]:
    return _load_schema("adoption-roadmap.schema.json")


@pytest.fixture(scope="session")
def executive_kpi_schema() -> dict[str, Any]:
    return _load_schema("executive-kpi-surface.schema.json")


@pytest.fixture(scope="session")
def rai_register_schema() -> dict[str, Any]:
    return _load_schema("responsible-ai-register.schema.json")


@pytest.fixture(scope="session")
def feature_value_schema() -> dict[str, Any]:
    return _load_schema("feature-value-ledger.schema.json")


@pytest.fixture(scope="session")
def publication_gate_schema() -> dict[str, Any]:
    return _load_schema("publication-gate-metadata.schema.json")


@pytest.fixture
def base_metadata() -> dict[str, Any]:
    """Minimum-valid PublicationGateMetadata block (manual_row_ratio = 0)."""
    return {
        "manual_row_count": 0,
        "total_row_count": 1,
        "manual_row_ratio": 0.0,
        "link_check_status": "passed",
        "last_gate_run_utc": "2026-05-11T00:00:00Z",
    }


def _resolver(schema: dict[str, Any]):
    """Build a referencing.Registry that resolves cross-schema $refs locally."""
    from referencing import Registry, Resource
    from referencing.jsonschema import DRAFT202012

    resources = []
    for name in (
        "risk-register.schema.json",
        "adoption-roadmap.schema.json",
        "executive-kpi-surface.schema.json",
        "responsible-ai-register.schema.json",
        "feature-value-ledger.schema.json",
        "publication-gate-metadata.schema.json",
    ):
        path = SCHEMA_DIR / name
        if path.exists():
            doc = json.loads(path.read_text(encoding="utf-8"))
            resources.append((name, Resource(contents=doc, specification=DRAFT202012)))
    registry = Registry().with_resources(resources)
    return registry


@pytest.fixture
def validator_factory():
    """Factory: given a schema dict, return a jsonschema validator with cross-refs resolved."""
    def _make(schema: dict[str, Any]):
        from jsonschema import Draft202012Validator

        registry = _resolver(schema)
        return Draft202012Validator(schema, registry=registry)

    return _make
