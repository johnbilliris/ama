"""Equivalence harness CLI (T024, FR-023).

Loads per-agent fixtures from ``tests/equivalence/fixtures/<agent>/``, replays
each through the legacy pipeline AND the MAF agent, scores via
``maf_runtime.equivalence.scorers.score``, and emits Markdown + JSON reports
under ``apps/agents/maf_runtime/equivalence/reports/<agent>-<UTC-timestamp>.{md,json}``.

Supports ``--dry-run`` for CI bootstrap before fixtures are populated (succeeds
with a zero-cases report).
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .scorers import EquivalenceVerdict, score

logger = logging.getLogger(__name__)


REPORTS_DIR = Path(__file__).resolve().parent / "reports"
DEFAULT_FIXTURES_ROOT = Path("tests/equivalence/fixtures")


def _load_fixture_pairs(agent: str, fixtures_root: Path) -> list[tuple[str, Any, Any]]:
    """Load (case_id, legacy_output, maf_output) tuples from JSON files.

    Each fixture file is expected to be JSON with this shape::

        {
          "case_id": "...",
          "input": {...},          # echoed for debugging
          "legacy_output": {...},  # captured pre-MAF
          "maf_output": {...}      # captured during the equivalence run
        }
    """
    agent_dir = fixtures_root / agent
    if not agent_dir.exists():
        return []
    pairs: list[tuple[str, Any, Any]] = []
    for fp in sorted(agent_dir.glob("*.json")):
        try:
            doc = json.loads(fp.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            logger.exception("Failed to parse fixture %s; skipping", fp)
            continue
        case_id = doc.get("case_id", fp.stem)
        legacy = doc.get("legacy_output")
        maf = doc.get("maf_output")
        if legacy is None and maf is None:
            continue
        pairs.append((case_id, legacy, maf))
    return pairs


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="MAF equivalence harness (FR-023).")
    parser.add_argument("--agent", required=True, choices=[
        "monitoring", "risk_assessment", "evacuation", "resource_allocation", "communication",
    ])
    parser.add_argument("--fixtures-root", type=Path, default=DEFAULT_FIXTURES_ROOT)
    parser.add_argument("--dry-run", action="store_true", help="Skip fixture loading; emit a zero-cases report.")
    parser.add_argument("--reports-dir", type=Path, default=REPORTS_DIR)
    args = parser.parse_args(argv)

    if args.dry_run:
        pairs: list[tuple[str, Any, Any]] = []
    else:
        pairs = _load_fixture_pairs(args.agent, args.fixtures_root)

    report = score(agent_name=args.agent, pairs=pairs)

    args.reports_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    md_path = args.reports_dir / f"{args.agent}-{timestamp}.md"
    json_path = args.reports_dir / f"{args.agent}-{timestamp}.json"
    md_path.write_text(report.to_markdown(), encoding="utf-8")
    json_path.write_text(report.to_json(), encoding="utf-8")

    logger.info("equivalence_report_written agent=%s verdict=%s", args.agent, report.verdict.value)
    print(f"verdict={report.verdict.value} report_md={md_path} report_json={json_path}")
    return 0 if report.verdict == EquivalenceVerdict.PASS else 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
