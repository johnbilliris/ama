"""Known-good manifest CLI (T049 + T160).

Maintains ``specs/034-webapp-capstone-coverage/known-good.json`` — the FR-027
rollback manifest. Each entry pins a (persona, outcome, hazard, fr_id) tuple
to the most recent commit/PR where the matching coverage trace row was
``status=passed``.

Subcommands:

  record     Append a new known-good entry from a passing trace row.
  rollback   Print the known-good revision for a tuple (used by CI on regression).
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
        return {"spec": "034-webapp-capstone-coverage", "schema_version": 1, "entries": {}}
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def save_manifest(payload: dict) -> None:
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


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
        "recorded_at": datetime.now(UTC).isoformat(timespec="seconds"),
    }
    save_manifest(manifest)
    append_audit(AUDIT_ROOT, "known-good-recorded", manifest["entries"][key])


def cmd_rollback(args: argparse.Namespace) -> None:
    manifest = load_manifest()
    key = _key(args.persona, args.outcome, args.hazard, args.fr_id)
    entry = manifest["entries"].get(key)
    if not entry:
        sys.stderr.write(f"known-good: no entry for {key}\n")
        sys.exit(2)
    json.dump(entry, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    append_audit(AUDIT_ROOT, "known-good-rollback-queried", {"key": key})


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

    p_roll = sub.add_parser("rollback", help="print known-good revision for a tuple")
    p_roll.add_argument("--persona", required=True)
    p_roll.add_argument("--outcome", type=int, choices=[1, 2, 3, 4, 5], required=True)
    p_roll.add_argument("--hazard", required=True)
    p_roll.add_argument("--fr-id", required=True)
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
