#!/usr/bin/env python3
"""Fail-closed validator for spec-004 feature evidence scaffolds (SC-003..SC-006)."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import yaml

FEATURE_ROOT = Path("specs/004-actor-github-agents")
EVIDENCE_ROOT = FEATURE_ROOT / "evidence"
RETIRED_IDS = {
    "ambulance-paramedic",
    "commonwealth-government",
    "fire-services",
    "meteorology-bom",
    "police",
    "ses",
}
REQUIRED_OPERATIONAL_ROLES = {
    "incident-commander",
    "operations-officer",
    "planning-officer",
    "logistics-officer",
    "public-information-officer",
    "field-coordinator",
    "resilience-planner",
    "executive-leader",
    "observer-auditor",
    "risk-manager",
}
REQUIRED_SECTOR_FAMILIES = {
    "commonwealth-government",
    "state-government",
    "territory-government",
    "local-government",
    "fire-services",
    "police",
    "ambulance-paramedic",
    "ses",
    "meteorology",
    "health",
    "utility",
    "transport",
    "community",
    "volunteer",
}


def _line_for(text: str, needle: str, default: int = 1) -> int:
    idx = text.find(needle)
    if idx < 0:
        return default
    return text.count("\n", 0, idx) + 1


def _diag(path: Path, line: int, message: str) -> str:
    return f"{path.as_posix()}:{line}: {message}"


def _load_yaml(path: Path, violations: list[str]) -> dict:
    if not path.exists():
        violations.append(_diag(path, 1, "missing YAML evidence scaffold"))
        return {}
    text = path.read_text(encoding="utf-8")
    try:
        doc = yaml.safe_load(text) or {}
    except yaml.YAMLError as exc:
        violations.append(_diag(path, 1, f"invalid YAML: {exc}"))
        return {}
    if not isinstance(doc, dict):
        violations.append(_diag(path, 1, "YAML root must be an object"))
        return {}
    return doc


def _load_json(path: Path, violations: list[str]) -> dict:
    if not path.exists():
        violations.append(_diag(path, 1, "missing JSON evidence scaffold"))
        return {}
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        violations.append(_diag(path, 1, f"invalid JSON: {exc}"))
        return {}
    if not isinstance(doc, dict):
        violations.append(_diag(path, 1, "JSON root must be an object"))
        return {}
    return doc


def _check_yaml_json_sync(
    yaml_path: Path, yaml_doc: dict, json_path: Path, json_doc: dict, violations: list[str]
) -> None:
    y_status = str(yaml_doc.get("status", "")).strip()
    j_status = str(json_doc.get("status", "")).strip()
    if y_status != j_status:
        violations.append(_diag(json_path, 1, f"status mismatch with YAML ({y_status} != {j_status})"))

    y_version = yaml_doc.get("schemaVersion")
    j_version = json_doc.get("schemaVersion")
    if y_version != j_version:
        violations.append(_diag(json_path, 1, f"schemaVersion mismatch with YAML ({y_version} != {j_version})"))


def _check_sc003(doc: dict, path: Path, violations: list[str]) -> None:
    status = str(doc.get("status", "")).strip()
    threshold = int(doc.get("thresholdPercent", 0))
    denominator = int(doc.get("denominator", 0))
    if threshold < 80:
        violations.append(_diag(path, 1, "thresholdPercent must be >= 80"))
    if denominator <= 0:
        violations.append(_diag(path, 1, "denominator must be > 0"))

    roles = doc.get("roles")
    if not isinstance(roles, list):
        violations.append(_diag(path, 1, "roles must be a list"))
        roles = []

    seen = {str(item.get("roleId", "")).strip() for item in roles if isinstance(item, dict)}
    missing = sorted(REQUIRED_OPERATIONAL_ROLES - seen)
    for role in missing:
        violations.append(_diag(path, 1, f"missing required operational role in question pack: {role}"))

    for role in roles:
        if not isinstance(role, dict):
            violations.append(_diag(path, 1, "roles entries must be objects"))
            continue
        role_id = str(role.get("roleId", "")).strip()
        questions = role.get("questions")
        if not isinstance(questions, list) or not questions:
            violations.append(_diag(path, 1, f"role {role_id or '<unknown>'} must include at least one question"))
            continue
        for question in questions:
            if not isinstance(question, dict):
                violations.append(_diag(path, 1, f"role {role_id}: question must be an object"))
                continue
            if not str(question.get("expectedAnswer", "")).strip():
                violations.append(_diag(path, 1, f"role {role_id}: expectedAnswer is required"))
            if not str(question.get("citation", "")).strip():
                violations.append(_diag(path, 1, f"role {role_id}: citation is required"))

    protocol = doc.get("sameSessionRoleIsolation", {})
    sequence = protocol.get("sequence") if isinstance(protocol, dict) else None
    expected_sequence = ["incident-commander", "observer-auditor", "planning-officer"]
    if sequence != expected_sequence:
        violations.append(
            _diag(
                path,
                1,
                "sameSessionRoleIsolation.sequence must equal incident-commander -> observer-auditor -> planning-officer",  # noqa: E501
            )
        )

    responses = doc.get("responses")
    responses = responses if isinstance(responses, list) else []
    measured_correct = int(doc.get("measuredCorrect", 0))
    measured_percent = float(doc.get("measuredPercent", 0.0))
    expected_percent = round((measured_correct / denominator) * 100, 2) if denominator else 0.0
    if measured_percent != expected_percent:
        violations.append(
            _diag(path, 1, f"score mismatch: measuredPercent={measured_percent} expected={expected_percent}")
        )

    if status.lower() in {"measured", "validated"}:
        if len(responses) == 0:
            violations.append(_diag(path, 1, "status measured/validated requires non-empty responses"))
        run = doc.get("run", {}) if isinstance(doc.get("run"), dict) else {}
        reviewer = str(run.get("reviewer", "")).strip()
        run_id = str(run.get("runId", "")).strip()
        if not reviewer or not run_id:
            violations.append(_diag(path, 1, "status measured/validated requires run.reviewer and run.runId"))


def _check_sc004(doc: dict, path: Path, violations: list[str]) -> None:
    status = str(doc.get("status", "")).strip()
    threshold = int(doc.get("thresholdPercent", 0))
    denominator = int(doc.get("denominator", 0))
    if threshold < 80:
        violations.append(_diag(path, 1, "thresholdPercent must be >= 80"))
    if denominator <= 0:
        violations.append(_diag(path, 1, "denominator must be > 0"))

    families = doc.get("families")
    if not isinstance(families, list):
        violations.append(_diag(path, 1, "families must be a list"))
        families = []

    seen_families = {str(item.get("familyId", "")).strip() for item in families if isinstance(item, dict)}
    for family in sorted(REQUIRED_SECTOR_FAMILIES - seen_families):
        violations.append(_diag(path, 1, f"missing required sector family: {family}"))

    for family in families:
        if not isinstance(family, dict):
            violations.append(_diag(path, 1, "family entries must be objects"))
            continue
        family_id = str(family.get("familyId", "")).strip()
        questions = family.get("questions")
        if not isinstance(questions, list) or not questions:
            violations.append(_diag(path, 1, f"family {family_id or '<unknown>'} must include at least one question"))
            continue
        for question in questions:
            if not isinstance(question, dict):
                violations.append(_diag(path, 1, f"family {family_id}: question must be an object"))
                continue
            target = str(question.get("targetAgentId", "")).strip()
            if target in RETIRED_IDS:
                violations.append(
                    _diag(path, 1, f"family {family_id}: archived targetAgentId is not allowed: {target}")
                )
            if not str(question.get("primarySourceCitation", "")).strip():
                violations.append(_diag(path, 1, f"family {family_id}: primarySourceCitation is required"))
            if not str(question.get("ownerRole", "")).strip():
                violations.append(_diag(path, 1, f"family {family_id}: ownerRole is required"))

    responses = doc.get("responses")
    responses = responses if isinstance(responses, list) else []
    measured_correct = int(doc.get("measuredCorrect", 0))
    measured_percent = float(doc.get("measuredPercent", 0.0))
    expected_percent = round((measured_correct / denominator) * 100, 2) if denominator else 0.0
    if measured_percent != expected_percent:
        violations.append(
            _diag(path, 1, f"score mismatch: measuredPercent={measured_percent} expected={expected_percent}")
        )

    if status.lower() in {"measured", "validated"}:
        if len(responses) == 0:
            violations.append(_diag(path, 1, "status measured/validated requires non-empty responses"))
        run = doc.get("run", {}) if isinstance(doc.get("run"), dict) else {}
        reviewer = str(run.get("reviewer", "")).strip()
        run_id = str(run.get("runId", "")).strip()
        if not reviewer or not run_id:
            violations.append(_diag(path, 1, "status measured/validated requires run.reviewer and run.runId"))


def _check_sc005(doc: dict, path: Path, violations: list[str]) -> None:
    status = str(doc.get("status", "")).strip()
    threshold = int(doc.get("thresholdPercent", 0))
    if threshold < 85:
        violations.append(_diag(path, 1, "thresholdPercent must be >= 85"))

    instrument = doc.get("instrument") if isinstance(doc.get("instrument"), dict) else {}
    required_fields = [
        "instrumentVersion",
        "frozenDate",
        "primaryBenefitQuestion",
        "scale",
        "favourableDefinition",
        "eligibilityRule",
        "denominatorRule",
        "nonResponseRule",
        "duplicateRule",
        "privacyRule",
    ]
    for field in required_fields:
        if not str(instrument.get(field, "")).strip():
            violations.append(_diag(path, 1, f"instrument.{field} is required"))

    responses = doc.get("responses") if isinstance(doc.get("responses"), list) else []
    aggregate = doc.get("aggregate") if isinstance(doc.get("aggregate"), dict) else {}
    eligible = int(aggregate.get("eligible", 0))
    favourable = int(aggregate.get("favourable", 0))
    measured_percent = float(aggregate.get("measuredPercent", 0.0))
    expected_percent = round((favourable / eligible) * 100, 2) if eligible else 0.0
    if measured_percent != expected_percent:
        violations.append(
            _diag(path, 1, f"aggregate score mismatch: measuredPercent={measured_percent} expected={expected_percent}")
        )

    seen_ids: set[str] = set()
    for response in responses:
        if not isinstance(response, dict):
            violations.append(_diag(path, 1, "responses entries must be objects"))
            continue
        rid = str(response.get("respondentId", "")).strip()
        if not rid:
            violations.append(_diag(path, 1, "responses.respondentId is required"))
            continue
        if "@" in rid:
            violations.append(_diag(path, 1, "responses.respondentId must be anonymized (no PII markers like email)"))
        if rid in seen_ids:
            violations.append(_diag(path, 1, f"duplicate anonymized respondentId: {rid}"))
        seen_ids.add(rid)

    first_response_at = str(doc.get("firstResponseAt", "")).strip()
    instrument_last_modified_at = str(doc.get("instrumentLastModifiedAt", "")).strip()
    if first_response_at and instrument_last_modified_at and instrument_last_modified_at > first_response_at:
        violations.append(
            _diag(
                path,
                1,
                "instrumentLastModifiedAt cannot be after firstResponseAt (post-response instrument edit detected)",
            )
        )

    if status.lower() in {"measured", "validated"}:
        if len(responses) == 0:
            violations.append(_diag(path, 1, "status measured/validated requires non-empty responses"))
        if eligible == 0:
            violations.append(_diag(path, 1, "status measured/validated requires eligible > 0"))
        run = doc.get("run", {}) if isinstance(doc.get("run"), dict) else {}
        reviewer = str(run.get("reviewer", "")).strip()
        run_id = str(run.get("runId", "")).strip()
        if not reviewer or not run_id:
            violations.append(_diag(path, 1, "status measured/validated requires run.reviewer and run.runId"))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def _check_sc006(doc: dict, path: Path, root: Path, violations: list[str]) -> None:
    status = str(doc.get("status", "")).strip()
    timing = doc.get("timingDefinition") if isinstance(doc.get("timingDefinition"), dict) else {}
    expected_values = {
        "startEvent": "catalogue review started",
        "stopEvent": "new actor file + registry + handoffs + references pass validator",
        "passBoundarySeconds": 1799,
        "failBoundarySeconds": 1800,
    }
    for key, value in expected_values.items():
        if timing.get(key) != value:
            violations.append(_diag(path, 1, f"timingDefinition.{key} must equal {value!r}"))

    execution = doc.get("executionPolicy") if isinstance(doc.get("executionPolicy"), dict) else {}
    expected_flags = {
        "independentContributor": True,
        "unfamiliarContributor": True,
        "facilitatorAuthored": False,
        "disposableWorkspace": True,
        "commitCreated": False,
    }
    for key, expected in expected_flags.items():
        if execution.get(key) is not expected:
            violations.append(_diag(path, 1, f"executionPolicy.{key} must be {expected}"))

    run_data = doc.get("run") if isinstance(doc.get("run"), dict) else {}
    elapsed = run_data.get("elapsedSeconds")
    outcome = str(run_data.get("outcome", "")).strip().lower()

    if status.lower() in {"measured", "validated"}:
        reviewer = str(run_data.get("reviewer", "")).strip()
        run_id = str(run_data.get("runId", "")).strip()
        validator_output = str(run_data.get("validatorOutput", "")).strip()
        artifacts = run_data.get("artifacts") if isinstance(run_data.get("artifacts"), list) else []
        if not reviewer or not run_id:
            violations.append(_diag(path, 1, "status measured/validated requires run.reviewer and run.runId"))
        if not validator_output:
            violations.append(_diag(path, 1, "status measured/validated requires run.validatorOutput"))
        if not isinstance(elapsed, int):
            violations.append(_diag(path, 1, "status measured/validated requires integer run.elapsedSeconds"))
        if not artifacts:
            violations.append(_diag(path, 1, "status measured/validated requires non-empty run.artifacts"))

        for artifact in artifacts:
            if not isinstance(artifact, dict):
                violations.append(_diag(path, 1, "run.artifacts entries must be objects"))
                continue
            artifact_path = str(artifact.get("path", "")).strip()
            artifact_hash = str(artifact.get("sha256", "")).strip()
            if not artifact_path or not artifact_hash:
                violations.append(_diag(path, 1, "run.artifacts entries require path and sha256"))
                continue
            resolved = (root / artifact_path).resolve()
            if not resolved.exists():
                violations.append(_diag(path, 1, f"artifact path does not exist: {artifact_path}"))
                continue
            if _sha256(resolved) != artifact_hash:
                violations.append(_diag(path, 1, f"artifact hash mismatch: {artifact_path}"))

        if isinstance(elapsed, int):
            if elapsed == 1800 and outcome == "pass":
                violations.append(_diag(path, 1, "elapsedSeconds 1800 must fail (under-30-minute boundary)"))
            if elapsed <= 1799 and outcome == "fail":
                violations.append(_diag(path, 1, "elapsedSeconds <= 1799 cannot be marked fail"))
    else:
        if elapsed is not None or run_data.get("artifacts"):
            violations.append(_diag(path, 1, "status Not measured must not include run timing/artifact claims"))


def run(root: Path) -> list[str]:
    violations: list[str] = []

    checks = [
        ("sc-003-operational", _check_sc003),
        ("sc-004-sectors", _check_sc004),
        ("sc-005-onboarding", _check_sc005),
        ("sc-006-timing", lambda doc, p, v: _check_sc006(doc, p, root, v)),
    ]

    for stem, checker in checks:
        yaml_path = root / EVIDENCE_ROOT / f"{stem}.yaml"
        json_path = root / EVIDENCE_ROOT / f"{stem}.json"
        md_path = root / EVIDENCE_ROOT / f"{stem}.md"

        yaml_doc = _load_yaml(yaml_path, violations)
        json_doc = _load_json(json_path, violations)
        if not md_path.exists():
            violations.append(_diag(md_path, 1, "missing Markdown evidence scaffold"))

        if yaml_doc and json_doc:
            _check_yaml_json_sync(yaml_path, yaml_doc, json_path, json_doc, violations)
            checker(yaml_doc, yaml_path, violations)

    return sorted(set(violations))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate spec-004 evidence scaffolds for SC-003..SC-006")
    parser.add_argument("--root", type=Path, default=Path("."), help="Repository root")
    args = parser.parse_args(argv)

    violations = run(args.root.resolve())
    if violations:
        print("actor-feature-evidence: FAIL")
        for violation in violations:
            print(f" - {violation}")
        return 1

    print("actor-feature-evidence: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
