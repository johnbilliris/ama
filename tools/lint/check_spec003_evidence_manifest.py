#!/usr/bin/env python3
"""Fail-closed validator for specs/003-rubric-gap-closure/evidence-manifest.json."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

EXPECTED_SC_IDS = {f"SC-{index:03d}" for index in range(1, 14)}
ALLOWED_OUTCOMES = {"PASS", "FAIL", "UNVERIFIED", "SKIP"}
HEX_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
HEX_REVISION_RE = re.compile(r"^[0-9a-f]{7,40}$")


def _read_manifest(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def _validate_entry(entry: dict[str, object], root: Path, violations: list[str]) -> None:
    sc_id = str(entry.get("scId", "")).strip()
    outcome = str(entry.get("outcome", "")).strip()
    revision = str(entry.get("revisionSha", "")).strip()
    command = str(entry.get("command", "")).strip()
    environment = str(entry.get("environment", "")).strip()
    fixture = str(entry.get("fixtureCohort", "")).strip()
    denominator = str(entry.get("denominator", "")).strip()
    artifact_path = str(entry.get("artifactPath", "")).strip()
    artifact_hash = str(entry.get("artifactSha256", "")).strip()
    reason = str(entry.get("reason", "")).strip()

    if not sc_id:
        violations.append("Entry missing scId")
    if outcome not in ALLOWED_OUTCOMES:
        violations.append(f"{sc_id or '<unknown>'}: unsupported outcome '{outcome}'")
    if not HEX_REVISION_RE.match(revision):
        violations.append(f"{sc_id}: revisionSha must be 7-40 lowercase hex chars")
    if not command:
        violations.append(f"{sc_id}: command is required")
    if not environment:
        violations.append(f"{sc_id}: environment is required")
    if not fixture:
        violations.append(f"{sc_id}: fixtureCohort is required")
    if not denominator:
        violations.append(f"{sc_id}: denominator is required")

    if outcome == "PASS":
        if command.lower() == "n/a":
            violations.append(f"{sc_id}: PASS rows cannot use command 'n/a'")
        if denominator.lower().startswith("0/"):
            violations.append(f"{sc_id}: PASS rows must include a non-zero denominator")

    must_have_reason = outcome in {"UNVERIFIED", "SKIP"}
    if must_have_reason and not reason:
        violations.append(f"{sc_id}: {outcome} rows require a reason")

    if artifact_path:
        resolved = (root / artifact_path).resolve()
        if not resolved.exists():
            violations.append(f"{sc_id}: artifactPath does not exist: {artifact_path}")
        if not HEX_SHA256_RE.match(artifact_hash):
            violations.append(f"{sc_id}: artifactSha256 must be a 64-char lowercase hex hash when artifactPath is set")
        elif resolved.exists():
            actual_hash = _sha256(resolved)
            if actual_hash != artifact_hash:
                violations.append(
                    f"{sc_id}: artifact hash mismatch for {artifact_path} (expected {artifact_hash}, got {actual_hash})"
                )
    elif outcome == "PASS":
        violations.append(f"{sc_id}: PASS rows require artifactPath and artifactSha256")


def run(manifest_path: Path, root: Path) -> list[str]:
    violations: list[str] = []
    if not manifest_path.exists():
        return [f"Missing manifest: {manifest_path}"]

    doc = _read_manifest(manifest_path)
    entries = doc.get("entries")
    if not isinstance(entries, list):
        return ["Manifest must include an entries array"]

    seen: list[str] = []
    for raw_entry in entries:
        if not isinstance(raw_entry, dict):
            violations.append("Every entries item must be an object")
            continue
        _validate_entry(raw_entry, root, violations)
        seen.append(str(raw_entry.get("scId", "")).strip())

    expected_count = len(EXPECTED_SC_IDS)
    if len(entries) != expected_count:
        violations.append(f"Manifest must contain exactly {expected_count} entries, found {len(entries)}")

    seen_set = {item for item in seen if item}
    if seen_set != EXPECTED_SC_IDS:
        missing = sorted(EXPECTED_SC_IDS - seen_set)
        extras = sorted(seen_set - EXPECTED_SC_IDS)
        if missing:
            violations.append("Missing SC entries: " + ", ".join(missing))
        if extras:
            violations.append("Unexpected SC entries: " + ", ".join(extras))

    duplicates = sorted({sc for sc in seen if sc and seen.count(sc) > 1})
    if duplicates:
        violations.append("Duplicate SC entries: " + ", ".join(duplicates))

    return violations


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("specs/003-rubric-gap-closure/evidence-manifest.json"),
        help="Path to evidence-manifest.json",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path("."),
        help="Repository root for artifact path resolution",
    )
    args = parser.parse_args(argv)

    violations = run(args.manifest.resolve(), args.root.resolve())
    if violations:
        print("spec003-evidence-manifest: FAIL")
        for violation in violations:
            print(f" - {violation}")
        return 1

    print("spec003-evidence-manifest: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
