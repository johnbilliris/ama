"""Spec-038 / T053 — Validate ``docs/test-data/manifest.json``.

Checks performed (FR-032, FR-033, FR-042, FR-043, CL-7):

1. Manifest validates against ``docs/test-data/manifest.schema.json`` (JSON
   Schema 2020-12).
2. Every catalogued file under the source roots (see
   ``build_test_data_manifest.SOURCE_ROOTS``) has at least one entry
   whose ``path`` matches it (FR-032 — no missing entries).
3. Every entry's ``path`` resolves to a real file on disk (no orphans).
4. Two-Path Rule: ``category`` ↔ ``path`` location mapping (plan §"Two-Path
   Rule — manifest enforcement") — caught here in addition to the schema-side
   ``allOf`` clauses.
5. PSPF cap: every entry ``pspf`` ∈ {``OFFICIAL``, ``OFFICIAL: SENSITIVE``}
   and never higher (FR-043, schema enum already enforces; double-checked).
6. AU residency: every entry ``residency == "AU"`` (FR-042).
7. ``pii == false`` (NN-3, FR-031).
8. Indigenous cultural-review flag obeyed (cross-checked further by
   ``check_indigenous_placeholders.py`` — kept in sync here).

Run::

    python tools/lint/check_test_data_manifest.py
    python tools/lint/check_test_data_manifest.py --render          # also write MANIFEST.md

Exit code 0 → clean, 1 → drift detected (machine-readable JSON summary on
stderr, human diff on stdout).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import jsonschema

# Reuse the catalogue + helpers from the builder.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_test_data_manifest import (  # noqa: E402
    SKIP_NAMES,
    SKIP_SUBSTR,
    SOURCE_ROOTS,
    _walk_root,
)

# Two-Path Rule manifest enforcement (plan lines 311–324).
PATH_RULES: dict[str, list[str]] = {
    # category : list of allowed path prefixes (POSIX).
    "synthetic": [
        "packages/domain/src/domain/seed/",
    ],
    "alert-template": [
        "packages/domain/src/domain/seed/alert-templates/",
    ],
    "persona-binding": [
        "packages/domain/src/domain/seed/",
    ],
    "generator": [
        "scripts/generators/",
    ],
    "simulator-feed-shape": [
        "apps/api/app/services/simulation/feeds/",
        "fixtures/sim_replays/",
    ],
    # ``mock`` and ``public`` are deliberately unconstrained — they exist so
    # in-process mocks (event_hub_publisher fallback, eval-runner cassettes,
    # the denylist itself, sample data/ fixtures) can be enumerated without
    # being treated as Path 1 or Path 2 artefacts.
}


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _enumerate_disk_files(repo_root: Path) -> set[str]:
    """Return the POSIX rel-paths of every file the manifest must enumerate."""
    out: set[str] = set()
    for rel_root, pattern, *_rest in SOURCE_ROOTS:
        for fp in _walk_root(repo_root, rel_root, pattern):
            if fp.name in SKIP_NAMES:
                continue
            rel = fp.relative_to(repo_root).as_posix()
            if any(s in "/" + rel for s in SKIP_SUBSTR):
                continue
            out.add(rel)
    return out


def check(repo_root: Path, render: bool) -> int:
    issues: list[str] = []
    summary: dict[str, object] = {"checks": []}

    schema_path = repo_root / "docs" / "test-data" / "manifest.schema.json"
    manifest_path = repo_root / "docs" / "test-data" / "manifest.json"
    if not schema_path.exists():
        print(f"ERROR: schema missing: {schema_path}", file=sys.stderr)
        return 2
    if not manifest_path.exists():
        print(f"ERROR: manifest missing: {manifest_path}", file=sys.stderr)
        return 2

    schema = _load(schema_path)
    doc = _load(manifest_path)

    # 1) Schema validation.
    try:
        jsonschema.Draft202012Validator(schema).validate(doc)
        summary["checks"].append({"name": "schema", "status": "pass"})
    except jsonschema.ValidationError as e:
        issues.append(f"schema-violation: {e.message} at {list(e.absolute_path)}")
        summary["checks"].append({"name": "schema", "status": "fail"})

    entries = doc.get("entries", [])
    by_path: dict[str, list[str]] = {}
    for e in entries:
        if "path" in e:
            by_path.setdefault(e["path"], []).append(e["id"])

    # 2) Every catalogued disk file has at least one manifest entry.
    on_disk = _enumerate_disk_files(repo_root)
    missing_in_manifest = sorted(on_disk - set(by_path.keys()))
    for p in missing_in_manifest:
        issues.append(f"missing-manifest-entry: {p}")

    # 3) Every entry path resolves to a real file.
    orphans: list[str] = []
    for p, ids in by_path.items():
        if not (repo_root / p).exists():
            orphans.append(p)
            issues.append(f"orphan-manifest-entry: {p} (ids={ids})")

    # 4) Two-Path Rule.
    for e in entries:
        cat = e.get("category")
        path = e.get("path")
        if cat in PATH_RULES and path:
            allowed = PATH_RULES[cat]
            if not any(path.startswith(prefix) for prefix in allowed):
                issues.append(
                    f"two-path-violation: id={e.get('id')!r} "
                    f"category={cat!r} path={path!r} "
                    f"(allowed prefixes: {allowed})"
                )

    # 5/6/7) PSPF cap, AU residency, no PII.
    for e in entries:
        if e.get("pspf") not in ("OFFICIAL", "OFFICIAL: SENSITIVE"):
            issues.append(f"pspf-cap-violation: id={e.get('id')!r} pspf={e.get('pspf')!r}")
        if e.get("residency") != "AU":
            issues.append(f"residency-violation: id={e.get('id')!r}")
        if e.get("pii") is not False:
            issues.append(f"pii-violation: id={e.get('id')!r}")

    # 8) Cultural-review flag (the deeper check is in
    #    check_indigenous_placeholders.py; here we just verify the field is
    #    present and boolean — the schema also enforces this).
    for e in entries:
        if not isinstance(e.get("cultural_review_required"), bool):
            issues.append(f"cultural-review-flag-missing: id={e.get('id')!r}")

    summary["entry_count"] = len(entries)
    summary["disk_files"] = len(on_disk)
    summary["missing"] = len(missing_in_manifest)
    summary["orphans"] = len(orphans)
    summary["issues"] = len(issues)

    if render:
        # Lazy import so the lint dep isn't required for non-render runs.
        from render_test_data_manifest_md import main as render_main

        render_main(["--repo-root", str(repo_root)])
        summary["rendered"] = True

    if issues:
        print("docs/test-data/manifest.json drift detected:")
        for issue in issues:
            print(f"  - {issue}")
        print(json.dumps(summary, indent=2), file=sys.stderr)
        return 1

    print(f"docs/test-data/manifest.json clean — {len(entries)} entries, {len(on_disk)} catalogued files, 0 orphans.")
    print(json.dumps(summary, indent=2), file=sys.stderr)
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo-root", default=".", type=Path)
    p.add_argument(
        "--render",
        action="store_true",
        help="Also write docs/test-data/MANIFEST.md from manifest.json.",
    )
    args = p.parse_args(argv)
    return check(args.repo_root.resolve(), args.render)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
