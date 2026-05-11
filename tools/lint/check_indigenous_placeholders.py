"""Spec-039 / T054 — Indigenous placeholder lint (FR-044, CL-6).

Two-layer enforcement (plan §"Indigenous Placeholder Lint Design"):

1. **Lexical denylist** — every file under the catalogued roots (seed,
   generators, simulator feeds, replays, manifest) is scanned for tokens
   from ``[NAMES]``, ``[COMMUNITIES]``, ``[SACRED_COORDS]``. Any match is a
   hard fail.
2. **Manifest cross-check** — every artefact whose contents (or file path,
   or persona bindings) intersect a ``[CONTEXT_ZONES]`` token MUST carry
   ``cultural_review_required=true`` in its manifest entry. Otherwise fail.

Run::

    python tools/lint/check_indigenous_placeholders.py
    python tools/lint/check_indigenous_placeholders.py --repo-root .

Exit code 0 → clean, 1 → drift (structured JSON summary on stderr).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

SCAN_ROOTS: tuple[str, ...] = (
    "packages/domain/src/domain/seed",
    "scripts/generators",
    "apps/api/app/services/simulation/feeds",
    "fixtures/sim_replays",
)
DENYLIST_REL = "tools/lint/data/indigenous_denylist.txt"
MANIFEST_REL = "docs/test-data/manifest.json"

SECTION_RE = re.compile(r"^\[(?P<name>NAMES|COMMUNITIES|SACRED_COORDS|CONTEXT_ZONES)\]\s*$")


def parse_denylist(text: str) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {
        "NAMES": [],
        "COMMUNITIES": [],
        "SACRED_COORDS": [],
        "CONTEXT_ZONES": [],
    }
    current: str | None = None
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        m = SECTION_RE.match(line)
        if m:
            current = m.group("name")
            continue
        if current is None:
            continue
        sections[current].append(line.lower())
    return sections


def _walk(repo_root: Path, rel_root: str) -> list[Path]:
    root = repo_root / rel_root
    if not root.exists():
        return []
    out: list[Path] = []
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        if "__pycache__" in p.parts:
            continue
        if p.suffix.lower() in (".pyc",):
            continue
        out.append(p)
    return sorted(out)


def _file_text(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8", errors="ignore").lower()
    except OSError:
        return ""


def check(repo_root: Path) -> int:
    denylist_path = repo_root / DENYLIST_REL
    if not denylist_path.exists():
        print(f"ERROR: denylist missing: {denylist_path}", file=sys.stderr)
        return 2

    deny = parse_denylist(denylist_path.read_text(encoding="utf-8"))
    issues: list[str] = []
    hits: dict[str, list[tuple[str, str, str]]] = defaultdict(list)

    # 1) Lexical scan of catalogued roots.
    for root in SCAN_ROOTS:
        for fp in _walk(repo_root, root):
            text = _file_text(fp)
            if not text:
                continue
            for section in ("NAMES", "COMMUNITIES", "SACRED_COORDS"):
                for token in deny[section]:
                    if not token:
                        continue
                    if token.lower() in text:
                        rel = fp.relative_to(repo_root).as_posix()
                        issues.append(f"denylist-hit: section={section} token={token!r} file={rel}")
                        hits[section].append((token, rel, ""))

    # 2) Manifest cross-check on context zones.
    manifest_path = repo_root / MANIFEST_REL
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            issues.append(f"manifest-parse-error: {e}")
            manifest = {"entries": []}
        for e in manifest.get("entries", []):
            path = e.get("path") or ""
            haystacks: list[str] = [
                path.lower(),
                e.get("id", "").lower(),
                e.get("name", "").lower(),
                " ".join(e.get("persona_bindings", [])).lower(),
                e.get("cultural_review_notes", "").lower(),
            ]
            # Also peek at file contents (only for small files to keep CI fast).
            file_path = repo_root / path if path else None
            if file_path and file_path.exists() and file_path.is_file():
                try:
                    if file_path.stat().st_size <= 1_000_000:
                        haystacks.append(_file_text(file_path))
                except OSError:
                    pass
            blob = "\n".join(haystacks)
            zone_hits = [z for z in deny["CONTEXT_ZONES"] if z and z in blob]
            if zone_hits and not e.get("cultural_review_required"):
                issues.append(
                    f"cultural_review_required=false but context-zone match: id={e.get('id')!r} zones={zone_hits}"
                )

    summary = {
        "denylist_sections": {k: len(v) for k, v in deny.items()},
        "scan_roots": list(SCAN_ROOTS),
        "issues": len(issues),
    }
    if issues:
        print("indigenous-placeholder lint drift detected:")
        for issue in issues:
            print(f"  - {issue}")
        print(json.dumps(summary, indent=2), file=sys.stderr)
        return 1
    print(
        f"indigenous-placeholder lint clean — denylist sections "
        f"{summary['denylist_sections']}, scanned {len(SCAN_ROOTS)} roots."
    )
    print(json.dumps(summary, indent=2), file=sys.stderr)
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo-root", default=".", type=Path)
    args = p.parse_args(argv)
    return check(args.repo_root.resolve())


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
