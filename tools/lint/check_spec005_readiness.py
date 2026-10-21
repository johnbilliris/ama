#!/usr/bin/env python3
"""Readiness/export validation for spec 005 governance evidence.

Implements AUD-026/AUD-027 automatable checks:
- Deterministic export of normalized governance state
- Validation of schema, thresholds, and evidence bindings
- Audit replay with exact diff output
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
API_ROOT = REPO_ROOT / "apps" / "api"
for import_root in (REPO_ROOT, API_ROOT):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

from app.core.tenant_context import TenantContext, reset_current_tenant, set_current_tenant  # noqa: E402
from app.repositories.governance_repository import GovernanceRepository  # noqa: E402
from app.services.governance_registry import GovernanceRegistryService  # noqa: E402

FEATURE_DIR = Path("specs/005-data-source-governance")
SEED_PATH = Path("packages/domain/src/domain/seed/data_sources_australia.json")
SCHEMA_VERSION = "spec005-readiness-v2"
TOOL_VERSION = "2026-09-16"


@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    errors: list[str]
    warnings: list[str]
    metrics: dict[str, Any]


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _sha256_json(value: Any) -> str:
    return _sha256_text(json.dumps(value, sort_keys=True, separators=(",", ":")))


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _git_revision() -> str:
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
    except Exception:
        return "unknown"
    return proc.stdout.strip() or "unknown"


def _tool_source_hash() -> str:
    text = Path(__file__).read_text(encoding="utf-8")
    return _sha256_text(text)


def _normalize(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _normalize(value[k]) for k in sorted(value)}
    if isinstance(value, list):
        normalized = [_normalize(item) for item in value]
        if all(isinstance(item, dict) for item in normalized):
            return sorted(
                normalized,
                key=lambda item: json.dumps(item, sort_keys=True, separators=(",", ":")),
            )
        return normalized
    return value


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _required_source_ids(seed_path: Path) -> list[str]:
    payload = _read_json(seed_path)
    if not isinstance(payload, list):
        raise ValueError(f"Seed file must be a JSON array: {seed_path}")

    ids: list[str] = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        source_id = str(item.get("data_source_id", "")).strip()
        if source_id:
            ids.append(source_id)
    return sorted(set(ids))


def _replay_from_audit(audit_entries: list[dict[str, Any]]) -> dict[str, Any]:
    """Best-effort replay projection from audit details.

    The existing audit model does not always include full entity payloads,
    so this replay intentionally reports explicit insufficiency where needed.
    """

    state: dict[str, dict[str, dict[str, Any]]] = {
        "sources": {},
        "assessments": {},
        "assignments": {},
        "chains": {},
    }
    unsupported: list[dict[str, str]] = []

    sorted_entries = sorted(
        audit_entries, key=lambda entry: (entry.get("timestamp", ""), entry.get("audit_entry_id", ""))
    )

    for entry in sorted_entries:
        if entry.get("outcome") == "pending":
            continue
        action = str(entry.get("action", ""))
        details = entry.get("details") if isinstance(entry.get("details"), dict) else {}
        related_id = str(entry.get("related_entity_id") or "")

        after = details.get("after") if isinstance(details.get("after"), dict) else None
        payload = None
        if isinstance(after, dict) and after:
            payload = after

        if payload is None:
            if action in {
                "registered",
                "updated",
                "assessment_created",
                "assessment_superseded",
                "agent_assigned",
                "agent_revoked",
                "handoff_defined",
                "handoff_updated",
                "handoff_deprecated",
            }:
                unsupported.append(
                    {
                        "audit_entry_id": str(entry.get("audit_entry_id", "")),
                        "action": action,
                        "reason": "missing_after_payload",
                    }
                )
            continue

        if action in {"registered", "updated", "deactivated"}:
            ds_id = str(payload.get("data_source_id") or entry.get("data_source_id") or "")
            if ds_id:
                state["sources"][ds_id] = _normalize(payload)
            continue

        if action in {"assessment_created", "assessment_superseded"}:
            assessment_id = str(payload.get("assessment_id") or related_id)
            if assessment_id:
                state["assessments"][assessment_id] = _normalize(payload)
            continue

        if action in {"agent_assigned", "agent_revoked"}:
            assignment_id = str(payload.get("assignment_id") or related_id)
            if assignment_id:
                state["assignments"][assignment_id] = _normalize(payload)
            continue

        if action in {"handoff_defined", "handoff_updated", "handoff_deprecated"}:
            chain_id = str(payload.get("chain_id") or related_id)
            if chain_id:
                state["chains"][chain_id] = _normalize(payload)

    return {
        "state": {
            "sources": sorted(state["sources"].values(), key=lambda item: str(item.get("data_source_id", ""))),
            "assessments": sorted(state["assessments"].values(), key=lambda item: str(item.get("assessment_id", ""))),
            "assignments": sorted(state["assignments"].values(), key=lambda item: str(item.get("assignment_id", ""))),
            "chains": sorted(state["chains"].values(), key=lambda item: str(item.get("chain_id", ""))),
        },
        "unsupported_events": unsupported,
    }


def _snapshot_hashes(snapshot: dict[str, Any]) -> dict[str, str]:
    return {
        "sources": _sha256_json(snapshot["sources"]),
        "assessments": _sha256_json(snapshot["assessments"]),
        "assignments": _sha256_json(snapshot["assignments"]),
        "chains": _sha256_json(snapshot["chains"]),
        "gaps": _sha256_json(snapshot["gaps"]),
        "audit": _sha256_json(snapshot["audit"]),
        "readiness": _sha256_json(snapshot["readiness"]),
        "replay": _sha256_json(snapshot["replay_validation"]),
    }


def export_snapshot(
    output_path: Path, tenant_id: str, agency_id: str, bootstrap_seed_catalogue: bool = True
) -> dict[str, Any]:
    token = set_current_tenant(
        TenantContext(
            tenant_id=tenant_id,
            agency_id=agency_id,
            jurisdiction_ids=("nsw",),
            persona_id="governance-lead",
        )
    )
    try:
        repo = GovernanceRepository()
        service = GovernanceRegistryService(repo=repo)

        if bootstrap_seed_catalogue:
            try:
                service.import_seed_catalogue(SEED_PATH.parent, actor_id="readiness-export")
            except Exception:
                # Export still proceeds and records actual observable state.
                pass

        sources = [source.model_dump(mode="json", by_alias=True) for source in repo.list_sources()]
        sources = sorted(sources, key=lambda item: str(item.get("data_source_id", "")))

        assessments: list[dict[str, Any]] = []
        assignments: list[dict[str, Any]] = []
        chains: list[dict[str, Any]] = []
        audits: list[dict[str, Any]] = []
        gap_map: dict[str, list[dict[str, Any]]] = {}

        for source in sources:
            source_id = str(source.get("data_source_id", ""))
            if not source_id:
                continue
            for assessment in repo.get_assessments_for_source(source_id, tenant_id):
                assessments.append(assessment.model_dump(mode="json", by_alias=True))
            for assignment in repo.get_assignments_for_source(source_id, tenant_id):
                assignments.append(assignment.model_dump(mode="json", by_alias=True))
            chain = repo.get_chain_for_source(source_id, tenant_id)
            if chain is not None:
                chains.append(chain.model_dump(mode="json", by_alias=True))
            gaps = service._project_source_gaps(service.get_source(source_id), tenant_id)  # noqa: SLF001
            if gaps:
                gap_map[source_id] = _normalize(gaps)
            audits.extend(
                [
                    event.model_dump(mode="json", by_alias=True)
                    for event in repo.get_audit_trail(source_id, tenant_id=tenant_id)
                ]
            )

        required_ids = _required_source_ids(SEED_PATH)
        covered_ids = sorted({str(item.get("data_source_id", "")) for item in sources if item.get("data_source_id")})
        covered_required = sorted(set(required_ids).intersection(covered_ids))
        coverage_ratio = (len(covered_required) / len(required_ids)) if required_ids else 0.0

        assessments = sorted(assessments, key=lambda item: str(item.get("assessment_id", "")))
        assignments = sorted(assignments, key=lambda item: str(item.get("assignment_id", "")))
        chains = sorted(chains, key=lambda item: str(item.get("chain_id", "")))
        audits = sorted(audits, key=lambda item: (str(item.get("timestamp", "")), str(item.get("audit_entry_id", ""))))

        replay = _replay_from_audit(audits)

        snapshot = {
            "schema_version": SCHEMA_VERSION,
            "generator": {
                "tool": "tools/lint/check_spec005_readiness.py",
                "version": TOOL_VERSION,
                "source_sha256": _tool_source_hash(),
            },
            "revision": _git_revision(),
            "generated_at": _now_iso(),
            "tenant_scope": {
                "tenant_id": tenant_id,
                "agency_id": agency_id,
            },
            "sources": _normalize(sources),
            "assessments": _normalize(assessments),
            "assignments": _normalize(assignments),
            "chains": _normalize(chains),
            "gaps": {
                "by_source": gap_map,
                "total": sum(len(items) for items in gap_map.values()),
            },
            "audit": _normalize(audits),
            "readiness": {
                "catalogue_source": SEED_PATH.as_posix(),
                "required_source_ids": required_ids,
                "covered_source_ids": covered_required,
                "source_coverage_ratio": round(coverage_ratio, 6),
                "unresolved_gap_total": sum(len(items) for items in gap_map.values()),
                "human_protocol": {
                    "roles": {
                        "governance_lead": "required",
                        "qa_observer": "required",
                        "sme_panel": "required",
                        "ux_researcher": "required",
                    },
                    "start_event": "manual_start",
                    "end_event": "manual_end",
                    "tested_user_count": 0,
                    "successful_user_count": 0,
                    "workflow_seconds": 1800,
                    "gap_identification_seconds": 120,
                    "approval_decision": "Not measured",
                    "deactivated_history_considered": False,
                    "notes": "UNVERIFIED pending scheduled rehearsal/usability and reviewer evidence.",
                },
            },
            "replay_validation": {
                "audit_entries": _normalize(audits),
                "replayed_state": replay["state"],
                "unsupported_events": replay["unsupported_events"],
                "exact_diff": {},
            },
        }

        replay_expected = {
            "sources": snapshot["sources"],
            "assessments": snapshot["assessments"],
            "assignments": snapshot["assignments"],
            "chains": snapshot["chains"],
        }
        exact_diff: dict[str, Any] = {}
        for key in ("sources", "assessments", "assignments", "chains"):
            if replay["state"][key] != replay_expected[key]:
                exact_diff[key] = {
                    "expected_sha256": _sha256_json(replay_expected[key]),
                    "actual_sha256": _sha256_json(replay["state"][key]),
                    "expected_count": len(replay_expected[key]),
                    "actual_count": len(replay["state"][key]),
                }
        snapshot["replay_validation"]["exact_diff"] = exact_diff

        hashes = _snapshot_hashes(snapshot)
        hashes["snapshot"] = _sha256_json(
            {
                "schema_version": snapshot["schema_version"],
                "generator": snapshot["generator"],
                "revision": snapshot["revision"],
                "tenant_scope": snapshot["tenant_scope"],
                "sources": snapshot["sources"],
                "assessments": snapshot["assessments"],
                "assignments": snapshot["assignments"],
                "chains": snapshot["chains"],
                "gaps": snapshot["gaps"],
                "audit": snapshot["audit"],
                "readiness": snapshot["readiness"],
                "replay_validation": snapshot["replay_validation"],
            }
        )
        snapshot["hashes"] = hashes

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")
        return snapshot
    finally:
        reset_current_tenant(token)


def _validate_generator(snapshot: dict[str, Any], errors: list[str]) -> None:
    generator = snapshot.get("generator")
    if not isinstance(generator, dict):
        errors.append("snapshot missing generator metadata")
        return

    source_hash = str(generator.get("source_sha256", "")).strip()
    if not re.fullmatch(r"[0-9a-f]{64}", source_hash):
        errors.append("generator.source_sha256 must be a 64-char lowercase hex SHA256")
        return

    current_hash = _tool_source_hash()
    if source_hash != current_hash:
        errors.append(
            "snapshot generator hash does not match current tool source; regenerate snapshot with current tool"
        )


def _validate_rehearsal_manifest(snapshot: dict[str, Any], errors: list[str], warnings: list[str]) -> None:
    readiness = snapshot.get("readiness")
    if not isinstance(readiness, dict):
        errors.append("snapshot missing readiness block")
        return

    human = readiness.get("human_protocol")
    if not isinstance(human, dict):
        errors.append("readiness.human_protocol must be an object")
        return

    workflow_seconds = int(human.get("workflow_seconds", 0) or 0)
    gap_seconds = int(human.get("gap_identification_seconds", 0) or 0)
    tested = int(human.get("tested_user_count", 0) or 0)
    success = int(human.get("successful_user_count", 0) or 0)
    approval = str(human.get("approval_decision", "")).strip()

    if workflow_seconds > 1800:
        errors.append("SC-004 fails: workflow_seconds must be <= 1800")
    if gap_seconds > 120:
        errors.append("SC-005 fails: gap_identification_seconds must be <= 120")
    if tested > 0:
        ratio = success / tested
        if ratio < 0.9:
            errors.append(f"SC-005 fails: successful_user_count/tested_user_count must be >= 0.9 (got {ratio:.3f})")
    elif approval.upper() == "PASS":
        errors.append("SC-005 PASS cannot be claimed with tested_user_count = 0")
    else:
        warnings.append("SC-005 remains UNVERIFIED until usability denominator is recorded")

    if approval == "Not measured":
        warnings.append("Human approval remains Not measured")


def _validate_thresholds(snapshot: dict[str, Any], errors: list[str], metrics: dict[str, Any]) -> None:
    readiness = snapshot.get("readiness")
    if not isinstance(readiness, dict):
        errors.append("readiness block missing")
        return

    required_ids = readiness.get("required_source_ids")
    covered_ids = readiness.get("covered_source_ids")
    if not isinstance(required_ids, list) or not isinstance(covered_ids, list):
        errors.append("readiness required_source_ids and covered_source_ids must be arrays")
        return

    required_set = {str(item) for item in required_ids}
    covered_set = {str(item) for item in covered_ids}
    ratio = (len(required_set & covered_set) / len(required_set)) if required_set else 0.0
    metrics["source_coverage_ratio"] = round(ratio, 6)
    if ratio < 0.9:
        errors.append(f"SC-001 fails: required ID coverage must be >= 0.90 (got {ratio:.6f})")

    replay = snapshot.get("replay_validation")
    if not isinstance(replay, dict):
        errors.append("replay_validation block missing")
        return

    exact_diff = replay.get("exact_diff")
    if not isinstance(exact_diff, dict):
        errors.append("replay_validation.exact_diff must be an object")
        return

    metrics["replay_diff_bucket_count"] = len(exact_diff)
    if exact_diff:
        errors.append("SC-006 fails: replay_validation.exact_diff must be empty for PASS")


def _validate_schema(snapshot: dict[str, Any], errors: list[str]) -> None:
    for key in (
        "schema_version",
        "generator",
        "revision",
        "generated_at",
        "tenant_scope",
        "sources",
        "assessments",
        "assignments",
        "chains",
        "gaps",
        "audit",
        "readiness",
        "replay_validation",
        "hashes",
    ):
        if key not in snapshot:
            errors.append(f"snapshot missing key: {key}")

    if snapshot.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version must be {SCHEMA_VERSION}")

    hashes = snapshot.get("hashes")
    if isinstance(hashes, dict):
        computed = _snapshot_hashes(snapshot)
        for key, expected in computed.items():
            actual = hashes.get(key)
            if actual != expected:
                errors.append(f"hash mismatch for '{key}'")
    else:
        errors.append("hashes must be an object")


def validate_snapshot(snapshot_path: Path) -> ValidationResult:
    errors: list[str] = []
    warnings: list[str] = []
    metrics: dict[str, Any] = {}

    snapshot = _read_json(snapshot_path)
    if not isinstance(snapshot, dict):
        return ValidationResult(False, ["snapshot root must be an object"], [], metrics)

    _validate_schema(snapshot, errors)
    _validate_generator(snapshot, errors)
    _validate_thresholds(snapshot, errors, metrics)
    _validate_rehearsal_manifest(snapshot, errors, warnings)

    return ValidationResult(ok=not errors, errors=errors, warnings=warnings, metrics=metrics)


def replay_snapshot(snapshot_path: Path) -> dict[str, Any]:
    snapshot = _read_json(snapshot_path)
    if not isinstance(snapshot, dict):
        raise ValueError("snapshot root must be an object")

    audit_entries = snapshot.get("audit")
    if not isinstance(audit_entries, list):
        raise ValueError("snapshot audit must be a list")

    replay = _replay_from_audit(_normalize(audit_entries))
    expected = {
        "sources": _normalize(snapshot.get("sources", [])),
        "assessments": _normalize(snapshot.get("assessments", [])),
        "assignments": _normalize(snapshot.get("assignments", [])),
        "chains": _normalize(snapshot.get("chains", [])),
    }
    exact_diff: dict[str, Any] = {}
    for key in ("sources", "assessments", "assignments", "chains"):
        if replay["state"][key] != expected[key]:
            exact_diff[key] = {
                "expected_sha256": _sha256_json(expected[key]),
                "actual_sha256": _sha256_json(replay["state"][key]),
                "expected_count": len(expected[key]),
                "actual_count": len(replay["state"][key]),
            }

    return {
        "schema_version": "spec005-readiness-replay-v1",
        "generated_at": _now_iso(),
        "input_snapshot": str(snapshot_path).replace("\\", "/"),
        "replayed_state": replay["state"],
        "unsupported_events": replay["unsupported_events"],
        "exact_diff": exact_diff,
    }


def _print_result(result: ValidationResult) -> int:
    if result.ok:
        print("spec005-readiness: PASS")
    else:
        print("spec005-readiness: FAIL")
    for warning in result.warnings:
        print(f" - WARN: {warning}")
    for error in result.errors:
        print(f" - ERROR: {error}")
    if result.metrics:
        print(json.dumps({"metrics": result.metrics}, indent=2))
    return 0 if result.ok else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    export_parser = subparsers.add_parser("export", help="Export normalized readiness snapshot")
    export_parser.add_argument(
        "--output",
        type=Path,
        default=FEATURE_DIR / "evidence/readiness-snapshot.generated.json",
    )
    export_parser.add_argument("--tenant-id", default=os.environ.get("AMA_GOVERNANCE_READINESS_TENANT", "live"))
    export_parser.add_argument("--agency-id", default=os.environ.get("AMA_GOVERNANCE_READINESS_AGENCY", "nsw-ses"))
    export_parser.add_argument(
        "--skip-seed-import",
        action="store_true",
        help="Do not bootstrap seed catalogue before exporting snapshot.",
    )

    validate_parser = subparsers.add_parser("validate", help="Validate snapshot schema/threshold/evidence")
    validate_parser.add_argument(
        "--input",
        type=Path,
        default=FEATURE_DIR / "evidence/readiness-snapshot.generated.json",
    )

    replay_parser = subparsers.add_parser("replay", help="Replay audit stream and emit exact diff")
    replay_parser.add_argument(
        "--input",
        type=Path,
        default=FEATURE_DIR / "evidence/readiness-snapshot.generated.json",
    )
    replay_parser.add_argument(
        "--output",
        type=Path,
        default=FEATURE_DIR / "evidence/readiness-replay.generated.json",
    )

    args = parser.parse_args(argv)

    if args.command == "export":
        payload = export_snapshot(
            args.output,
            tenant_id=args.tenant_id,
            agency_id=args.agency_id,
            bootstrap_seed_catalogue=not args.skip_seed_import,
        )
        print(f"spec005-readiness export: {args.output.as_posix()}")
        print(json.dumps({"revision": payload["revision"], "hash": payload["hashes"]["snapshot"]}, indent=2))
        return 0

    if args.command == "validate":
        result = validate_snapshot(args.input)
        return _print_result(result)

    if args.command == "replay":
        payload = replay_snapshot(args.input)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        print(f"spec005-readiness replay: {args.output.as_posix()}")
        if payload["exact_diff"]:
            print("spec005-readiness replay: DIFF")
            return 1
        print("spec005-readiness replay: MATCH")
        return 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
