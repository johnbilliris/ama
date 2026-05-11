"""Unit tests for spec-036 T-R01 — canonical 16-layer taxonomy (FR-027).

The Pydantic ``StrEnum`` at ``packages/domain/src/domain/models/sim_layer_taxonomy``
is the **single source of truth** for the closed-set of 16 map-overlay layer
types. The TypeScript twin
(``apps/web/src/lib/sse/map-overlay-events.ts:51-68``) MUST stay byte-aligned;
the contract test in ``tests/contract/test_layer_taxonomy_alignment.py``
asserts set-equality across both. T-R02 (Wave 2) will refactor
``apps/api/app/services/simulation/map_overlay_publisher.py`` to import this
enum.

Acceptance criteria from tasks.md §11 T-R01:
- Pydantic StrEnum with 16 canonical names per FR-027.
- Mirrors ``apps/web/src/lib/sse/map-overlay-events.ts`` enum exactly.
- Exportable as JSON schema (Wave 2 codegen feeds the TS side).
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from packages.domain.src.domain.models.sim_layer_taxonomy import (
    ALL_LAYER_TYPES,
    SimLayerTaxonomy,
    layer_taxonomy_json_schema,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
TS_TAXONOMY_FILE = REPO_ROOT / "apps" / "web" / "src" / "lib" / "sse" / "map-overlay-events.ts"


def _ts_layer_types() -> list[str]:
    """Parse the TS ``MAP_OVERLAY_LAYER_TYPES`` array literal.

    We only look for the contents inside the first
    ``MAP_OVERLAY_LAYER_TYPES = [ ... ]`` declaration; quoted entries
    become the returned list in source order.
    """

    text = TS_TAXONOMY_FILE.read_text(encoding="utf-8")
    block_match = re.search(
        r"MAP_OVERLAY_LAYER_TYPES\s*=\s*\[(.*?)\]\s*as\s+const",
        text,
        flags=re.DOTALL,
    )
    assert block_match is not None, "Could not find MAP_OVERLAY_LAYER_TYPES literal in TS file"
    return re.findall(r'"([^"]+)"', block_match.group(1))


def test_taxonomy_has_exactly_sixteen_members() -> None:
    """FR-027 asserts the closed set is exactly 16 layer types."""

    assert len(SimLayerTaxonomy) == 16
    assert len(ALL_LAYER_TYPES) == 16


def test_taxonomy_members_match_typescript_source() -> None:
    """The Python enum mirrors the TS ``MAP_OVERLAY_LAYER_TYPES`` exactly."""

    ts_types = _ts_layer_types()
    py_types = [member.value for member in SimLayerTaxonomy]
    assert py_types == ts_types, (
        f"Python ↔ TypeScript taxonomy drift detected:\n  python: {py_types}\n  typescript: {ts_types}"
    )


def test_taxonomy_set_equality() -> None:
    """Order-insensitive equality check between Python and TS sets."""

    assert set(member.value for member in SimLayerTaxonomy) == set(_ts_layer_types())


def test_taxonomy_is_str_enum() -> None:
    """Each member is a string-comparable enum (works as map / dict key)."""

    sample = SimLayerTaxonomy.HAZARD_PERIMETER
    assert sample == "hazard-perimeter"
    assert sample.value == "hazard-perimeter"
    assert {sample: 1}[sample] == 1


def test_taxonomy_rejects_unknown_strings() -> None:
    """Unknown strings cannot coerce to a member (closed-set guarantee)."""

    import pytest

    with pytest.raises(ValueError):
        SimLayerTaxonomy("not-a-real-layer")


def test_layer_taxonomy_json_schema_round_trip() -> None:
    """The exported JSON schema enumerates the 16 canonical members."""

    schema = layer_taxonomy_json_schema()
    rendered = json.dumps(schema)
    payload = json.loads(rendered)
    assert payload["type"] == "string"
    assert set(payload["enum"]) == set(_ts_layer_types())
    assert payload["title"] == "SimLayerTaxonomy"
    assert "FR-027" in payload.get("description", "")
