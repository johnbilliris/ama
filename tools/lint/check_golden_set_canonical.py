"""Spec 036 / F-A10 / T220 — golden-set canonicalisation lint.

Per Pass 1 Q-P1-08 + FR-RAG-TEST-03 — there must be exactly ONE
golden-set fixture (``tests/fixtures/golden-set-v1.json``) and every
historical reference must point at it. This script fails CI when:

1. ``tests/fixtures/golden-set-v1.json`` is missing.
2. Any other ``golden-set*.json`` exists under ``tests/fixtures/``.
3. The required tags (``agency_disambiguation``, national-institution
   marker) fall below the SC-013 / SC-015 floors.

Usage:
    python tools/lint/check_golden_set_canonical.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "tests" / "fixtures" / "golden-set-v1.json"
FIXTURE_DIR = ROOT / "tests" / "fixtures"

# SC-013 floor — ≥20 agency_disambiguation entries; SC-015 floor —
# ≥20 national-institution / authority_precedence entries.
TAG_FLOORS: dict[str, int] = {
    "agency_disambiguation": 20,
    "authority_precedence": 20,
}


def main() -> int:
    errors: list[str] = []

    if not FIXTURE.exists():
        errors.append(f"missing canonical fixture: {FIXTURE.relative_to(ROOT)}")
        return _emit(errors)

    # Walk fixture dir for sibling golden-set files (other than v1).
    for path in FIXTURE_DIR.glob("golden-set*"):
        if path.name == "golden-set-v1.json":
            continue
        if path.suffix.lower() in {".json", ".jsonl", ".yaml", ".yml"}:
            errors.append(
                f"non-canonical fixture detected: {path.relative_to(ROOT)} "
                "(consolidate into golden-set-v1.json per Pass 1 Q-P1-08)"
            )

    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    if isinstance(payload, dict) and "entries" in payload:
        entries = payload["entries"]
    elif isinstance(payload, list):
        entries = payload
    else:
        errors.append("golden-set-v1.json must be a JSON array OR an object with an 'entries' array")
        return _emit(errors)
    if not isinstance(entries, list):
        errors.append("golden-set-v1.json 'entries' must be a JSON array")
        return _emit(errors)

    tag_counts: dict[str, int] = {tag: 0 for tag in TAG_FLOORS}
    for entry in entries:
        scenario = entry.get("scenario")
        if isinstance(scenario, str) and scenario in tag_counts:
            tag_counts[scenario] += 1
        for tag in entry.get("tags", []) or []:
            if tag in tag_counts:
                tag_counts[tag] += 1

    for tag, floor in TAG_FLOORS.items():
        if tag_counts[tag] < floor:
            errors.append(f"tag '{tag}' has {tag_counts[tag]} entries; floor is {floor} (SC-013 / SC-015)")

    return _emit(errors)


def _emit(errors: list[str]) -> int:
    if not errors:
        print("[OK] golden-set v1 canonical (FR-RAG-TEST-03)")
        return 0
    print("[FAIL] golden-set canonicalisation lint:")
    for err in errors:
        print(f"  - {err}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
