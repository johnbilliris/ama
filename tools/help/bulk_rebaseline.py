"""spec-038 T-AA180 — bulk re-baseline tool when route_registry.previous_route_id changes."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from uuid import uuid4

from tools.help.route_registry import REGISTRY  # type: ignore[import-not-found]


def main() -> int:
    bulk_id = f"bulk-{uuid4().hex[:8]}"
    moved = []
    for entry in REGISTRY.values():
        prev = entry.get("previous_route_id")
        if prev:
            moved.append({"from": prev, "to": entry["route_id"], "bulk_baseline_id": bulk_id})
    Path("bulk-rebaseline-report.json").write_text(json.dumps(moved, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
