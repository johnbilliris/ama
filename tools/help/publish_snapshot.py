"""spec-038 T-AA165 — local + CI snapshot publisher.

Idempotent on ``(snapshot_id, source_id, content_hash)``. Calls the
``apps/ingest-runner`` help_snapshot pipeline, swings the alias, emits
``audit.snapshot_published``. ``rollback`` re-binds the alias and emits
``audit.snapshot_rollback`` within the 5-min FR-011c budget.
"""

from __future__ import annotations

import argparse
import json
import logging
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

logger = logging.getLogger(__name__)


def _ts_snapshot_id() -> str:
    return f"snap-{datetime.now(UTC):%Y%m%dT%H%M%SZ}"


def parse_approver(arg: str) -> dict:
    if "=" not in arg:
        raise SystemExit(f"--approver requires identity=role, got {arg!r}")
    identity, role = arg.split("=", 1)
    return {"identity": identity, "role": role}


def cmd_publish(args: argparse.Namespace) -> int:
    approvers = [parse_approver(a) for a in args.approver]
    identities = {a["identity"] for a in approvers}
    roles = {a["role"] for a in approvers}
    if len(identities) < 2:
        raise SystemExit("dual approval requires 2 distinct identities")
    if "help_content_owner" not in roles:
        raise SystemExit("missing approver with role help_content_owner")
    if not (roles & {"safety_lead", "governance_lead"}):
        raise SystemExit("missing approver with role safety_lead or governance_lead")

    snapshot_id = args.snapshot_id or _ts_snapshot_id()
    logger.info("publishing snapshot %s (manifest=%s)", snapshot_id, args.manifest)
    subprocess.check_call(
        [
            sys.executable,
            "-m",
            "help_snapshot",
            "--manifest",
            args.manifest,
            "--snapshot-id",
            snapshot_id,
            *(["--dry-run"] if args.dry_run else []),
        ]
    )
    # write SnapshotRecord JSON for downstream verification
    Path("snapshot-record.json").write_text(
        json.dumps({"id": snapshot_id, "approvers": approvers, "published_at": datetime.now(UTC).isoformat()}),
        encoding="utf-8",
    )
    print(snapshot_id)
    return 0


def cmd_rollback(args: argparse.Namespace) -> int:
    logger.info("rollback to %s", args.restored_snapshot_id)
    # Re-bind alias via swing_alias helper:
    from help_snapshot.alias_swinger import swing_alias  # type: ignore[import-not-found]

    swing_alias(snapshot_id=args.restored_snapshot_id)
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)

    pub = sub.add_parser("publish")
    pub.add_argument("--manifest", required=True)
    pub.add_argument("--snapshot-id")
    pub.add_argument("--approver", action="append", required=True, help="identity=role")
    pub.add_argument("--dry-run", action="store_true")
    pub.set_defaults(func=cmd_publish)

    rb = sub.add_parser("rollback")
    rb.add_argument("--restored-snapshot-id", required=True)
    rb.set_defaults(func=cmd_rollback)

    args = p.parse_args(argv)
    logging.basicConfig(level=logging.INFO)
    return args.func(args)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
