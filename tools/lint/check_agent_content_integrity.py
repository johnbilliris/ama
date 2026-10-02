#!/usr/bin/env python3
"""Validate agent markdown integrity for control bytes, fences, and path references.

This linter is intentionally conservative and supports explicit illustrative/proposed
allow semantics to avoid flagging placeholder examples.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

FORBIDDEN_CTRL = {*range(0, 9), 11, 12, *range(14, 32), 127}
ALLOWED_REF_PREFIXES = (
    ".github/",
    ".specify/",
    "apps/",
    "artifacts/",
    "contracts/",
    "data/",
    "docs/",
    "fixtures/",
    "infra/",
    "packages/",
    "scripts/",
    "specs/",
    "tests/",
    "tools/",
)
PATH_TOKEN_RE = re.compile(r"(?<![A-Za-z0-9_./-])([./]?[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.{}<>-]+)+)(?![A-Za-z0-9_./-])")
ILLUSTRATIVE_RE = re.compile(r"\b(illustrative|example|proposed|placeholder|convention)\b", re.IGNORECASE)
MALFORMED_FENCE_RE = re.compile(r"^\s*`[A-Za-z0-9_-]*\s*$")


def iter_targets(paths: list[Path]) -> list[Path]:
    out: list[Path] = []
    for p in paths:
        if p.is_file() and p.suffix.lower() == ".md":
            out.append(p)
            continue
        if p.is_dir():
            out.extend(sorted(p.rglob("*.md")))
    return out


def likely_repo_relative(token: str) -> bool:
    normalized = token.lstrip("./")
    if token.startswith("../"):
        return False
    if token.startswith("http://") or token.startswith("https://"):
        return False
    return normalized.startswith(ALLOWED_REF_PREFIXES)


def normalize_candidate(token: str) -> str:
    token = token.strip("`[](){}<>,.:;!\"'")
    return token.replace("\\", "/").lstrip("./")


def validate_file(path: Path, repo_root: Path) -> list[str]:
    errors: list[str] = []
    raw = path.read_bytes()

    for i, b in enumerate(raw):
        if b in FORBIDDEN_CTRL:
            errors.append(f"{path}:{i + 1}: forbidden control byte 0x{b:02x}")

    text = raw.decode("utf-8", errors="replace")
    lines = text.splitlines()

    for line_no, line in enumerate(lines, start=1):
        if "\t" in line and re.search(r"\S\t\S|\t\S", line):
            errors.append(f"{path}:{line_no}: tab appears inside or directly before token")
        if "\r" in line and re.search(r"\S\r\S|\r\S", line):
            errors.append(f"{path}:{line_no}: carriage return appears inside token")
        if MALFORMED_FENCE_RE.match(line):
            errors.append(f"{path}:{line_no}: malformed code fence line")

        illustrative = bool(ILLUSTRATIVE_RE.search(line))
        for m in PATH_TOKEN_RE.finditer(line):
            token = m.group(1)
            if not likely_repo_relative(token):
                continue
            candidate = normalize_candidate(token)
            if "{" in candidate or "<" in candidate:
                if illustrative:
                    continue
                errors.append(f"{path}:{line_no}: unresolved templated reference '{token}' without illustrative marker")
                continue
            full = repo_root / candidate
            if not full.exists() and not illustrative:
                errors.append(f"{path}:{line_no}: unresolved repo-relative reference '{token}'")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate actor markdown integrity")
    parser.add_argument("paths", nargs="*", default=[".github/agents"], help="Files or directories to scan")
    parser.add_argument("--repo-root", default=".", help="Repository root used to resolve references")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    targets = iter_targets([Path(p).resolve() for p in args.paths])

    all_errors: list[str] = []
    for file_path in targets:
        all_errors.extend(validate_file(file_path, repo_root))

    if all_errors:
        for err in all_errors:
            print(err)
        return 1

    print(f"OK: {len(targets)} markdown files passed integrity checks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
