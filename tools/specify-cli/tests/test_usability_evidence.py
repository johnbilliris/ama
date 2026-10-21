from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import cast

import pytest
from jsonschema import Draft202012Validator, FormatChecker

# isort: split
from specify_cli.evidence import UsabilityLifecycleContext, validate_usability_semantics

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "evidence"
SCHEMA_PATH = REPOSITORY_ROOT / "specs" / "001-extension-list" / "contracts" / "usability-evidence.schema.json"


def _evidence(name: str = "usability-passing.json") -> dict[str, object]:
    value = json.loads((FIXTURE_ROOT / name).read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _schema_validate(evidence: dict[str, object]) -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(evidence)


def _mapping(value: object) -> dict[str, object]:
    assert isinstance(value, dict)
    return value


def _records(value: object) -> list[dict[str, object]]:
    assert isinstance(value, list) and all(isinstance(item, dict) for item in value)
    return cast(list[dict[str, object]], value)


def _lifecycle(**changes: object) -> UsabilityLifecycleContext:
    values: dict[str, object] = {
        "execution_mode": "sovereign",
        "audit_sink": "immutable-au",
        "authorized_au_store": True,
        "collect_audited": True,
        "finalize_audited": True,
        "human_lifecycle_actions_audited": True,
        "fake": True,
    }
    values.update(changes)
    return UsabilityLifecycleContext(
        execution_mode=cast(str, values["execution_mode"]),
        audit_sink=cast(str, values["audit_sink"]),
        authorized_au_store=cast(bool, values["authorized_au_store"]),
        collect_audited=cast(bool, values["collect_audited"]),
        finalize_audited=cast(bool, values["finalize_audited"]),
        human_lifecycle_actions_audited=cast(bool, values["human_lifecycle_actions_audited"]),
        fake=cast(bool, values["fake"]),
    )


def test_usability_semantic_validator_reports_thresholds_separately_from_validity() -> None:
    passing = _evidence()
    failed = _evidence("usability-failed.json")
    _schema_validate(passing)
    _schema_validate(failed)

    passing_result = validate_usability_semantics(passing, _lifecycle())
    failed_result = validate_usability_semantics(failed, _lifecycle())

    assert passing_result.status == failed_result.status == "validated-fake"
    assert (passing_result.sc_001_count, passing_result.sc_001_passed) == (20, True)
    assert (passing_result.sc_006_count, passing_result.sc_006_passed) == (20, True)
    assert (failed_result.sc_001_count, failed_result.sc_001_passed) == (18, False)
    assert (failed_result.sc_006_count, failed_result.sc_006_passed) == (17, False)


@pytest.mark.parametrize(
    ("field", "value"),
    [("is_adult", False), ("uses_cli_monthly", False), ("prior_feature_exposure", True)],
)
def test_usability_semantic_validator_rejects_ineligible_participants(field: str, value: object) -> None:
    evidence = _evidence()
    novice = _records(_mapping(evidence["participants"])["novice"])
    novice[0][field] = value
    with pytest.raises(ValueError, match="eligibility"):
        validate_usability_semantics(evidence, _lifecycle())


def test_usability_semantic_validator_recomputes_deterministic_allocation() -> None:
    evidence = _evidence()
    _records(evidence["allocation_records"])[0]["allocation_position"] = 2
    with pytest.raises(ValueError, match="allocation"):
        validate_usability_semantics(evidence, _lifecycle())


def test_usability_semantic_validator_derives_outcomes_and_aggregates() -> None:
    evidence = _evidence()
    _records(_mapping(evidence["participants"])["novice"])[0]["sc_001_success"] = False
    with pytest.raises(ValueError, match="SC-001"):
        validate_usability_semantics(evidence, _lifecycle())

    evidence = _evidence()
    _mapping(evidence["aggregates"])["sc_006_clear_count"] = 19
    with pytest.raises(ValueError, match="aggregate"):
        validate_usability_semantics(evidence, _lifecycle())


def test_usability_semantic_validator_rejects_unfulfilled_accommodation() -> None:
    evidence = _evidence()
    _records(_mapping(evidence["participants"])["novice"])[0]["provided_accommodations"] = []
    with pytest.raises(ValueError, match="accommodation"):
        validate_usability_semantics(evidence, _lifecycle())


def test_usability_semantic_validator_rejects_invalid_replacement() -> None:
    evidence = _evidence()
    _records(evidence["excluded_participants"])[0]["replacement_participant_id"] = "synthetic-experienced-00"
    with pytest.raises(ValueError, match="replacement"):
        validate_usability_semantics(evidence, _lifecycle())


def test_usability_semantic_validator_enforces_retention_and_review_consistency() -> None:
    evidence = _evidence()
    _mapping(evidence["privacy"])["retention_delete_by"] = "2026-12-22T00:00:01Z"
    with pytest.raises(ValueError, match="retention"):
        validate_usability_semantics(evidence, _lifecycle())

    evidence = _evidence()
    _mapping(evidence["review"])["decision_reason_code"] = "study-rejected"
    with pytest.raises(ValueError, match="review"):
        validate_usability_semantics(evidence, _lifecycle())


@pytest.mark.parametrize(
    "changes",
    [
        {"execution_mode": "local-synthetic"},
        {"audit_sink": "ephemeral-local"},
        {"authorized_au_store": False},
        {"collect_audited": False},
        {"finalize_audited": False},
        {"human_lifecycle_actions_audited": False},
    ],
)
def test_usability_semantic_validator_requires_external_audited_lifecycle(changes: dict[str, object]) -> None:
    with pytest.raises((PermissionError, ValueError), match="lifecycle"):
        validate_usability_semantics(_evidence(), _lifecycle(**changes))


@pytest.mark.parametrize("field", ["participant_name", "email_address", "free_text_notes"])
def test_usability_semantic_validator_rejects_names_identifiers_and_free_text(field: str) -> None:
    evidence = deepcopy(_evidence())
    _records(_mapping(evidence["participants"])["novice"])[0][field] = "prohibited"
    with pytest.raises(ValueError, match="prohibited"):
        validate_usability_semantics(
            evidence,
            _lifecycle(),
        )
