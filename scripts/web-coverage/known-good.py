"""Known-good manifest CLI (T049 + T155 + T160).

Maintains ``specs/034-webapp-capstone-coverage/known-good.json`` — the FR-027
rollback manifest. Each entry pins a (persona, outcome, hazard, fr_id) tuple
to the most recent commit/PR where the matching coverage trace row was
``status=passed``. The manifest also tracks ``last_regression`` so a CI
regression event can name the failing Test ID + reverted commit SHA + restored
revision SHA in one place.

Subcommands:

  record     Append a single known-good entry from a passing trace row.
  update     Refresh the manifest after a successful deploy (cd.yml T155):
             walks the merged trace, records every passing row, clears
             ``last_regression`` only if the manifest had none before.
  rollback   Compose with the cd.yml 5-min auto-rollback by stamping
             ``last_regression`` with the failing Test ID, the reverted commit
             SHA, and the restored revision SHA (FR-027).
  list       Print the manifest JSON.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

# Ensure ``_lib`` is importable when this CLI is invoked from any cwd.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _lib.audit_append import append_audit  # noqa: E402, I001


REPO_ROOT = Path(__file__).resolve().parents[2]
SPEC_ROOT = REPO_ROOT / "specs" / "034-webapp-capstone-coverage"
MANIFEST = SPEC_ROOT / "known-good.json"
AUDIT_ROOT = SPEC_ROOT / "_evidence" / "audit" / "web-coverage-known-good"


def load_manifest() -> dict:
    if not MANIFEST.exists():
        return {
            "spec": "034-webapp-capstone-coverage",
            "schema_version": 1,
            "entries": {},
            "last_regression": None,
            "last_updated_at": None,
            "last_updated_commit": None,
        }
    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    payload.setdefault("entries", {})
    payload.setdefault("last_regression", None)
    payload.setdefault("last_updated_at", None)
    payload.setdefault("last_updated_commit", None)
    return payload


def save_manifest(payload: dict) -> None:
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def _key(persona: str, outcome: int, hazard: str, fr_id: str) -> str:
    return f"{persona}|{outcome}|{hazard}|{fr_id}"


def cmd_record(args: argparse.Namespace) -> None:
    manifest = load_manifest()
    key = _key(args.persona, args.outcome, args.hazard, args.fr_id)
    manifest["entries"][key] = {
        "persona_id": args.persona,
        "outcome": args.outcome,
        "hazard": args.hazard,
        "fr_id": args.fr_id,
        "merge_sha": args.merge_sha,
        "pr_url": args.pr_url,
        "recorded_at": _now_iso(),
    }
    save_manifest(manifest)
    append_audit(AUDIT_ROOT, "known-good-recorded", manifest["entries"][key])


def cmd_update(args: argparse.Namespace) -> None:
    """Refresh the manifest from a fully-passing trace at a green deploy.

    Called from ``.github/workflows/cd.yml`` after ``record-revisions``. Reads
    the merged ``coverage-trace.json``, records every row where status=passed
    against the deploy commit + revisions JSON, and persists the manifest.
    Skips silently when the trace file is missing (e.g., first deploy).
    """

    trace_path = Path(args.trace)
    if not trace_path.exists():
        sys.stderr.write(f"known-good update: trace missing at {trace_path}; skipping\n")
        return
    trace = json.loads(trace_path.read_text(encoding="utf-8"))
    rows = trace if isinstance(trace, list) else trace.get("rows", [])

    revisions: dict = {}
    if args.revisions_json:
        try:
            revisions = json.loads(args.revisions_json)
        except json.JSONDecodeError:
            sys.stderr.write("known-good update: revisions-json is not valid JSON; ignoring\n")
            revisions = {}

    manifest = load_manifest()
    recorded = 0
    for row in rows:
        if row.get("status") != "passed":
            continue
        key = _key(
            row["persona_id"],
            int(row["outcome"]),
            row["hazard"],
            row["fr_id"],
        )
        manifest["entries"][key] = {
            "persona_id": row["persona_id"],
            "outcome": int(row["outcome"]),
            "hazard": row["hazard"],
            "fr_id": row["fr_id"],
            "merge_sha": args.commit,
            "revisions": revisions,
            "recorded_at": _now_iso(),
        }
        recorded += 1
    manifest["last_updated_at"] = _now_iso()
    manifest["last_updated_commit"] = args.commit
    save_manifest(manifest)
    append_audit(
        AUDIT_ROOT,
        "known-good-updated",
        {"commit": args.commit, "recorded_entries": recorded},
    )
    sys.stdout.write(f"known-good update: refreshed {recorded} entries at {args.commit}\n")


def cmd_rollback(args: argparse.Namespace) -> None:
    """Stamp the manifest with rollback evidence.

    Composes with cd.yml's 5-min auto-rollback: scripts/rollback.sh reverts
    the deploy, then this command records the failing Test ID + reverted
    commit SHA + restored revision SHA against the gap so a re-deploy can
    look up the prior known-good state.
    """

    manifest = load_manifest()
    manifest["last_regression"] = {
        "gap_id": args.gap_id,
        "failing_test_id": args.failing_test_id,
        "reverted_commit_sha": args.reverted_sha,
        "restored_revision_sha": args.restored_sha,
        "rolled_back_at": _now_iso(),
    }
    save_manifest(manifest)
    append_audit(AUDIT_ROOT, "known-good-rollback", manifest["last_regression"])
    json.dump(manifest["last_regression"], sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")


def cmd_list(_args: argparse.Namespace) -> None:
    json.dump(load_manifest(), sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="command", required=True)

    p_record = sub.add_parser("record", help="record a passing tuple's commit/PR")
    p_record.add_argument("--persona", required=True)
    p_record.add_argument("--outcome", type=int, choices=[1, 2, 3, 4, 5], required=True)
    p_record.add_argument("--hazard", required=True)
    p_record.add_argument("--fr-id", required=True)
    p_record.add_argument("--merge-sha", required=True)
    p_record.add_argument("--pr-url", required=True)
    p_record.set_defaults(func=cmd_record)

    p_update = sub.add_parser("update", help="refresh manifest from a passing trace (cd.yml)")
    p_update.add_argument("--commit", required=True)
    p_update.add_argument("--revisions-json", default="{}")
    p_update.add_argument("--trace", required=True)
    p_update.set_defaults(func=cmd_update)

    p_roll = sub.add_parser("rollback", help="record rollback evidence (FR-027)")
    p_roll.add_argument("--gap-id", required=True)
    p_roll.add_argument("--failing-test-id", required=True)
    p_roll.add_argument("--reverted-sha", required=True)
    p_roll.add_argument("--restored-sha", required=True)
    p_roll.set_defaults(func=cmd_rollback)

    p_list = sub.add_parser("list", help="print manifest JSON to stdout")
    p_list.set_defaults(func=cmd_list)

    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    args.func(args)
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    sys.exit(main())
