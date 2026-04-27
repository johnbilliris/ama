"""T061 — Freeze controller (FR-019, FR-020).

Activates / deactivates a change-freeze window. Emits ``freeze.activate`` /
``freeze.deactivate`` audit events. Persists state to a JSON file consumed by
the PR-gates and CD workflows; the workflows refuse to deploy when freeze is
active unless ``emergency-hotfix`` label is present and signed off by the
incident commander.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

from pipeline_tools.audit_emitter import emit

LOG = logging.getLogger("freeze_controller")


def _read_state(path: Path) -> dict:
    if not path.exists():
        return {"active": False, "reason": None, "activated_at": None, "deactivated_at": None}
    return json.loads(path.read_text(encoding="utf-8"))


def _write_state(path: Path, state: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Freeze controller (FR-019, FR-020)")
    parser.add_argument("--state-file", type=Path, default=Path(".github/state/freeze.json"))
    parser.add_argument("--audit-actor", default=os.environ.get("GITHUB_ACTOR", "freeze-controller"))
    parser.add_argument("--dry-run", action="store_true")
    sub = parser.add_subparsers(dest="cmd", required=True)
    activate = sub.add_parser("activate")
    activate.add_argument("--reason", required=True)
    sub.add_parser("deactivate")
    sub.add_parser("status")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    state = _read_state(args.state_file)
    now = datetime.now(tz=UTC).isoformat().replace("+00:00", "Z")

    if args.cmd == "activate":
        state.update({"active": True, "reason": args.reason, "activated_at": now})
        _write_state(args.state_file, state)
        emit(
            action="freeze.activate", actor=args.audit_actor, outcome="success",
            rationale=args.reason, dry_run=args.dry_run,
        )
        print("freeze active")
        return 0
    if args.cmd == "deactivate":
        state.update({"active": False, "deactivated_at": now})
        _write_state(args.state_file, state)
        emit(
            action="freeze.deactivate", actor=args.audit_actor, outcome="success",
            rationale=state.get("reason"), dry_run=args.dry_run,
        )
        print("freeze cleared")
        return 0
    print(json.dumps(state))
    return 0 if not state.get("active") else 1


if __name__ == "__main__":
    sys.exit(main())
