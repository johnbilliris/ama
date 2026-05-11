"""Lint: RAG-OPTOUT marker ↔ ADR ↔ FR-RAG-NS clause binding (Spec 036 / FR-RAG-NS-08, SC-008, T128).

Walks every Python module under ``apps/agents/`` and ``apps/api/app/services/``
and asserts the same invariants exercised by ``tests/contract/test_rag_optout_lint.py``:

1. **Marker → ADR**: every ``# RAG-OPTOUT [FR-RAG-NS-NN]`` comment is followed
   by a matching ADR file ``docs/decisions/036-foundry-rag-grounding/<NN>-rag-optout-*.md``.
2. **FR coverage**: every FR in FR-RAG-NS-01..09 has at least one ADR file.
3. **ADR → marker**: every ADR file (except the meta-ADR FR-RAG-NS-08) is
   referenced by ≥ 1 marker in the codebase **OR** carries a
   ``code_marker_optional: true`` front-matter line.
4. **Format**: every marker matches the canonical regex
   ``# RAG-OPTOUT [FR-RAG-NS-(0[1-9])]: <reason>``.

Run::

    python tools/lint/check_rag_optout_bindings.py
    python tools/lint/check_rag_optout_bindings.py --root C:\\code\\ama

Exit code 0 → clean, 1 → drift detected (with a structured report on stdout).

This script is the CI hook for FR-RAG-NS-08. It is the structural guarantee
that opt-outs are intentional, declared, and auditable.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

#: Canonical marker form (FR-RAG-NS-08).
MARKER_RE = re.compile(
    r"#\s*RAG-OPTOUT\s*\[FR-RAG-NS-(0[1-9])\]\s*:?\s*(?P<reason>.*)"
)

#: Strict canonical form (anchored to line start).
CANONICAL_RE = re.compile(
    r"^\s*#\s*RAG-OPTOUT\s*\[FR-RAG-NS-(0[1-9])\]\s*:\s*\S",
)

#: ADR filenames carry the FR ordinal as a 2-digit prefix.
ADR_FILE_RE = re.compile(r"^(0[1-9])-rag-optout-[a-z0-9-]+\.md$")

#: All nine FR-RAG-NS clauses MUST be covered.
ALL_FR_ORDINALS: tuple[str, ...] = tuple(f"0{i}" for i in range(1, 10))

#: Source-tree directories scanned for markers.
SCAN_SUBDIRS: tuple[tuple[str, ...], ...] = (
    ("apps", "agents"),
    ("apps", "api", "app", "services"),
)

ADR_SUBDIR: tuple[str, ...] = ("docs", "decisions", "036-foundry-rag-grounding")


def _scan_markers(root: Path) -> list[tuple[Path, int, str, str]]:
    """Return ``(file, line, ordinal, reason)`` tuples for every marker found."""
    out: list[tuple[Path, int, str, str]] = []
    for parts in SCAN_SUBDIRS:
        scan_root = root.joinpath(*parts)
        if not scan_root.exists():
            continue
        for py in scan_root.rglob("*.py"):
            if "__pycache__" in py.parts:
                continue
            try:
                text = py.read_text(encoding="utf-8")
            except OSError:
                continue
            for lineno, line in enumerate(text.splitlines(), 1):
                m = MARKER_RE.search(line)
                if not m:
                    continue
                out.append((py, lineno, m.group(1), (m.group("reason") or "").strip()))
    return out


def _adr_files(root: Path) -> dict[str, Path]:
    """Map ordinal → ADR path for every well-formed ADR file."""
    adr_dir = root.joinpath(*ADR_SUBDIR)
    if not adr_dir.exists():
        return {}
    out: dict[str, Path] = {}
    for f in sorted(adr_dir.iterdir()):
        if not f.is_file():
            continue
        m = ADR_FILE_RE.match(f.name)
        if m:
            out[m.group(1)] = f
    return out


def _adr_marker_optional(adr_path: Path) -> bool:
    """An ADR may declare itself marker-optional via front-matter."""
    try:
        text = adr_path.read_text(encoding="utf-8")
    except OSError:
        return False
    return bool(
        re.search(r"^\s*code_marker_optional\s*:\s*true", text, re.MULTILINE | re.IGNORECASE)
        or re.search(r"\*\*Code[- ]marker optional\*\*\s*:\s*true", text, re.IGNORECASE)
    )


def check(root: Path) -> tuple[bool, list[str]]:
    """Run all four invariants. Return ``(ok, errors)``."""
    errors: list[str] = []

    adrs = _adr_files(root)
    markers = _scan_markers(root)

    # 1. FR coverage.
    missing_adrs = [o for o in ALL_FR_ORDINALS if o not in adrs]
    if missing_adrs:
        errors.append(
            "[fr-coverage] missing ADR(s): "
            + ", ".join(f"FR-RAG-NS-{o}" for o in missing_adrs)
        )

    # 2. Marker → ADR.
    for path, lineno, ordinal, _reason in markers:
        if ordinal not in adrs:
            errors.append(
                f"[orphan-marker] {path.relative_to(root)}:{lineno} "
                f"→ FR-RAG-NS-{ordinal} has no ADR file"
            )

    # 3. Canonical form.
    for path, lineno, _ordinal, _reason in markers:
        try:
            line = path.read_text(encoding="utf-8").splitlines()[lineno - 1]
        except (OSError, IndexError):
            continue
        if not CANONICAL_RE.search(line):
            errors.append(
                f"[non-canonical] {path.relative_to(root)}:{lineno} "
                f"→ {line.strip()!r}"
            )

    # 4. ADR → marker (with marker-optional escape hatch + meta-ADR exemption).
    referenced = {ordinal for _, _, ordinal, _ in markers}
    for ordinal, adr_path in adrs.items():
        if ordinal == "08":  # lint meta-ADR
            continue
        if ordinal in referenced:
            continue
        if _adr_marker_optional(adr_path):
            continue
        errors.append(
            f"[unreferenced-adr] FR-RAG-NS-{ordinal} "
            f"({adr_path.relative_to(root)}) has no code marker and no "
            "``code_marker_optional: true`` declaration"
        )

    # 5. At least one marker must exist (smoke).
    if not markers:
        errors.append(
            "[no-markers] no RAG-OPTOUT markers found in apps/agents or "
            "apps/api/app/services — production carve-outs MUST carry markers"
        )

    return (not errors), errors


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else "")
    p.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
        help="Repository root (default: detected from script location).",
    )
    args = p.parse_args(argv)

    root: Path = args.root.resolve()
    sys.stdout.write(f"[rag-optout-lint] root: {root}\n")

    ok, errors = check(root)
    if ok:
        sys.stdout.write(
            "[rag-optout-lint] OK — every marker, every ADR, every "
            "FR-RAG-NS-NN binding is consistent.\n"
        )
        return 0

    sys.stdout.write(f"[rag-optout-lint] FAILED with {len(errors)} error(s):\n")
    for e in errors:
        sys.stdout.write(f"  {e}\n")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
