"""Spec-038 / T046 — Render ``docs/test-data/MANIFEST.md`` from manifest.json.

Deterministic markdown output (LF terminators, sorted by category then id).
Run::

    python tools/lint/render_test_data_manifest_md.py
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

HEADER = """# Test-Data Manifest (Spec 038)

> **Auto-generated** from `docs/test-data/manifest.json` by
> `tools/lint/render_test_data_manifest_md.py`.
> Do not edit by hand — re-run the renderer instead.

This document is the human-readable view of the canonical machine-readable
manifest enumerating every test-data artefact in the AMA repository.
Validation lives in `tools/lint/check_test_data_manifest.py` and is wired
into the `quality` job of `.github/workflows/ci.yml` (CL-7).

Cross-references:

- Corpus inventory: [`docs/corpus/MANIFEST.md`](../corpus/MANIFEST.md)
- Indexing licence inventory: [`docs/corpus/INDEXING-LICENCE-INVENTORY.md`](../corpus/INDEXING-LICENCE-INVENTORY.md)
- Schema: [`manifest.schema.json`](./manifest.schema.json)
- Indigenous placeholder denylist:
  [`tools/lint/data/indigenous_denylist.txt`](../../tools/lint/data/indigenous_denylist.txt)
"""


def render(doc: dict) -> str:
    parts: list[str] = [HEADER, ""]
    entries = sorted(doc.get("entries", []), key=lambda e: (e["category"], e["id"]))

    by_cat: dict[str, list[dict]] = defaultdict(list)
    for e in entries:
        by_cat[e["category"]].append(e)

    parts.append("## Summary\n")
    parts.append(f"- Schema version: `{doc.get('schema_version')}`")
    parts.append(f"- Total entries: **{len(entries)}**")
    for cat in sorted(by_cat):
        parts.append(f"- `{cat}`: {len(by_cat[cat])}")
    parts.append("")

    for cat in sorted(by_cat):
        parts.append(f"## Category: `{cat}`\n")
        parts.append("| id | path / source_shape | domain_group | personas | pspf | licence | cultural_review |")
        parts.append("|---|---|---|---|---|---|---|")
        for e in by_cat[cat]:
            target = e.get("path") or e.get("source_shape", "")
            personas = ", ".join(e.get("persona_bindings", []))
            parts.append(
                f"| `{e['id']}` | `{target}` | `{e['domain_group']}` | "
                f"{personas} | `{e['pspf']}` | `{e['licence']}` | "
                f"{'**YES**' if e.get('cultural_review_required') else 'no'} |"
            )
        parts.append("")
    return "\n".join(parts).rstrip() + "\n"


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo-root", default=".", type=Path)
    p.add_argument("--manifest", default=None, type=Path)
    p.add_argument("--out", default=None, type=Path)
    args = p.parse_args(argv)
    repo_root = args.repo_root.resolve()
    manifest = args.manifest or (repo_root / "docs" / "test-data" / "manifest.json")
    out = args.out or (repo_root / "docs" / "test-data" / "MANIFEST.md")

    doc = json.loads(manifest.read_text(encoding="utf-8"))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(render(doc).replace("\r\n", "\n").encode("utf-8"))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
