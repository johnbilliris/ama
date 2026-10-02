from __future__ import annotations

import argparse
import datetime as dt
import fnmatch
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml

AU_ALLOWED_LOCATIONS = {
    "australiaeast",
    "australiasoutheast",
    "australiacentral",
    "australiacentral2",
}


class GateError(RuntimeError):
    pass


def _parse_date(value: str, field: str) -> dt.date:
    try:
        return dt.date.fromisoformat(value)
    except ValueError as exc:
        raise GateError(f"invalid {field}: {value!r} (expected YYYY-MM-DD)") from exc


def _business_days_between(older: dt.date, newer: dt.date) -> int:
    if newer < older:
        return -_business_days_between(newer, older)
    days = 0
    cursor = older
    while cursor < newer:
        cursor += dt.timedelta(days=1)
        if cursor.weekday() < 5:
            days += 1
    return days


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise GateError(f"inventory not found: {path}")
    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise GateError("inventory root must be an object")
    return loaded


def _git_changed_files(base_sha: str, head_sha: str) -> list[str]:
    if not base_sha or not head_sha:
        raise GateError("base_sha and head_sha are required when changed-file arguments are not provided")
    cmd = ["git", "diff", "--name-only", base_sha, head_sha]
    result = subprocess.run(cmd, check=False, capture_output=True, text=True)
    if result.returncode != 0:
        raise GateError(f"git diff failed: {result.stderr.strip()}")
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def _load_waiver(path: Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    if not path.exists():
        raise GateError(f"waiver file not found: {path}")
    if path.suffix.lower() in {".yaml", ".yml"}:
        waiver = yaml.safe_load(path.read_text(encoding="utf-8"))
    else:
        waiver = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(waiver, dict):
        raise GateError("waiver file must contain an object")
    return waiver


def _waiver_is_valid(waiver: dict[str, Any] | None, release_date: dt.date) -> tuple[bool, str]:
    if waiver is None:
        return False, "none"
    required = ["type", "owner", "reason", "expires_on"]
    missing = [key for key in required if not waiver.get(key)]
    if missing:
        raise GateError(f"waiver missing required fields: {', '.join(missing)}")
    waiver_type = str(waiver["type"]).strip().lower()
    if waiver_type not in {"emergency", "not-p1"}:
        raise GateError("waiver type must be 'emergency' or 'not-p1'")
    expires = _parse_date(str(waiver["expires_on"]), "waiver.expires_on")
    if release_date > expires:
        return False, waiver_type
    return True, waiver_type


def _required_metadata_errors(flow: dict[str, Any], release_date: dt.date) -> list[str]:
    errors: list[str] = []
    flow_id = flow.get("flow_id", "<unknown>")
    for key in ("flow_id", "source_paths", "training_pack", "operator_notes", "owner", "last_reviewed", "signed_by", "signed_at"):
        if key not in flow:
            errors.append(f"{flow_id}: missing {key}")

    if errors:
        return errors

    reviewed = _parse_date(str(flow["last_reviewed"]), f"{flow_id}.last_reviewed")
    signed = _parse_date(str(flow["signed_at"]), f"{flow_id}.signed_at")

    reviewed_age = _business_days_between(reviewed, release_date)
    signed_age = _business_days_between(signed, release_date)
    if reviewed_age > 5:
        errors.append(f"{flow_id}: last_reviewed is stale by {reviewed_age} business days (>5)")
    if signed_age > 5:
        errors.append(f"{flow_id}: signed_at is stale by {signed_age} business days (>5)")

    train = flow["training_pack"]
    notes = flow["operator_notes"]
    if not isinstance(train, dict) or not isinstance(notes, dict):
        errors.append(f"{flow_id}: training_pack/operator_notes must be objects")
        return errors

    for bucket_name, bucket in (("training_pack", train), ("operator_notes", notes)):
        for key in ("path", "version", "locale"):
            if key not in bucket or bucket[key] in (None, "", []):
                errors.append(f"{flow_id}: {bucket_name}.{key} is required")
        path_value = bucket.get("path")
        if path_value:
            if not Path(str(path_value)).exists():
                errors.append(f"{flow_id}: {bucket_name}.path does not exist: {path_value}")

    return errors


def run_gate(
    *,
    inventory_path: Path,
    release_date: dt.date,
    changed_files: list[str] | None,
    base_sha: str | None,
    head_sha: str | None,
    waiver_path: Path | None,
) -> tuple[bool, dict[str, Any]]:
    inventory = _load_yaml(inventory_path)
    flows = inventory.get("flows")
    if not isinstance(flows, list) or not flows:
        raise GateError("inventory must define non-empty flows list")

    if changed_files:
        changed = sorted({f.replace("\\", "/") for f in changed_files if f.strip()})
    else:
        changed = sorted({f.replace("\\", "/") for f in _git_changed_files(base_sha or "", head_sha or "")})

    if not changed:
        raise GateError("no changed files detected; classification is required and fail-closed")

    matched_by_flow: dict[str, list[str]] = {}
    matched_files: set[str] = set()

    for flow in flows:
        flow_id = str(flow.get("flow_id", "")).strip()
        patterns = flow.get("source_paths", [])
        if not flow_id:
            raise GateError("flow missing flow_id")
        if not isinstance(patterns, list) or not patterns:
            raise GateError(f"{flow_id}: source_paths must be a non-empty list")
        matched = [path for path in changed if any(fnmatch.fnmatch(path, pat) for pat in patterns)]
        if matched:
            matched_by_flow[flow_id] = matched
            matched_files.update(matched)

    unmatched = [path for path in changed if path not in matched_files]

    waiver = _load_waiver(waiver_path)
    waiver_valid, waiver_type = _waiver_is_valid(waiver, release_date)

    errors: list[str] = []
    if unmatched and not waiver_valid:
        errors.append(
            "unclassified changed files require explicit non-expired waiver (type emergency or not-p1): "
            + ", ".join(unmatched)
        )

    if matched_by_flow:
        flow_index = {str(flow.get("flow_id")): flow for flow in flows}
        for flow_id in sorted(matched_by_flow):
            errors.extend(_required_metadata_errors(flow_index[flow_id], release_date))

    passed = not errors
    if errors and waiver_valid and waiver_type == "emergency":
        passed = True

    summary = {
        "passed": passed,
        "release_date": release_date.isoformat(),
        "inventory": str(inventory_path),
        "base_sha": base_sha,
        "head_sha": head_sha,
        "changed_files": changed,
        "matched_flows": matched_by_flow,
        "unclassified_files": unmatched,
        "waiver": waiver,
        "waiver_valid": waiver_valid,
        "waiver_type": waiver_type,
        "errors": errors,
    }
    return passed, summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Fail-closed P1 training release gate")
    parser.add_argument(
        "--inventory",
        type=Path,
        default=Path("docs/disaster-response-hub/p1-flow-inventory.yaml"),
    )
    parser.add_argument("--release-date", default=dt.date.today().isoformat())
    parser.add_argument("--base-sha")
    parser.add_argument("--head-sha", default="HEAD")
    parser.add_argument("--changed-file", action="append", dest="changed_files")
    parser.add_argument("--waiver-file", type=Path)
    parser.add_argument("--summary-out", type=Path)
    args = parser.parse_args(argv)

    try:
        release_date = _parse_date(args.release_date, "release_date")
        passed, summary = run_gate(
            inventory_path=args.inventory,
            release_date=release_date,
            changed_files=args.changed_files,
            base_sha=args.base_sha,
            head_sha=args.head_sha,
            waiver_path=args.waiver_file,
        )
    except GateError as exc:
        print(f"p1-release-gate: FAIL - {exc}")
        return 1

    if args.summary_out:
        args.summary_out.parent.mkdir(parents=True, exist_ok=True)
        args.summary_out.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")

    print(json.dumps(summary, indent=2, sort_keys=True))
    if passed:
        print("p1-release-gate: PASS")
        return 0
    print("p1-release-gate: FAIL")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
