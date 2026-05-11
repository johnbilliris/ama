"""Codegen guard for spec-036 T-R03 — TS twin alignment with the canonical
Python layer taxonomy.

Wave 1 introduced the
:class:`packages.domain.src.domain.models.sim_layer_taxonomy.SimLayerTaxonomy`
StrEnum; Wave 1 also exported it via
:func:`packages.domain.src.domain.models.sim_layer_taxonomy.layer_taxonomy_json_schema`.
T-R03 wires those into a small codegen helper at
``scripts/codegen/generate_map_overlay_taxonomy_ts.py`` that rewrites the
canonical block in ``apps/web/src/lib/sse/map-overlay-events.ts``.

These tests double as contract drift guards:
1. The codegen helper produces a stable rendering for the canonical 16
   layer types (covered by the in-place Python schema export).
2. The current TS file already contains the rendered block — i.e. there
   is no pending drift.
3. Running the helper in ``--check`` mode succeeds (CI gate).

The Wave 4 contract test (T-R06) will additionally compare the parsed
TS array to ``ALL_LAYER_TYPES`` set-equally; this Wave 2 test is the
*generation-side* invariant.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from packages.domain.src.domain.models.sim_layer_taxonomy import (
    ALL_LAYER_TYPES,
    layer_taxonomy_json_schema,
)
from scripts.codegen.generate_map_overlay_taxonomy_ts import (
    END_SENTINEL,
    START_SENTINEL,
    render_layer_types_block,
)
from scripts.codegen.generate_map_overlay_taxonomy_ts import (
    main as codegen_main,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
TS_FILE = REPO_ROOT / "apps" / "web" / "src" / "lib" / "sse" / "map-overlay-events.ts"


@pytest.fixture(scope="module")
def ts_text() -> str:
    return TS_FILE.read_text(encoding="utf-8")


def test_render_block_includes_each_canonical_layer_type() -> None:
    """The rendered block names every member of the canonical enum."""

    block = render_layer_types_block(list(ALL_LAYER_TYPES))
    for name in ALL_LAYER_TYPES:
        assert f'"{name}"' in block, f"Codegen output is missing {name!r}; canonical={ALL_LAYER_TYPES!r}"


def test_render_block_starts_and_ends_with_sentinels() -> None:
    """The rendered block is bounded by the splice sentinels."""

    block = render_layer_types_block(list(ALL_LAYER_TYPES))
    assert block.startswith(START_SENTINEL)
    assert block.rstrip().endswith(END_SENTINEL)


def test_ts_file_already_contains_canonical_block(ts_text: str) -> None:
    """The TS twin already mirrors what the codegen would write.

    This is the byte-equality drift guard — if the Python enum is ever
    extended without re-running the codegen helper, this test fails.
    """

    block = render_layer_types_block(list(ALL_LAYER_TYPES))
    assert block in ts_text, (
        "Drift detected between the canonical Python taxonomy and "
        f"{TS_FILE.relative_to(REPO_ROOT)}. Re-run "
        "`python -m scripts.codegen.generate_map_overlay_taxonomy_ts`."
    )


def test_ts_file_does_not_re_emit_legacy_categories(ts_text: str) -> None:
    """Legacy *signal-category* strings must not appear as TS literal types."""

    legacy_strings = {
        '"weather"',
        '"fire-behaviour"',
        '"comms-channel-state"',
        '"jurisdiction-boundary"',
        '"cascade-link"',
        '"sub-agent-thread"',
        '"comm-receipt"',
        '"lessons-marker"',
        '"degraded-mode-banner"',
        '"simulation-watermark"',
    }
    leaked = {s for s in legacy_strings if s in ts_text}
    assert leaked == set(), (
        "TS map-overlay-events file still contains legacy category strings: "
        f"{leaked!r}. Run the codegen helper to regenerate."
    )


def test_codegen_check_mode_passes() -> None:
    """``--check`` exits 0 — the TS file is already in sync."""

    rc = codegen_main(["--check"])
    assert rc == 0, "Codegen --check reports drift; the TS file is out of sync with the canonical Python taxonomy."


def test_layer_taxonomy_json_schema_round_trip() -> None:
    """The exported JSON Schema enumerates exactly the canonical 16 names."""

    schema = layer_taxonomy_json_schema()
    assert schema["type"] == "string"
    assert tuple(schema["enum"]) == ALL_LAYER_TYPES
    assert schema["enum"]  # non-empty closed set
    # Mutating the returned schema must not contaminate subsequent calls.
    schema["enum"].append("rogue-layer")
    fresh = layer_taxonomy_json_schema()
    assert "rogue-layer" not in fresh["enum"]
