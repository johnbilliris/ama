from __future__ import annotations

import ast
import base64
import hashlib
import json
import warnings
from copy import deepcopy
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, cast

import pytest
import rfc8785
from jsonschema import Draft202012Validator, FormatChecker, ValidationError

REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
CONTRACT_ROOT = REPOSITORY_ROOT / "specs" / "001-extension-list" / "contracts"
FIXTURE_ROOT = Path(__file__).resolve().parents[1] / "fixtures" / "evidence"
CURRENT_SCHEMA_NAMES = {
    "agent-action-audit.schema.json",
    "catalog-config.schema.json",
    "catalog-source.schema.json",
    "extension-list.schema.json",
    "external-validation-status.schema.json",
    "implementation-prerequisite-attestation.schema.json",
    "platform-evidence.schema.json",
    "root-regression-baseline.schema.json",
    "usability-evidence.schema.json",
}
PLANNED_SCHEMA_NAMES = {"read-only-evidence.schema.json", "performance-evidence.schema.json"}
SESSION_ID = "11111111-1111-4111-8111-111111111111"
ACTOR_ID = "22222222-2222-4222-8222-222222222222"
FORMAT_CHECKER = FormatChecker()
RESOURCE_PREFIX = "/subscriptions/sub/resourceGroups/rg/providers/"
SYNTHETIC_RESOURCE_PREFIX = "/subscriptions/synthetic/resourceGroups/rg/providers/"
SOVEREIGN_BINDINGS = {
    "execution_mode": "sovereign",
    "audit_sink": "immutable-au",
    "sovereign_session_id": SESSION_ID,
    "preflight_attestation_digest": "a" * 64,
    "execution_vm_resource_id": RESOURCE_PREFIX + "Microsoft.Compute/virtualMachines/runner",
    "audit_intent_event_id": "77777777-7777-4777-8777-777777777777",
    "audit_intent_event_digest": "b" * 64,
}


def _mapping(value: object) -> dict[str, object]:
    assert isinstance(value, dict)
    return value


def _records(value: object) -> list[dict[str, object]]:
    assert isinstance(value, list) and all(isinstance(item, dict) for item in value)
    return cast(list[dict[str, object]], value)


def _canonical_bytes(value: object) -> bytes:
    return rfc8785.dumps(cast(Any, value))


def _schema(name: str) -> dict[str, object]:
    value = json.loads((CONTRACT_ROOT / name).read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _validator(name: str) -> Draft202012Validator:
    return Draft202012Validator(_schema(name), format_checker=FORMAT_CHECKER)


def _planned_validator(name: str) -> Draft202012Validator:
    path = CONTRACT_ROOT / name
    assert path.is_file(), f"planned schema is absent: {name}"
    schema = json.loads(path.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema, format_checker=FORMAT_CHECKER)


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _identifier_digest(kind: str, stable_identifier: str) -> str:
    return hashlib.sha256(f"{kind}\0{stable_identifier}".encode()).hexdigest()


def _target(kind: str, stable_identifier: str, pre_state: object, post_state: object | None) -> dict[str, object]:
    return {
        "descriptor_version": "1.0",
        "kind": kind,
        "identifier_digest": _identifier_digest(kind, stable_identifier),
        "pre_state_digest": _digest(pre_state),
        "post_state_digest": None if post_state is None else _digest(post_state),
    }


def _audit_record(
    *,
    phase: str,
    event_id: str,
    sequence: int,
    target: dict[str, object],
    intent_event_id: str | None,
    session_id: str = SESSION_ID,
    action: str = "task.edit",
) -> dict[str, object]:
    record = {
        "schema_version": "1.0",
        "feature": "001-extension-list",
        "execution_mode": "local-synthetic",
        "audit_sink": "ephemeral-local",
        "ledger_partition": f"spec001-extension-list/{session_id}",
        "event_id": event_id,
        "session_id": session_id,
        "session_manifest_digest": "a" * 64,
        "sequence": sequence,
        "append_position_bytes": sequence * 100,
        "recorded_at": "2026-09-21T00:00:00Z",
        "actor_principal_id": ACTOR_ID,
        "phase": phase,
        "intent_event_id": intent_event_id,
        "action": action,
        "task_id": "T078",
        "rationale_code": "schema-validation",
        "outcome": "started" if phase == "intent" else "succeeded",
        "target": target,
        "target_digest": _digest(target),
        "previous_event_digest": "b" * 64,
        "event_digest": "c" * 64,
    }
    return record


def _validate_audit_pair(intent: dict[str, object], result: dict[str, object]) -> None:
    validator = _validator("agent-action-audit.schema.json")
    validator.validate(intent)
    validator.validate(result)
    if intent["phase"] != "intent" or result["phase"] != "result":
        raise ValueError("audit phases must be intent then result")
    if result["intent_event_id"] != intent["event_id"]:
        raise ValueError("audit intent linkage mismatch")
    intent_sequence = intent["sequence"]
    result_sequence = result["sequence"]
    assert isinstance(intent_sequence, int) and isinstance(result_sequence, int)
    if result_sequence != intent_sequence + 1:
        raise ValueError("audit pair must remain consecutive")
    if intent["session_id"] != result["session_id"] or intent["ledger_partition"] != result["ledger_partition"]:
        raise ValueError("audit pair cannot split sessions or partitions")
    expected_partition = f"spec001-extension-list/{intent['session_id']}"
    if intent["ledger_partition"] != expected_partition:
        raise ValueError("ledger partition must bind the session")
    intent_target = intent["target"]
    result_target = result["target"]
    assert isinstance(intent_target, dict) and isinstance(result_target, dict)
    for field in ("descriptor_version", "kind", "identifier_digest", "pre_state_digest"):
        if result_target[field] != intent_target[field]:
            raise ValueError("audit result target does not retain intent identity")
    if intent_target["post_state_digest"] is not None or result_target["post_state_digest"] is None:
        raise ValueError("audit phase state digests are invalid")
    for record in (intent, result):
        if record["target_digest"] != _digest(record["target"]):
            raise ValueError("audit target digest mismatch")
    if intent["action"] != "session.finalize" and intent_sequence > 48_998:
        raise ValueError("ordinary actions must reserve finalization capacity")


def _b64url(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode()


def _preflight_claims() -> dict[str, object]:
    return {
        "schema_version": "1.0",
        "feature": "001-extension-list",
        "execution_mode": "sovereign",
        "issuer": "ama-security-control-plane",
        "audience": "spec001-extension-list-sovereign-preflight",
        "algorithm": "ES256",
        "key_id": "https://signing.vault.azure.net/keys/preflight/1",
        "jti": "33333333-3333-4333-8333-333333333333",
        "challenge_id": "44444444-4444-4444-8444-444444444444",
        "nonce": "d" * 64,
        "requested_at": "2026-09-21T00:00:00Z",
        "issued_at": "2026-09-21T00:00:00Z",
        "not_before": "2026-09-21T00:00:00Z",
        "expires_at": "2026-09-21T00:10:00Z",
        "repository_digest": "e" * 64,
        "branch": "001-extension-list",
        "audit_ledger": {
            "storage_account_resource_id": RESOURCE_PREFIX + "Microsoft.Storage/storageAccounts/audit",
            "container_scope": RESOURCE_PREFIX
            + "Microsoft.Storage/storageAccounts/audit/blobServices/default/containers/ledger",
            "location": "australiaeast",
            "public_network_access": "Disabled",
            "default_network_action": "Deny",
            "private_endpoint_state": "Approved",
            "immutability_policy_mode": "Locked",
            "managed_identity_principal_id": ACTOR_ID,
            "coordinator_ready": True,
        },
        "execution_vm": {
            "resource_id": RESOURCE_PREFIX + "Microsoft.Compute/virtualMachines/runner",
            "vm_id": "55555555-5555-4555-8555-555555555555",
            "location": "australiaeast",
            "os": "ubuntu",
            "architecture": "x64",
            "encrypted_ephemeral_storage": True,
            "owner_authenticated_ipc": True,
        },
        "package_cache": {"cache_digest": "f" * 64, "authorized_au_mirror": True, "offline_ready": True},
        "private_dependencies": {
            "catalog_stores_ready": True,
            "evidence_store_ready": True,
            "study_store_ready": True,
            "role_enumeration_ready": True,
            "control_plane_verified": True,
            "control_plane_resource_id": RESOURCE_PREFIX + "Microsoft.Web/sites/control",
            "control_plane_location": "australiaeast",
            "control_plane_public_network_access": "Disabled",
            "control_plane_private_endpoint_state": "Approved",
            "signing_key_vault_verified": True,
            "signing_key_vault_resource_id": RESOURCE_PREFIX + "Microsoft.KeyVault/vaults/signing",
            "signing_key_vault_location": "australiaeast",
            "signing_key_vault_public_network_access": "Disabled",
            "signing_key_vault_private_endpoint_state": "Approved",
            "signing_key_enabled": True,
            "signing_key_expires_at": "2027-09-21T00:00:00Z",
            "pseudonymous_reviewer_store_ready": True,
        },
    }


def _preflight_artifact() -> dict[str, object]:
    claims = _preflight_claims()
    compact_jws = f"e30.{_b64url(_canonical_bytes(claims))}.c2ln"
    return {
        "claims": claims,
        "compact_jws": compact_jws,
        "attestation_digest": hashlib.sha256(compact_jws.encode()).hexdigest(),
        "replay_protection": {
            "marker_blob_uri": "https://amaaudit.blob.core.windows.net/ledger/spec001-extension-list/preflight-jti/33333333-3333-4333-8333-333333333333",
            "marker_created": True,
            "marker_created_at": "2026-09-21T00:00:00Z",
            "marker_retain_until": "2026-09-22T00:00:00Z",
            "immutability_policy_mode": "Locked",
        },
    }


def _decoded_payload(compact_jws: str) -> object:
    payload = compact_jws.split(".")[1]
    return json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))


def _usability_schema_fixture() -> dict[str, object]:
    participants: dict[str, list[dict[str, object]]] = {"novice": [], "experienced": []}
    allocation_records: list[dict[str, object]] = []
    for stratum in ("novice", "experienced"):
        for index in range(10):
            participant_id = f"synthetic-{stratum}-{index:02d}"
            task_variant = ("installed", "enabled")[index % 2]
            accommodations = ["screen-reader"] if index == 0 else []
            participants[stratum].append(
                {
                    "participant_id": participant_id,
                    "is_adult": True,
                    "uses_cli_monthly": True,
                    "prior_feature_exposure": False,
                    "spec_kit_workflows_last_6_months": 1 if stratum == "novice" else 6,
                    "used_extension_management": stratum == "experienced",
                    "task_variant": task_variant,
                    "requested_accommodations": accommodations,
                    "provided_accommodations": accommodations,
                    "installed_answer_correct": True,
                    "enabled_answer_correct": True,
                    "elapsed_seconds": 10.0,
                    "sc_001_success": True,
                    "sc_006_clarity_rating": 5,
                    "consulted_installation_directories": False,
                    "attempted_extension_command": False,
                    "sc_006_clear": True,
                }
            )
            allocation_records.append(
                {
                    "participant_id": participant_id,
                    "experience_stratum": stratum,
                    "task_variant": task_variant,
                    "allocation_position": index + 1,
                }
            )
    return {
        "schema_version": "1.0",
        "feature": "001-extension-list",
        "privacy": {
            "notice_version": "synthetic-v1",
            "notice_provided_at": "2026-09-21T00:00:00Z",
            "consent_recorded_for_all_included_and_excluded": True,
            "purpose_limitation": ["SC-001", "SC-006"],
            "au_store_resource_id": SYNTHETIC_RESOURCE_PREFIX + "Microsoft.Storage/storageAccounts/study",
            "reviewed_at": "2026-09-22T00:00:00Z",
            "retention_delete_by": "2026-12-20T00:00:00Z",
            "legal_hold_approved": False,
            "verified_deletion_required": True,
            "controller_role": "research-governance",
            "no_direct_identifiers": True,
            "reidentification_key_separated": True,
            "recruitment_records_separated": True,
            "least_privilege_named_study_team_access": True,
            "immutable_access_audit": True,
            "encrypted_in_transit": True,
            "encrypted_at_rest": True,
            "withdrawal_process_confirmed": True,
            "breach_response_process_confirmed": True,
        },
        "allocation_algorithm": "sha256-seeded-stratified-order-v1",
        "allocation_seed": "1" * 64,
        "task_variants": ["installed", "enabled"],
        "allocation_records": allocation_records,
        "participants": participants,
        "excluded_participants": [
            {
                "participant_id": "synthetic-excluded-00",
                "experience_stratum": "novice",
                "excluded_before_task_exposure": True,
                "exclusion_reason": "required-accommodation-unavailable",
                "unavailable_accommodations": ["hearing-support"],
                "replacement_participant_id": "synthetic-novice-00",
            }
        ],
        "aggregates": {
            "included_participant_count": 20,
            "sc_001_success_count": 20,
            "sc_006_clear_count": 20,
        },
        "review": {
            "reviewer_identifier": "reviewer-0123456789abcdef",
            "reviewer_role": "privacy",
            "reviewed_at": "2026-09-22T00:00:00Z",
            "decision": "approved",
            "decision_reason_code": "study-verified",
        },
    }


def test_current_schema_contracts_compile_exact_inventory_without_warnings() -> None:
    actual = {path.name for path in CONTRACT_ROOT.glob("*.schema.json")} - PLANNED_SCHEMA_NAMES
    assert actual == CURRENT_SCHEMA_NAMES
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        for name in sorted(CURRENT_SCHEMA_NAMES):
            Draft202012Validator.check_schema(_schema(name))
    assert caught == []


@pytest.mark.parametrize(
    ("kind", "stable_identifier", "pre_state", "post_state"),
    [
        (
            "repository-file",
            "tools/specify-cli/tests/example.py",
            {"state": "absent", "sha256": None},
            {"state": "file", "sha256": "1" * 64},
        ),
        ("command", '["pytest","-q"]', {"state": "not-started"}, {"state": "completed", "exit_code": 0}),
        ("decision", "T078\0schema-validation", {"state": "not-recorded"}, {"state": "recorded"}),
        ("validation", "T078\0current-schema", {"state": "not-run"}, {"state": "completed"}),
        ("session", SESSION_ID, {"state": "inactive"}, {"state": "active"}),
        ("runtime-request", "66666666-6666-4666-8666-666666666666", {"state": "not-processed"}, {"state": "completed"}),
        (
            "external-write",
            "spec001-extension-list/fake.json",
            {"state": "absent"},
            {"state": "created", "content_sha256": "2" * 64},
        ),
    ],
)
def test_current_schema_contracts_audit_target_algorithm_and_linkage(
    kind: str, stable_identifier: str, pre_state: object, post_state: object
) -> None:
    intent_id = "77777777-7777-4777-8777-777777777777"
    intent_target = _target(kind, stable_identifier, pre_state, None)
    result_target = _target(kind, stable_identifier, pre_state, post_state)
    intent = _audit_record(phase="intent", event_id=intent_id, sequence=10, target=intent_target, intent_event_id=None)
    result = _audit_record(
        phase="result",
        event_id="88888888-8888-4888-8888-888888888888",
        sequence=11,
        target=result_target,
        intent_event_id=intent_id,
    )
    _validate_audit_pair(intent, result)
    assert intent_target["identifier_digest"] == hashlib.sha256(f"{kind}\0{stable_identifier}".encode()).hexdigest()


def test_current_schema_contracts_audit_capacity_partition_and_no_rollover() -> None:
    target = _target("validation", "T078\0capacity", {"state": "not-run"}, None)
    result_target = _target("validation", "T078\0capacity", {"state": "not-run"}, {"state": "completed"})
    intent = _audit_record(
        phase="intent",
        event_id="77777777-7777-4777-8777-777777777777",
        sequence=48_999,
        target=target,
        intent_event_id=None,
    )
    result = _audit_record(
        phase="result",
        event_id="88888888-8888-4888-8888-888888888888",
        sequence=49_000,
        target=result_target,
        intent_event_id=str(intent["event_id"]),
    )
    with pytest.raises(ValueError, match="reserve finalization"):
        _validate_audit_pair(intent, result)

    intent["action"] = result["action"] = "session.finalize"
    _validate_audit_pair(intent, result)
    result["session_id"] = "99999999-9999-4999-8999-999999999999"
    result["ledger_partition"] = f"spec001-extension-list/{result['session_id']}"
    with pytest.raises(ValueError, match="split sessions"):
        _validate_audit_pair(intent, result)

    over_capacity = deepcopy(intent)
    over_capacity["sequence"] = 49_001
    with pytest.raises(ValidationError):
        _validator("agent-action-audit.schema.json").validate(over_capacity)


def test_current_schema_contracts_preflight_payload_request_and_replay_are_bound() -> None:
    schema = _schema("implementation-prerequisite-attestation.schema.json")
    artifact = _preflight_artifact()
    Draft202012Validator(schema, format_checker=FORMAT_CHECKER).validate(artifact)
    assert _decoded_payload(str(artifact["compact_jws"])) == artifact["claims"]
    assert artifact["attestation_digest"] == hashlib.sha256(str(artifact["compact_jws"]).encode()).hexdigest()

    claims = artifact["claims"]
    assert isinstance(claims, dict)
    request = {
        key: claims[key]
        for key in (
            "schema_version",
            "feature",
            "execution_mode",
            "challenge_id",
            "nonce",
            "requested_at",
            "repository_digest",
            "branch",
        )
    }
    definitions = _mapping(schema["$defs"])
    request_schema = {**_mapping(definitions["preflightRequest"]), "$defs": definitions}
    Draft202012Validator(request_schema, format_checker=FORMAT_CHECKER).validate(request)
    replay_protection = _mapping(artifact["replay_protection"])
    assert str(replay_protection["marker_blob_uri"]).endswith(str(claims["jti"]))
    created = datetime.fromisoformat(str(replay_protection["marker_created_at"]).replace("Z", "+00:00"))
    retained = datetime.fromisoformat(str(replay_protection["marker_retain_until"]).replace("Z", "+00:00"))
    assert retained - created >= timedelta(days=1)


def test_current_schema_contracts_platform_fixture_is_explicit_and_schema_valid() -> None:
    fixture_path = FIXTURE_ROOT / "platform-valid.json"
    assert fixture_path.is_file()
    _validator("platform-evidence.schema.json").validate(json.loads(fixture_path.read_text(encoding="utf-8")))


def test_current_schema_contracts_extension_evidence_is_digest_only_with_zero_warnings() -> None:
    entry: dict[str, object] = {
        "id": "synthetic-extension",
        "fallback_identity": None,
        "source_locations": [".specify/extensions/synthetic-extension"],
        "name": "Synthetic Extension",
        "description": None,
        "version": "1.0.0",
        "priority": 1,
        "enabled": True,
        "source": {"kind": "local"},
        "evidence": [{"kind": "local", "source_sha256": "a" * 64, "source_ordinal": 0, "record_sha256": "b" * 64}],
        "provides": {"commands": 0, "templates": 0, "scripts": 0, "hooks": 0},
        "install_allowed": None,
        "installed": True,
        "installed_version": "1.0.0",
        "available_versions": [],
        "activation_state": "active",
        "activation_diagnostic": None,
        "health": {"state": "healthy", "diagnostics": []},
        "conflict": False,
        "conflict_reasons": [],
        "catalog_sources": [],
    }
    _validator("extension-list.schema.json").validate([entry])
    evidence = _records(entry["evidence"])
    assert set(evidence[0]) == {"kind", "source_sha256", "source_ordinal", "record_sha256"}
    assert _mapping(entry["health"])["diagnostics"] == []
    for prohibited in ("source", "author", "canonical_record", "absolute_path", "raw_output"):
        assert prohibited not in evidence[0]


def test_current_schema_contracts_root_runtime_is_closed_and_path_free() -> None:
    baseline: dict[str, object] = {
        "schema_version": "1.0",
        "feature": "001-extension-list",
        "lifecycle": "external-temp-ephemeral",
        "raw_output_deleted": True,
        "command": (
            "uv run --no-sync pytest tests/unit tests/contract tests/integration "
            'tests/simulation -m "not azure_staging and not azure_foundry_staging '
            "and not azure_cosmos_staging and not azure_speech_staging and not "
            "azure_blob_worm_staging and not measurement_staging and not e2e and "
            'not load and not locust" --cov=apps --cov=packages '
            "--cov-report=xml --cov-report=term"
        ),
        "runtime": {"python_version": "3.12.1", "uv_version": "uv 0.11.0", "os": "synthetic", "architecture": "x64"},
        "working_directory": ".",
        "captured_before_package_source": True,
        "captured_at": "2026-09-21T00:00:00Z",
        "exit_code": 0,
        "normalized_failures": [],
        "normalized_collection_errors": [],
        "output": {"byte_count": 0, "line_count": 0, "sha256": "a" * 64},
    }
    validator = _validator("root-regression-baseline.schema.json")
    validator.validate(baseline)
    for field, value in _mapping(baseline["runtime"]).items():
        assert not Path(str(value)).is_absolute(), field
    invalid = deepcopy(baseline)
    _mapping(invalid["runtime"])["python_executable"] = "C:/Python/python.exe"
    with pytest.raises(ValidationError):
        validator.validate(invalid)


def test_current_schema_contracts_reviewers_are_pseudonymous_and_closed_coded() -> None:
    for schema_name, reason in (
        ("platform-evidence.schema.json", "evidence-verified"),
        ("usability-evidence.schema.json", "study-verified"),
    ):
        schema = _schema(schema_name)
        definitions = _mapping(schema["$defs"])
        review_schema = _mapping(definitions["review"])
        properties = _mapping(review_schema["properties"])
        reviewer_role = _mapping(properties["reviewer_role"])
        roles = cast(list[str], reviewer_role["enum"])
        role = roles[0]
        review = {
            "reviewer_identifier": "reviewer-0123456789abcdef",
            "reviewer_role": role,
            "reviewed_at": "2026-09-21T00:00:00Z",
            "decision": "approved",
            "decision_reason_code": reason,
        }
        validator = Draft202012Validator(review_schema, format_checker=FORMAT_CHECKER)
        validator.validate(review)
        with pytest.raises(ValidationError):
            validator.validate({**review, "reviewer_name": "Synthetic Reviewer"})


def test_usability_schema_contract_accepts_closed_privacy_allocation_and_review_shape() -> None:
    evidence = _usability_schema_fixture()
    _validator("usability-evidence.schema.json").validate(evidence)

    privacy = evidence["privacy"]
    participants = evidence["participants"]
    review = evidence["review"]
    assert isinstance(privacy, dict) and privacy["no_direct_identifiers"] is True
    assert isinstance(participants, dict)
    assert len(participants["novice"]) == len(participants["experienced"]) == 10
    assert participants["novice"][0]["requested_accommodations"] == ["screen-reader"]
    assert participants["novice"][0]["consulted_installation_directories"] is False
    assert participants["novice"][0]["attempted_extension_command"] is False
    assert isinstance(review, dict)
    assert set(review) == {
        "reviewer_identifier",
        "reviewer_role",
        "reviewed_at",
        "decision",
        "decision_reason_code",
    }


@pytest.mark.parametrize(
    ("section", "field", "value"),
    [
        ("top", "participant_name", "Synthetic Person"),
        ("privacy", "email_address", "synthetic@example.invalid"),
        ("participant", "free_text_notes", "synthetic note"),
        ("review", "reviewer_name", "Synthetic Reviewer"),
        ("review", "notes", "synthetic note"),
    ],
)
def test_usability_schema_contract_rejects_names_direct_identifiers_and_free_text(
    section: str, field: str, value: str
) -> None:
    evidence = _usability_schema_fixture()
    if section == "top":
        evidence[field] = value
    elif section == "privacy":
        privacy = evidence["privacy"]
        assert isinstance(privacy, dict)
        privacy[field] = value
    elif section == "participant":
        participants = evidence["participants"]
        assert isinstance(participants, dict)
        participants["novice"][0][field] = value
    else:
        review = evidence["review"]
        assert isinstance(review, dict)
        review[field] = value
    with pytest.raises(ValidationError):
        _validator("usability-evidence.schema.json").validate(evidence)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("reviewer_identifier", "reviewer-name"),
        ("reviewer_role", "operator"),
        ("decision", "pending"),
        ("decision_reason_code", "free-form-reason"),
    ],
)
def test_usability_schema_contract_rejects_open_review_values(field: str, value: str) -> None:
    evidence = _usability_schema_fixture()
    review = evidence["review"]
    assert isinstance(review, dict)
    review[field] = value
    with pytest.raises(ValidationError):
        _validator("usability-evidence.schema.json").validate(evidence)


def test_optional_in_memory_status_contract_accepts_only_two_pending_external_categories() -> None:
    status: list[dict[str, object]] = [
        {
            "validation": "sovereign-external-platform",
            "status": "pending-external",
            "reason": "Requires authorized external platform validation",
            "evidence_path": None,
            "validated_at": None,
        },
        {
            "validation": "human-study",
            "status": "pending-external",
            "reason": "Requires the authorized external human study",
            "evidence_path": None,
            "validated_at": None,
        },
    ]
    _validator("external-validation-status.schema.json").validate(status)


@pytest.mark.parametrize(
    ("index", "field", "value"),
    [
        (0, "status", "completed"),
        (0, "evidence_path", "artifacts/platform-evidence.json"),
        (1, "validated_at", "2026-09-21T00:00:00Z"),
        (0, "validation", "local-current-platform"),
        (1, "repository_path", "status.json"),
    ],
)
def test_optional_in_memory_status_contract_rejects_completion_paths_and_local_substitution(
    index: int, field: str, value: object
) -> None:
    status: list[dict[str, object]] = [
        {
            "validation": "sovereign-external-platform",
            "status": "pending-external",
            "reason": "External platform validation remains pending",
            "evidence_path": None,
            "validated_at": None,
        },
        {
            "validation": "human-study",
            "status": "pending-external",
            "reason": "External human study remains pending",
            "evidence_path": None,
            "validated_at": None,
        },
    ]
    status[index][field] = value
    with pytest.raises(ValidationError):
        _validator("external-validation-status.schema.json").validate(status)


def test_optional_in_memory_status_contract_has_no_repository_object_or_package_helper() -> None:
    assert list(REPOSITORY_ROOT.rglob("external-validation-status.json")) == []
    package_root = REPOSITORY_ROOT / "tools" / "specify-cli" / "src" / "specify_cli"
    prohibited_symbols: list[str] = []
    for path in package_root.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                normalized = node.name.casefold()
                if "external" in normalized and "status" in normalized:
                    prohibited_symbols.append(node.name)
                if "status" in normalized and ("serial" in normalized or "produc" in normalized):
                    prohibited_symbols.append(node.name)
    assert prohibited_symbols == []


def test_planned_ephemeral_schema_contracts_read_only_exact_closed_shape() -> None:
    validator = _planned_validator("read-only-evidence.schema.json")
    evidence = {
        "schema_version": "1.0",
        "feature": "001-extension-list",
        "category": "read-only-validation",
        "lifecycle": "encrypted-au-ephemeral",
        "validation_id": "66666666-6666-4666-8666-666666666666",
        "validated_at": "2026-09-21T00:00:00Z",
        "view": "installed",
        "output_mode": "json",
        "outcome": "succeeded",
        "exit_code": 0,
        "source_state_before_sha256": "c" * 64,
        "source_state_after_sha256": "c" * 64,
        "protected_state_before_sha256": "d" * 64,
        "protected_state_after_sha256": "d" * 64,
        "coverage_state_before_sha256": "e" * 64,
        "coverage_state_after_sha256": "e" * 64,
        **SOVEREIGN_BINDINGS,
        "peer_authenticated": True,
        "au_vm_verified": True,
        "encrypted_temporary_storage": True,
        "audit_transaction_complete": True,
        "raw_output_deleted": True,
        "repository_payload_persisted": False,
    }
    expected_fields = {
        "schema_version",
        "feature",
        "category",
        "lifecycle",
        "validation_id",
        "validated_at",
        "view",
        "output_mode",
        "outcome",
        "exit_code",
        "source_state_before_sha256",
        "source_state_after_sha256",
        "protected_state_before_sha256",
        "protected_state_after_sha256",
        "coverage_state_before_sha256",
        "coverage_state_after_sha256",
        *SOVEREIGN_BINDINGS,
        "peer_authenticated",
        "au_vm_verified",
        "encrypted_temporary_storage",
        "audit_transaction_complete",
        "raw_output_deleted",
        "repository_payload_persisted",
    }
    assert set(evidence) == expected_fields
    validator.validate(evidence)
    for forbidden in (
        "repository_path",
        "raw_output",
        "diff",
        "base64_payload",
        "absolute_path",
        "secret",
        "environment",
        "inventory",
        "participant_name",
        "external_claim",
    ):
        with pytest.raises(ValidationError):
            validator.validate({**evidence, forbidden: "prohibited"})


def test_planned_ephemeral_schema_contracts_performance_exact_closed_shape() -> None:
    validator = _planned_validator("performance-evidence.schema.json")
    evidence = {
        "os": "synthetic-os",
        "architecture": "x64",
        "cpu_model": "Synthetic CPU",
        "logical_cpu_count": 8,
        "total_memory_bytes": 17179869184,
        "python_version": "3.12.1",
        "package_version": "0.1.0",
        "lock_sha256": "f" * 64,
        "runner_id": "synthetic-runner",
        "network_disabled": True,
        "fixture_id": "performance-100",
        "fixture_count": 100,
        "executed_at": "2026-09-21T00:00:00Z",
        "warmup_outcomes": [
            {"exit_code": 0, "passed": True},
            {"exit_code": 0, "passed": True},
            {"exit_code": 0, "passed": True},
        ],
        "durations_seconds": [0.1 + index / 1000 for index in range(30)],
        "rank": 29,
        "p95_seconds": 0.128,
        "threshold_seconds": 2.000,
        "passed": True,
        **SOVEREIGN_BINDINGS,
    }
    required_fields = {
        "os",
        "architecture",
        "cpu_model",
        "logical_cpu_count",
        "total_memory_bytes",
        "python_version",
        "package_version",
        "lock_sha256",
        "network_disabled",
        "fixture_id",
        "fixture_count",
        "executed_at",
        "warmup_outcomes",
        "durations_seconds",
        "rank",
        "p95_seconds",
        "threshold_seconds",
        "passed",
        *SOVEREIGN_BINDINGS,
    }
    assert set(evidence) == required_fields | {"runner_id"}
    validator.validate(evidence)

    without_runner = {key: value for key, value in evidence.items() if key != "runner_id"}
    validator.validate(without_runner)
    for field, value in (
        ("logical_cpu_count", 0),
        ("total_memory_bytes", 0),
        ("fixture_count", 99),
        ("rank", 28),
        ("threshold_seconds", 2.001),
        ("network_disabled", False),
    ):
        with pytest.raises(ValidationError):
            validator.validate({**evidence, field: value})
    warmup_outcomes = _records(evidence["warmup_outcomes"])
    durations = cast(list[float], evidence["durations_seconds"])
    with pytest.raises(ValidationError):
        validator.validate({**evidence, "warmup_outcomes": warmup_outcomes[:2]})
    with pytest.raises(ValidationError):
        validator.validate({**evidence, "durations_seconds": durations[:29]})
    with pytest.raises(ValidationError):
        validator.validate({**evidence, "repository_payload_persisted": False})
