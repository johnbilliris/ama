"""CLI entry: `python -m evidence_pack_gate [--dry-run] [--repo-root PATH]`."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .gate import run_gate


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Spec-037 publication gate")
    parser.add_argument("--repo-root", type=Path, default=None)
    parser.add_argument("--dry-run", action="store_true", help="Skip emitting metrics")
    args = parser.parse_args(argv)

    result = run_gate(args.repo_root, dry_run=args.dry_run)
    print(f"evidence-pack-publication-gate: {result.artefacts_seen} artefact(s)")
    if result.passed:
        print("PASS")
        return 0
    print("FAIL")
    for f in result.failures:
        print(f"  - {f}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
