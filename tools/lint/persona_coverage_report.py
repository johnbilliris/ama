"""Spec-038 T163 (Phase 7) — persona-coverage report CLI.

Thin wrapper around the same logic as
``tests/integration/test_persona_coverage_zero_unbacked.py`` (FR-060,
SC-001, SC-008, SC-012). Emits a tabular summary on stderr (mirroring the
``check_test_data_manifest.py`` style) and exits non-zero on coverage gaps.

Run::

    python tools/lint/persona_coverage_report.py            # human summary
    python tools/lint/persona_coverage_report.py --strict   # exit 1 if any gap

The "coverage gap" condition is identical to the integration test:
    1. Every one of the 68 personas in ``PERSONA_ROSTERS`` resolves to ≥1
       manifest entry's ``persona_bindings``.
    2. Every of the 8 domain groups appears as ``domain_group`` on ≥1 entry.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "tools" / "lint"))

from build_test_data_manifest import PERSONA_ROSTERS  # noqa: E402

MANIFEST = REPO_ROOT / "docs" / "test-data" / "manifest.json"


def _load_manifest_bindings() -> tuple[dict[str, int], set[str]]:
    doc = json.loads(MANIFEST.read_text(encoding="utf-8"))
    counts: dict[str, int] = {}
    groups: set[str] = set()
    for e in doc.get("entries", []):
        for p in e.get("persona_bindings", []) or []:
            counts[p] = counts.get(p, 0) + 1
        g = e.get("domain_group")
        if g:
            groups.add(g)
    return counts, groups


def _emit_table(counts: dict[str, int], groups: set[str]) -> tuple[int, int, list[str], list[str]]:
    print("persona-coverage-report — spec 038", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    total_personas = 0
    covered = 0
    missing_personas: list[str] = []
    for group in sorted(PERSONA_ROSTERS):
        roster = sorted(PERSONA_ROSTERS[group])
        group_in_manifest = "yes" if group in groups else "NO"
        print(
            f"  domain_group={group:<16}  personas={len(roster):>2}  "
            f"in_manifest={group_in_manifest}",
            file=sys.stderr,
        )
        for persona in roster:
            total_personas += 1
            n = counts.get(persona, 0)
            mark = "OK " if n > 0 else "GAP"
            print(f"    [{mark}] {persona:<32}  entries={n}", file=sys.stderr)
            if n > 0:
                covered += 1
            else:
                missing_personas.append(persona)
    missing_groups = sorted(set(PERSONA_ROSTERS) - groups)
    print("-" * 60, file=sys.stderr)
    print(
        f"summary: domain_groups={len(PERSONA_ROSTERS)} "
        f"({len(PERSONA_ROSTERS) - len(missing_groups)} present); "
        f"personas={total_personas} ({covered} covered, "
        f"{len(missing_personas)} unbacked)",
        file=sys.stderr,
    )
    return total_personas, covered, missing_personas, missing_groups


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--strict",
        action="store_true",
        help="Exit 1 if any persona is unbacked or any domain group is missing.",
    )
    p.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON summary on stdout.",
    )
    args = p.parse_args(argv)

    counts, groups = _load_manifest_bindings()
    total, covered, missing_p, missing_g = _emit_table(counts, groups)

    if args.json:
        print(
            json.dumps(
                {
                    "manifest": str(MANIFEST.relative_to(REPO_ROOT)),
                    "domain_groups_total": len(PERSONA_ROSTERS),
                    "domain_groups_missing": missing_g,
                    "personas_total": total,
                    "personas_covered": covered,
                    "personas_unbacked": missing_p,
                },
                indent=2,
                sort_keys=True,
            )
        )

    if missing_p or missing_g:
        if args.strict:
            print(
                f"FAIL: {len(missing_p)} unbacked personas; "
                f"{len(missing_g)} missing domain groups.",
                file=sys.stderr,
            )
            return 1
        print(
            "WARN: coverage gaps present (use --strict to fail).",
            file=sys.stderr,
        )
        return 0
    print(
        f"clean: {len(PERSONA_ROSTERS)} domain groups + {total} personas all backed.",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
