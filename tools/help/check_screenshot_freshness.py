"""spec-038 T-AA174 — screen freshness check.

Recomputes ``screen_id_hash`` from the current build's route registry +
anchor set and compares with the value stored in the snapshot
``screenshot_registry``. Mismatches raise a :class:`StalenessFlag`.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from ama_domain import compute_screen_id_hash  # type: ignore[attr-defined]

logger = logging.getLogger(__name__)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--registry", required=True, help="path to JSON describing current routes + anchors")
    p.add_argument("--baseline", required=True, help="path to JSON snapshot_registry baseline")
    p.add_argument("--register-only", action="store_true")
    args = p.parse_args(argv)
    logging.basicConfig(level=logging.INFO)

    current = json.loads(Path(args.registry).read_text(encoding="utf-8"))
    baseline = json.loads(Path(args.baseline).read_text(encoding="utf-8"))

    flags: list[dict] = []
    for route_id, info in current.items():
        anchors = info.get("anchors", [])
        h = compute_screen_id_hash(route_id, anchors)
        prev = baseline.get(route_id, {}).get("screen_id_hash")
        if args.register_only:
            baseline.setdefault(route_id, {})["screen_id_hash"] = h
        elif prev and prev != h:
            flags.append({"route_id": route_id, "previous": prev, "current": h})
            logger.warning("staleness flag: %s %s -> %s", route_id, prev, h)

    if args.register_only:
        Path(args.baseline).write_text(json.dumps(baseline, indent=2), encoding="utf-8")
        return 0
    if flags:
        Path("staleness-report.json").write_text(json.dumps(flags, indent=2), encoding="utf-8")
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
