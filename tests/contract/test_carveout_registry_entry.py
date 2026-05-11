"""T012 — Entity test for ``CarveoutRegistryEntry`` (Spec 036 / FR-RAG-CV-01..02).

Validates every row in ``infra/parameters/foundry-carveout.yaml`` against
``infra/parameters/foundry-carveout.schema.json`` AND enforces the spec-036
tightenings on top of the schema:

- ``data_minimisation_required: true``
- ``classification_filter_required: true``
- ``len(approver_identities) >= 2``
- ``review_date <= today + 365 days``

Spec ref: data-model.md §CarveoutRegistryEntry; spec.md FR-RAG-CV-01..02.

This test goes RED before T024/T027 land production rows and GREEN once
each row is policy-conformant. An empty ``deployments: []`` registry is a
valid baseline (carve-out is not yet exercised).
"""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from typing import Any

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = ROOT / "infra" / "parameters" / "foundry-carveout.yaml"
SCHEMA_PATH = ROOT / "infra" / "parameters" / "foundry-carveout.schema.json"

PLACEHOLDER_PATTERNS = ("<", "TODO", "FIXME", "PLACEHOLDER")
ONE_YEAR = dt.timedelta(days=365)


@pytest.fixture(scope="module")
def registry() -> dict[str, Any]:
    return yaml.safe_load(REGISTRY_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def schema() -> dict[str, Any]:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def test_registry_validates_against_schema(registry, schema) -> None:
    """The yaml MUST validate against the schema."""
    jsonschema = pytest.importorskip("jsonschema")
    # YAML 1.1 parses ISO-8601 date scalars into ``datetime.date`` objects;
    # the JSON-Schema ``"format": "date"`` predicate requires strings. Round-
    # trip through JSON serialisation (mirrors what ``verify-carveout.ps1``
    # does at runtime) so the schema validates the wire shape.
    jsonable = json.loads(
        json.dumps(
            registry,
            default=lambda o: o.isoformat() if isinstance(o, dt.date | dt.datetime) else str(o),
        )
    )
    jsonschema.validate(jsonable, schema)


def test_reviewer_quorum_at_least_two(registry) -> None:
    """Schema requires reviewer_quorum >= 2; fail fast here for human-readable message."""
    assert int(registry["reviewer_quorum"]) >= 2, (
        f"FR-RAG-CV-01 — reviewer_quorum must be >= 2, got {registry['reviewer_quorum']}"
    )


def test_every_row_carries_data_minimisation_and_classification_flags(registry) -> None:
    """Spec 036 tightening: both flags MUST be true on every row."""
    for row in registry.get("deployments") or []:
        assert row["data_minimisation_required"] is True, (
            f"FR-RAG-CV-03 — deployment {row['model_name']!r} missing data_minimisation_required: true"
        )
        assert row["classification_filter_required"] is True, (
            f"FR-RAG-CV-03 — deployment {row['model_name']!r} missing classification_filter_required: true"
        )


def test_every_row_has_at_least_two_real_approvers(registry) -> None:
    """approver_identities MUST have ≥ 2 non-placeholder entries (FR-RAG-CV-01)."""
    for row in registry.get("deployments") or []:
        approvers = row.get("approver_identities") or []
        assert len(approvers) >= 2, (
            f"FR-RAG-CV-01 — deployment {row['model_name']!r} has {len(approvers)} approver_identities; minimum is 2"
        )
        for who in approvers:
            for placeholder in PLACEHOLDER_PATTERNS:
                assert placeholder not in str(who), (
                    f"FR-RAG-CV-01 — deployment {row['model_name']!r} has placeholder "
                    f"approver {who!r}; replace before CD apply"
                )


def test_every_row_review_date_within_one_year(registry) -> None:
    """review_date MUST be ≤ today + 365 days (FR-RAG-CV-02; SC-003)."""
    today = dt.date.today()
    horizon = today + ONE_YEAR
    for row in registry.get("deployments") or []:
        review_raw = row["review_date"]
        review = review_raw if isinstance(review_raw, dt.date) else dt.date.fromisoformat(str(review_raw))
        assert today <= review <= horizon, (
            f"FR-RAG-CV-02 — deployment {row['model_name']!r} review_date {review} is not within ({today}, {horizon}]"
        )


def test_every_row_region_is_au_or_explicit_carveout(registry) -> None:
    """Australia East / Southeast are default; non-AU regions only via documented business_justification."""
    for row in registry.get("deployments") or []:
        region = str(row["region"]).lower()
        if region not in ("australiaeast", "australiasoutheast"):
            assert len(str(row["business_justification"])) >= 30, (
                f"FR-RAG-CV-04 — deployment {row['model_name']!r} in non-AU region {region!r} "
                f"requires a non-trivial business_justification (≥ 30 chars)"
            )
