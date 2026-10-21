from __future__ import annotations

import json
from pathlib import Path

import yaml

from tools.lint.check_actor_feature_evidence import run


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _write_yaml_json(root: Path, stem: str, data: dict) -> None:
    evidence = root / "specs/004-actor-github-agents/evidence"
    _write(evidence / f"{stem}.yaml", yaml.safe_dump(data, sort_keys=False))
    _write(evidence / f"{stem}.json", json.dumps(data, indent=2) + "\n")
    _write(evidence / f"{stem}.md", f"# {stem}\n\nStatus: {data['status']}\n")


def _valid_docs() -> dict[str, dict]:
    sc003 = {
        "schemaVersion": 1,
        "status": "Not measured",
        "thresholdPercent": 80,
        "denominator": 10,
        "measuredCorrect": 0,
        "measuredPercent": 0.0,
        "roles": [
            {"roleId": role, "questions": [{"question": "q", "expectedAnswer": "a", "citation": "spec.md#L1"}]}
            for role in [
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
            ]
        ],
        "sameSessionRoleIsolation": {
            "sequence": ["incident-commander", "observer-auditor", "planning-officer"],
        },
        "run": {"runId": "", "reviewer": ""},
        "responses": [],
    }

    families = [
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
    ]
    sc004 = {
        "schemaVersion": 1,
        "status": "Not measured",
        "thresholdPercent": 80,
        "denominator": 14,
        "measuredCorrect": 0,
        "measuredPercent": 0.0,
        "families": [
            {
                "familyId": family,
                "questions": [
                    {
                        "question": "q",
                        "targetAgentId": "incident-commander",
                        "ownerRole": "sector-reviewer",
                        "primarySourceCitation": "source",
                    }
                ],
            }
            for family in families
        ],
        "run": {"runId": "", "reviewer": ""},
        "responses": [],
    }

    sc005 = {
        "schemaVersion": 1,
        "status": "Not measured",
        "thresholdPercent": 85,
        "instrument": {
            "instrumentVersion": "v1",
            "frozenDate": "2026-09-15",
            "primaryBenefitQuestion": "Did the agent improve onboarding?",
            "scale": "1-5",
            "favourableDefinition": ">=4",
            "eligibilityRule": "first-time contributors",
            "denominatorRule": "eligible responders",
            "nonResponseRule": "exclude non-responders from denominator",
            "duplicateRule": "dedupe by anonymized respondentId",
            "privacyRule": "no PII",
        },
        "firstResponseAt": "",
        "instrumentLastModifiedAt": "2026-09-15",
        "aggregate": {"eligible": 0, "favourable": 0, "measuredPercent": 0.0},
        "run": {"runId": "", "reviewer": ""},
        "responses": [],
    }

    sc006 = {
        "schemaVersion": 1,
        "status": "Not measured",
        "timingDefinition": {
            "startEvent": "catalogue review started",
            "stopEvent": "new actor file + registry + handoffs + references pass validator",
            "passBoundarySeconds": 1799,
            "failBoundarySeconds": 1800,
        },
        "executionPolicy": {
            "independentContributor": True,
            "unfamiliarContributor": True,
            "facilitatorAuthored": False,
            "disposableWorkspace": True,
            "commitCreated": False,
        },
        "run": {
            "runId": "",
            "reviewer": "",
            "elapsedSeconds": None,
            "outcome": "",
            "validatorOutput": "",
            "artifacts": [],
        },
    }

    return {
        "sc-003-operational": sc003,
        "sc-004-sectors": sc004,
        "sc-005-onboarding": sc005,
        "sc-006-timing": sc006,
    }


def _build_fixture(root: Path) -> None:
    for stem, data in _valid_docs().items():
        _write_yaml_json(root, stem, data)


def test_feature_evidence_valid_fixture_passes(tmp_path: Path) -> None:
    _build_fixture(tmp_path)
    assert run(tmp_path) == []


def test_sc003_missing_role_fails(tmp_path: Path) -> None:
    _build_fixture(tmp_path)
    yaml_path = tmp_path / "specs/004-actor-github-agents/evidence/sc-003-operational.yaml"
    data = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    data["roles"] = [row for row in data["roles"] if row["roleId"] != "risk-manager"]
    _write_yaml_json(tmp_path, "sc-003-operational", data)
    violations = run(tmp_path)
    assert any("missing required operational role" in item for item in violations)


def test_sc004_archived_target_and_missing_citation_fail(tmp_path: Path) -> None:
    _build_fixture(tmp_path)
    yaml_path = tmp_path / "specs/004-actor-github-agents/evidence/sc-004-sectors.yaml"
    data = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    data["families"][0]["questions"][0]["targetAgentId"] = "fire-services"
    data["families"][1]["questions"][0]["primarySourceCitation"] = ""
    _write_yaml_json(tmp_path, "sc-004-sectors", data)
    violations = run(tmp_path)
    assert any("archived targetAgentId" in item for item in violations)
    assert any("primarySourceCitation is required" in item for item in violations)


def test_sc005_duplicate_and_post_response_edit_fail(tmp_path: Path) -> None:
    _build_fixture(tmp_path)
    yaml_path = tmp_path / "specs/004-actor-github-agents/evidence/sc-005-onboarding.yaml"
    data = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    data["status"] = "Measured"
    data["aggregate"] = {"eligible": 2, "favourable": 2, "measuredPercent": 100.0}
    data["responses"] = [
        {"respondentId": "anon-001", "score": 5},
        {"respondentId": "anon-001", "score": 4},
    ]
    data["firstResponseAt"] = "2026-09-15T10:00:00Z"
    data["instrumentLastModifiedAt"] = "2026-09-15T11:00:00Z"
    data["run"] = {"runId": "run-1", "reviewer": "reviewer"}
    _write_yaml_json(tmp_path, "sc-005-onboarding", data)
    violations = run(tmp_path)
    assert any("duplicate anonymized respondentId" in item for item in violations)
    assert any("post-response instrument edit detected" in item for item in violations)


def test_sc006_boundary_and_artifact_requirements_fail(tmp_path: Path) -> None:
    _build_fixture(tmp_path)
    yaml_path = tmp_path / "specs/004-actor-github-agents/evidence/sc-006-timing.yaml"
    data = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    data["status"] = "Measured"
    data["run"] = {
        "runId": "run-1",
        "reviewer": "reviewer",
        "elapsedSeconds": 1800,
        "outcome": "pass",
        "validatorOutput": "ok",
        "artifacts": [],
    }
    _write_yaml_json(tmp_path, "sc-006-timing", data)
    violations = run(tmp_path)
    assert any("requires non-empty run.artifacts" in item for item in violations)
    assert any("1800 must fail" in item for item in violations)
