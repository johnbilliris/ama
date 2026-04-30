"""Dashboard field snapshot — captures the field set referenced by every existing operator workbook query.

Implements T024b for FR-017 / SC-009 (dashboards continue to render with no per-agent gaps).

Walks ``infra/bicep/modules/dashboards/`` (or any subdirectory containing
``*.workbook.json`` / ``.bicep`` files referencing KQL via ``query:`` /
``serializedData``) and extracts:

- Top-level KQL column references (``| project ...`` / ``| extend ...`` / ``customDimensions.<field>``)
- Application Insights span attribute references (``customDimensions.<field>``)
- Cosmos query projections (``SELECT c.<field>``)

Writes a deterministic JSON snapshot at ``tests/contract/snapshots/existing_dashboard_fields.json``
that ``tests/contract/test_existing_dashboards_no_regression.py`` (T060b) reads
post-cutover to assert no field-level regression.

Run via:

    python -m apps.agents.maf_runtime.equivalence.dashboard_snapshot
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from pathlib import Path

logger = logging.getLogger(__name__)


REPO_ROOT = Path(__file__).resolve().parents[4]
DASHBOARDS_DIR = REPO_ROOT / "infra" / "bicep" / "modules" / "dashboards"
DEFAULT_SNAPSHOT_PATH = REPO_ROOT / "tests" / "contract" / "snapshots" / "existing_dashboard_fields.json"


_CUSTOM_DIM_RE = re.compile(r"customDimensions\.([A-Za-z_][A-Za-z0-9_]*)")
_CUSTOM_DIM_BRACKET_RE = re.compile(r"customDimensions\['([A-Za-z_][A-Za-z0-9_]*)'\]")
_PROJECT_RE = re.compile(r"\|\s*project\s+([^|]+)")
_EXTEND_RE = re.compile(r"\|\s*extend\s+([^|]+)")
_COSMOS_SELECT_RE = re.compile(r"SELECT\s+([^FROM]+)\s+FROM", re.IGNORECASE)


def _extract_fields_from_text(text: str) -> set[str]:
    fields: set[str] = set()
    for m in _CUSTOM_DIM_RE.finditer(text):
        fields.add(m.group(1))
    for m in _CUSTOM_DIM_BRACKET_RE.finditer(text):
        fields.add(m.group(1))
    for m in _PROJECT_RE.finditer(text):
        for tok in m.group(1).split(","):
            tok = tok.strip().split("=", 1)[0].strip()
            if tok and re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", tok):
                fields.add(tok)
    for m in _EXTEND_RE.finditer(text):
        for tok in m.group(1).split(","):
            tok = tok.strip().split("=", 1)[0].strip()
            if tok and re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", tok):
                fields.add(tok)
    for m in _COSMOS_SELECT_RE.finditer(text):
        for tok in m.group(1).split(","):
            tok = tok.strip()
            if tok.startswith("c."):
                tok = tok[2:]
            tok = tok.split(" ")[0]
            if tok and re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", tok):
                fields.add(tok)
    return fields


def collect_fields(roots: list[Path]) -> dict[str, list[str]]:
    """Walk *roots* and return a map of {file_relative_path: sorted field names}."""
    result: dict[str, list[str]] = {}
    for root in roots:
        if not root.exists():
            continue
        for fp in sorted(root.rglob("*")):
            if fp.is_file() and fp.suffix.lower() in {".bicep", ".json", ".kql"}:
                try:
                    text = fp.read_text(encoding="utf-8", errors="replace")
                except Exception:  # noqa: BLE001
                    continue
                fields = _extract_fields_from_text(text)
                if fields:
                    rel = fp.relative_to(REPO_ROOT).as_posix()
                    result[rel] = sorted(fields)
    return result


def write_snapshot(snapshot_path: Path, fields_by_file: dict[str, list[str]]) -> None:
    snapshot_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "_meta": {
            "purpose": "Pre-MAF dashboard field snapshot (T024b → T060b regression test)",
            "schema": "{file_path: [field, ...]}",
        },
        "fields_by_file": fields_by_file,
    }
    snapshot_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot-path", type=Path, default=DEFAULT_SNAPSHOT_PATH)
    parser.add_argument("--root", type=Path, action="append", default=None,
                        help="Repeatable: directories to scan. Default: infra/bicep/modules/dashboards/.")
    args = parser.parse_args(argv)
    roots = args.root or [DASHBOARDS_DIR]
    fields = collect_fields(roots)
    write_snapshot(args.snapshot_path, fields)
    total = sum(len(v) for v in fields.values())
    print(
        f"Wrote {args.snapshot_path} (files={len(fields)}, total_fields={total})."
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
