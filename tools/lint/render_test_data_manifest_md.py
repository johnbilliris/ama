"""Spec-039 / T046 — Render ``docs/test-data/MANIFEST.md`` from manifest.json.

Deterministic markdown output (LF terminators, sorted by category then id).
Run::

    python tools/lint/render_test_data_manifest_md.py
"""

from __future__ import annotations

import argparse
import difflib
import json
import sys
from collections import defaultdict
from pathlib import Path

HEADER = """# Test-Data Manifest (Spec 039)

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
    p.add_argument(
        "--check",
        action="store_true",
        help=(
            "Spec-039 FR-036 / CL-9 freshness gate: re-render in memory, "
            "byte-compare against the committed MANIFEST.md (after CRLF→LF "
            "normalisation), exit 0 on parity, exit 1 with unified diff + "
            "remediation command on drift, exit 0 with stderr skip notice "
            "if manifest.json is absent (CL-10)."
        ),
    )
    p.add_argument(
        "--max-diff-lines",
        type=int,
        default=500,
        help="Truncate the unified diff printed in --check mode to this many lines.",
    )
    args = p.parse_args(argv)
    repo_root = args.repo_root.resolve()
    manifest = args.manifest or (repo_root / "docs" / "test-data" / "manifest.json")
    out = args.out or (repo_root / "docs" / "test-data" / "MANIFEST.md")

    if args.check:
        if not manifest.exists():
            print(
                f"[skip] {manifest} not present — freshness gate N/A on this branch (CL-10)",
                file=sys.stderr,
            )
            return 0
        doc = json.loads(manifest.read_text(encoding="utf-8"))
        rendered = render(doc).replace("\r\n", "\n").encode("utf-8")
        if not out.exists():
            print(
                f"[manifest-md-freshness-lint] {out} is missing — "
                f"run: python tools/lint/build_test_data_manifest.py && "
                f"python tools/lint/render_test_data_manifest_md.py",
                file=sys.stderr,
            )
            return 1
        committed = out.read_bytes().replace(b"\r\n", b"\n")
        if committed == rendered:
            return 0
        # Drift — emit unified diff (truncated) and remediation.
        committed_lines = committed.decode("utf-8", errors="replace").splitlines(keepends=True)
        rendered_lines = rendered.decode("utf-8").splitlines(keepends=True)
        diff = list(
            difflib.unified_diff(
                committed_lines,
                rendered_lines,
                fromfile=str(out) + " (committed)",
                tofile=str(out) + " (re-rendered)",
                n=3,
            )
        )
        max_lines = max(1, args.max_diff_lines)
        truncated = False
        if len(diff) > max_lines:
            diff = diff[:max_lines]
            truncated = True
        sys.stdout.write("".join(diff))
        if truncated:
            sys.stdout.write(f"\n... (diff truncated to {max_lines} lines; raise --max-diff-lines for more)\n")
        sys.stdout.flush()
        print(
            "[manifest-md-freshness-lint] FAIL: docs/test-data/MANIFEST.md is "
            "stale relative to docs/test-data/manifest.json. Remediate with: "
            "python tools/lint/build_test_data_manifest.py && "
            "python tools/lint/render_test_data_manifest_md.py",
            file=sys.stderr,
        )
        return 1

    if not manifest.exists():
        print(f"manifest not found: {manifest}", file=sys.stderr)
        return 1
    doc = json.loads(manifest.read_text(encoding="utf-8"))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(render(doc).replace("\r\n", "\n").encode("utf-8"))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
