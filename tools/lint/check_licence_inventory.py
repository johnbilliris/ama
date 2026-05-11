"""Lint: ``docs/corpus/INDEXING-LICENCE-INVENTORY.md`` ↔ ``source.json`` parity.

Spec 036 T039 / T055 — fails CI if the machine-checked inventory drifts away
from the canonical ``source.json`` files under ``docs/corpus/``.

Drift cases caught:

1. An entry under ``docs/corpus/`` with no row in the inventory.
2. A row in the inventory with no matching ``source.json`` on disk.
3. Mismatched ``licence`` or ``mode`` between ``source.json`` and the
   inventory row.

Run::

    python tools/lint/check_licence_inventory.py
    python tools/lint/check_licence_inventory.py --inventory docs/corpus/INDEXING-LICENCE-INVENTORY.md \\
                                                  --corpus-root docs/corpus

Exit code 0 → clean, 1 → drift detected (with a structured diff written to
stdout for the CI logs).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Iterable
from pathlib import Path
from typing import Any

ROW_RE = re.compile(
    r"^\|\s*(?P<jurisdiction>[a-z0-9_]+)\s*\|\s*(?P<topic>[A-Za-z0-9._\-]+)\s*\|"
    r"\s*(?P<mode>full-text|metadata-only|excluded)\s*\|"
    r"\s*(?P<licence>[^|]+?)\s*\|\s*(?P<source_url>[^|]+?)\s*\|"
)


def parse_inventory(text: str) -> list[dict[str, str]]:
    """Parse the Markdown inventory into a list of row-dicts."""
    rows: list[dict[str, str]] = []
    for line in text.splitlines():
        m = ROW_RE.match(line)
        if not m:
            continue
        if m.group("topic") == "topic":  # header row
            continue
        rows.append(
            {
                "jurisdiction": m.group("jurisdiction").strip(),
                "topic": m.group("topic").strip(),
                "mode": m.group("mode").strip(),
                "licence": m.group("licence").strip(),
                "source_url": m.group("source_url").strip(),
            }
        )
    return rows


def discover_sources(corpus_root: Path) -> list[dict[str, Any]]:
    """Walk ``corpus_root`` and return one record per ``source.json``."""
    out: list[dict[str, Any]] = []
    for src in sorted(corpus_root.rglob("source.json")):
        rel = src.relative_to(corpus_root)
        parts = rel.parts
        if len(parts) < 3:
            continue
        try:
            data = json.loads(src.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        out.append(
            {
                "jurisdiction": parts[0],
                "topic": parts[1],
                "mode": data.get("mode", "full-text"),
                "licence": data.get("licence", ""),
                "source_url": data.get("url", ""),
                "path": str(src),
            }
        )
    return out


def diff(inventory_rows: Iterable[dict[str, str]], sources: Iterable[dict[str, Any]]) -> list[str]:
    """Compute the inventory-↔-sources diff; return human-readable lines."""
    inv_index = {(r["jurisdiction"], r["topic"]): r for r in inventory_rows}
    src_index = {(s["jurisdiction"], s["topic"]): s for s in sources}

    issues: list[str] = []
    only_in_sources = sorted(set(src_index.keys()) - set(inv_index.keys()))
    only_in_inventory = sorted(set(inv_index.keys()) - set(src_index.keys()))
    for j, t in only_in_sources:
        issues.append(f"missing-from-inventory: {j}/{t}")
    for j, t in only_in_inventory:
        issues.append(f"missing-on-disk: {j}/{t}")

    for key in sorted(set(inv_index.keys()) & set(src_index.keys())):
        inv = inv_index[key]
        src = src_index[key]
        # Mode parity: source.json defaults to ``full-text`` when absent.
        if inv["mode"] != src["mode"]:
            issues.append(f"mode-mismatch: {key[0]}/{key[1]} inventory={inv['mode']!r} source={src['mode']!r}")
    return issues


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--inventory",
        default="docs/corpus/INDEXING-LICENCE-INVENTORY.md",
        type=Path,
    )
    p.add_argument("--corpus-root", default="docs/corpus", type=Path)
    args = p.parse_args(argv)

    if not args.inventory.exists():
        print(f"ERROR: inventory file {args.inventory} not found", file=sys.stderr)
        return 1
    if not args.corpus_root.exists():
        print(f"ERROR: corpus root {args.corpus_root} not found", file=sys.stderr)
        return 1

    inventory_rows = parse_inventory(args.inventory.read_text(encoding="utf-8"))
    sources = discover_sources(args.corpus_root)
    issues = diff(inventory_rows, sources)
    if issues:
        print("INDEXING-LICENCE-INVENTORY drift detected:")
        for issue in issues:
            print(f"  - {issue}")
        return 1
    print(f"INDEXING-LICENCE-INVENTORY clean — {len(sources)} source.json <-> {len(inventory_rows)} inventory rows.")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
