"""Codegen helper for the FR-027 map-overlay layer taxonomy (T-R03).

Regenerates the canonical block inside
``apps/web/src/lib/sse/map-overlay-events.ts`` (the
``MapOverlayLayerType`` discriminated-union and the
``MAP_OVERLAY_LAYER_TYPES`` literal tuple) from the canonical Python
source of truth at
``packages/domain/src/domain/models/sim_layer_taxonomy.py``.

This script is intentionally *idempotent* and *additive*: it only rewrites
the two declarations between sentinel comments, leaving payload typings,
imports, and helper code untouched.

Usage
-----
    python -m scripts.codegen.generate_map_overlay_taxonomy_ts            # in-place rewrite
    python -m scripts.codegen.generate_map_overlay_taxonomy_ts --check    # CI-friendly diff
    python -m scripts.codegen.generate_map_overlay_taxonomy_ts --emit     # print to stdout

The companion test in
``tests/unit/test_map_overlay_taxonomy_codegen.py`` invokes
:func:`render_layer_types_block` and asserts the TS file already contains
the rendered text (drift guard for spec-036 T-R06 contract test).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
TS_FILE = REPO_ROOT / "apps" / "web" / "src" / "lib" / "sse" / "map-overlay-events.ts"

# Sentinels that wrap the codegen-managed block in the TS file.
START_SENTINEL = "/** Closed set of map-overlay layer types (FR-027 / spec-036 contract §2). */"
END_SENTINEL = "] as const satisfies readonly MapOverlayLayerType[];"


def render_layer_types_block(layer_types: list[str]) -> str:
    """Return the canonical TS block for *layer_types* (deterministic).

    Two declarations are produced:
    * The ``MapOverlayLayerType`` discriminated-union of string literals.
    * The ``MAP_OVERLAY_LAYER_TYPES`` ``as const`` literal tuple, which
      doubles as a runtime iterable.
    """

    union_lines = "\n".join(f'  | "{name}"' for name in layer_types)
    array_lines = "\n".join(f'  "{name}",' for name in layer_types)
    return (
        f"{START_SENTINEL}\n"
        "export type MapOverlayLayerType =\n"
        f"{union_lines};\n"
        "\n"
        "/**\n"
        " * The 16 layer types as a literal tuple — the LENGTH of this tuple is\n"
        " * type-checked against the closed set above so the count never drifts.\n"
        " *\n"
        " * @see specs/036-sim-agent-extend/contracts/sse-map-overlay.md §2\n"
        " */\n"
        "export const MAP_OVERLAY_LAYER_TYPES = [\n"
        f"{array_lines}\n"
        f"{END_SENTINEL}"
    )


def _load_canonical_layer_types() -> list[str]:
    """Import the canonical taxonomy without forcing a heavy dependency tree.

    The function defers the import so callers running ``--help`` need not
    install the domain package.
    """

    sys.path.insert(0, str(REPO_ROOT))
    from packages.domain.src.domain.models.sim_layer_taxonomy import (
        ALL_LAYER_TYPES,
    )

    return list(ALL_LAYER_TYPES)


def _splice(existing: str, replacement: str) -> str:
    """Replace the codegen block in *existing* with *replacement*."""

    start = existing.find(START_SENTINEL)
    end = existing.find(END_SENTINEL, start + 1)
    if start < 0 or end < 0:
        raise RuntimeError(
            f"Could not locate codegen sentinels in {TS_FILE}. "
            "Manual repair required before re-running codegen."
        )
    end_with_sentinel = end + len(END_SENTINEL)
    return existing[:start] + replacement + existing[end_with_sentinel:]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit non-zero if the TS file would change. CI-friendly.",
    )
    parser.add_argument(
        "--emit",
        action="store_true",
        help="Print the rendered TS block to stdout and exit.",
    )
    args = parser.parse_args(argv)

    layer_types = _load_canonical_layer_types()
    block = render_layer_types_block(layer_types)

    if args.emit:
        print(block)
        return 0

    existing = TS_FILE.read_text(encoding="utf-8")
    rewritten = _splice(existing, block)

    if args.check:
        if existing == rewritten:
            return 0
        sys.stderr.write(
            f"{TS_FILE.relative_to(REPO_ROOT)} is out of sync with the canonical "
            "Python taxonomy. Re-run `python -m scripts.codegen.generate_map_overlay_taxonomy_ts`.\n"
        )
        return 2

    if existing != rewritten:
        TS_FILE.write_text(rewritten, encoding="utf-8")
    return 0


if __name__ == "__main__":  # pragma: no cover — CLI entrypoint
    raise SystemExit(main())
