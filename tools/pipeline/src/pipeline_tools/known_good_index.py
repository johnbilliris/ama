"""T025 — Known-good index (FR-011, FR-012).

Maintains the rolling window of last-N successful production deployments per
service so the canary controller can roll back to a known-good marker.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import UTC, datetime
from pathlib import Path

LOG = logging.getLogger("known_good_index")

DEFAULT_WINDOW = 10


def _load(path: Path) -> dict:
    if not path.exists():
        return {"version": 1, "window": DEFAULT_WINDOW, "entries": {}}
    return json.loads(path.read_text(encoding="utf-8"))


def _save(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Known-good index (FR-011, FR-012)")
    parser.add_argument("--index-file", type=Path, default=Path(".github/state/known-good.json"))
    sub = parser.add_subparsers(dest="cmd", required=True)
    add = sub.add_parser("add")
    add.add_argument("--service", required=True)
    add.add_argument("--commit-sha", required=True)
    add.add_argument("--evidence-uri", required=True)
    show = sub.add_parser("latest")
    show.add_argument("--service", required=True)
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    data = _load(args.index_file)
    if args.cmd == "add":
        entries = data["entries"].setdefault(args.service, [])
        entries.insert(0, {
            "commit_sha": args.commit_sha,
            "evidence_uri": args.evidence_uri,
            "recorded_at": datetime.now(tz=UTC).isoformat().replace("+00:00", "Z"),
        })
        del entries[data["window"]:]
        _save(args.index_file, data)
        print(f"recorded {args.commit_sha} for {args.service}")
        return 0
    if args.cmd == "latest":
        entries = data["entries"].get(args.service, [])
        if not entries:
            print("no known-good entry", file=sys.stderr)
            return 1
        print(json.dumps(entries[0]))
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
