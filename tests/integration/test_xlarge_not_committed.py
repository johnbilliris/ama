"""Spec-039 T102 — committed fixtures must not exceed 1000 records (CL-3, R7).

Walks ``fixtures/`` and the seed catalogue dirs and fails if any committed
``*.ndjson`` / ``*.json`` carries > 1000 records. xlarge volumes are
generator-produced at runtime and never committed.
"""

from __future__ import annotations

import json
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
SCAN_ROOTS = (
    "fixtures",
    "packages/domain/src/domain/seed",
    "apps/api/app/services/simulation/data",
    "data",
)
LIMIT = 1000


def _record_count(p: Path) -> int:
    suffix = p.suffix.lower()
    if suffix in (".ndjson", ".jsonl"):
        with p.open("r", encoding="utf-8") as fh:
            return sum(1 for line in fh if line.strip())
    if suffix == ".json":
        try:
            doc = json.loads(p.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return 0
        if isinstance(doc, dict):
            recs = doc.get("records")
            if isinstance(recs, list):
                return len(recs)
            return 0
        if isinstance(doc, list):
            return len(doc)
    return 0


def test_no_committed_fixture_over_1000_records() -> None:
    offenders: list[tuple[str, int]] = []
    for root in SCAN_ROOTS:
        base = _REPO / root
        if not base.exists():
            continue
        for p in base.rglob("*"):
            if not p.is_file():
                continue
            if p.suffix.lower() not in (".json", ".jsonl", ".ndjson"):
                continue
            n = _record_count(p)
            if n > LIMIT:
                offenders.append((p.relative_to(_REPO).as_posix(), n))
    assert not offenders, f"committed fixtures exceed {LIMIT} records (CL-3): {offenders}"
