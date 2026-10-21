from __future__ import annotations

import hashlib
import importlib.resources
import importlib.util
import json
import sys
from copy import deepcopy
from pathlib import Path
from types import ModuleType
from typing import Any, cast

import pytest
import rfc8785
from jsonschema import Draft202012Validator, FormatChecker

# isort: split
from specify_cli.evidence import (
    HostedLifecycleContext,
    HostedWriteContext,
    validate_hosted_platform_semantics,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
FIXTURE_PATH = Path(__file__).parent / "fixtures" / "evidence" / "platform-valid.json"
SCHEMA_PATH = REPOSITORY_ROOT / "specs" / "001-extension-list" / "contracts" / "platform-evidence.schema.json"
SESSION_ID = "11111111-1111-4111-8111-111111111111"
FINAL_KEY = f"spec001-extension-list/{SESSION_ID}/final/platform-evidence.json"
SCRIPT_PATH = REPOSITORY_ROOT / "scripts" / "spec001" / "run_external_platform_validation.py"
CONTRIBUTOR_ROLE_ID = "ba92f5b4-2d11-453d-a403-e96b0029c9fe"


def _mapping(value: object) -> dict[str, object]:
    assert isinstance(value, dict)
    return value


def _load_operator_script() -> ModuleType:
    specification = importlib.util.spec_from_file_location("spec001_external_platform_validation", SCRIPT_PATH)
    if specification is None or specification.loader is None:
        raise AssertionError("external platform script could not be loaded")
    module = importlib.util.module_from_spec(specification)
    sys.modules[specification.name] = module
    specification.loader.exec_module(module)
    return module


class _RecordingAudit:
    def __init__(self, events: list[str]) -> None:
        self.events = events

    def begin(self, action: str, target: str) -> str:
        self.events.append(f"audit.begin:{action}:{target}")
        return "audit-intent-1"

    def complete(self, intent_event_id: str, action: str, target: str, outcome: str) -> None:
        assert intent_event_id == "audit-intent-1"
        self.events.append(f"audit.complete:{action}:{target}:{outcome}")


class _CollectTransport:
    def __init__(self, events: list[str], *, marker_created: bool = True) -> None:
        self.events = events
        self.marker_created = marker_created
        self.request: dict[str, object] | None = None
        self.written_payload: dict[str, object] | None = None

    def verify_pinned_resource(self, resource_kind: str, pins: dict[str, object]) -> dict[str, object]:
        self.events.append(f"verify:{resource_kind}")
        assert pins["allowed_regions"] == ["australiaeast", "australiasoutheast"]
        return {
            "arm_resource_id": pins["arm_resource_id"],
            "location": "australiaeast",
            "public_network_access": "Disabled",
            "default_network_action": "Deny",
            "private_endpoint_id": pins["private_endpoint_id"],
            "private_dns_host": pins["private_dns_host"],
            "private_dns_only": True,
            "key_enabled": True,
            "key_expires_at": "2027-09-21T00:00:00Z",
        }

    def authorization_inventory(self, required_role_id: str) -> dict[str, object]:
        self.events.append("authorization")
        assert required_role_id == CONTRIBUTOR_ROLE_ID
        return _contributor_inventory()

    def post_attestation(
        self,
        endpoint: str,
        scope: str,
        request: dict[str, object],
        *,
        deadline_seconds: int,
        maximum_response_bytes: int,
        allow_redirects: bool,
        retries: int,
    ) -> dict[str, str]:
        self.events.append("attestation.post")
        assert endpoint == "https://attestation.private.example.invalid/spec001/prewrite"
        assert scope == "api://ama-security-control-plane/.default"
        assert deadline_seconds == 5
        assert maximum_response_bytes == 16 * 1024
        assert allow_redirects is False
        assert retries == 0
        assert set(request) == {
            "container_scope",
            "feature",
            "managed_identity_principal_id",
            "nonce",
            "no_broader_data_plane_write_role",
            "operation",
            "private_endpoint_connection_resource_id",
            "requested_at",
            "role_definition_id",
            "schema_version",
            "storage_account_resource_id",
            "target_blob_name",
            "validation_session_id",
        }
        self.request = request
        return {"compact_jws": "header.collect.signature"}

    def create_replay_marker_if_absent(self, marker: dict[str, object]) -> bool:
        self.events.append("marker.create")
        assert marker["immutability_policy_mode"] == "Locked"
        assert marker["retain_for_seconds"] == 86_400
        return self.marker_created

    def create_blob_if_absent(self, target: str, payload: dict[str, object]) -> bool:
        self.events.append("fragment.create")
        self.written_payload = payload
        return True


class _FinalizeTransport(_CollectTransport):
    def __init__(
        self,
        events: list[str],
        fragments: dict[str, dict[str, object]],
        *,
        marker_created: bool = True,
    ) -> None:
        super().__init__(events, marker_created=marker_created)
        self.fragments = fragments

    def read_fragments(self, prefix: str) -> dict[str, dict[str, object]]:
        self.events.append("fragments.read")
        assert prefix == f"spec001-extension-list/{SESSION_ID}/fragments/"
        return deepcopy(self.fragments)

    def create_blob_if_absent(self, target: str, payload: dict[str, object]) -> bool:
        self.events.append("final.create")
        self.written_payload = payload
        return True


def _contributor_inventory() -> dict[str, object]:
    target_scope = (
        "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/rg-spec001-au/"
        "providers/Microsoft.Storage/storageAccounts/amaevidence/blobServices/default/containers/evidence"
    )
    return {
        "enumeration_complete": True,
        "groups_resolved": True,
        "scopes_resolved": True,
        "roles_resolved": True,
        "vm_principal_id": "00000000-0000-4000-8000-000000000010",
        "transitive_group_ids": [],
        "target_scope": target_scope,
        "ancestor_scopes": [],
        "required_role_id": CONTRIBUTOR_ROLE_ID,
        "role_definitions": {
            CONTRIBUTOR_ROLE_ID: {
                "name": "Storage Blob Data Contributor",
                "built_in": True,
                "data_actions": [
                    "Microsoft.Storage/storageAccounts/blobServices/containers/blobs/read",
                    "Microsoft.Storage/storageAccounts/blobServices/containers/blobs/write",
                ],
                "not_data_actions": [],
            }
        },
        "assignments": [
            {
                "principal_id": "00000000-0000-4000-8000-000000000010",
                "scope": target_scope,
                "role_definition_id": CONTRIBUTOR_ROLE_ID,
                "eligible": False,
            }
        ],
    }


def _collect_request(operator: ModuleType) -> Any:
    return operator.CollectRequest(
        session_id=SESSION_ID,
        storage_account_resource_id=(
            "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/rg-spec001-au/"
            "providers/Microsoft.Storage/storageAccounts/amaevidence"
        ),
        container_name="evidence",
        blob_account_host="amaevidence.blob.core.windows.net",
        container_scope=_contributor_inventory()["target_scope"],
        private_endpoint_connection_resource_id=(
            "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/rg-spec001-au/"
            "providers/Microsoft.Network/privateEndpointConnections/pec-spec001-evidence"
        ),
        vm_principal_id="00000000-0000-4000-8000-000000000010",
        target_blob_name=f"spec001-extension-list/{SESSION_ID}/fragments/windows-vm-001.json",
        record={"synthetic": True},
    )


def _verified_lifecycle(operator: ModuleType) -> Any:
    return operator.OperatorLifecycle(
        execution_mode="sovereign",
        bootstrap_checks=("protected-state", "dispatcher-root-regression"),
        sovereign_preflight_verified=True,
        daemon_session_verified=True,
        peer_authenticated=True,
        dispatcher_invocation=True,
        fake_transport=True,
    )


def _finalize_request(operator: ModuleType) -> Any:
    collect = _collect_request(operator)
    return operator.FinalizeRequest(
        session_id=collect.session_id,
        storage_account_resource_id=collect.storage_account_resource_id,
        container_name=collect.container_name,
        blob_account_host=collect.blob_account_host,
        container_scope=collect.container_scope,
        private_endpoint_connection_resource_id=collect.private_endpoint_connection_resource_id,
        vm_principal_id=collect.vm_principal_id,
        target_blob_name=FINAL_KEY,
        review={
            "reviewer_identifier": "reviewer-0000000000000001",
            "reviewer_role": "security",
            "reviewed_at": "2026-09-21T00:00:00Z",
            "decision": "approved",
            "decision_reason_code": "evidence-verified",
        },
    )


def _claims_for_request(request: dict[str, object]) -> dict[str, object]:
    return {
        **request,
        "issuer": "ama-security-control-plane",
        "audience": "spec001-extension-list-prewrite",
        "algorithm": "ES256",
        "jti": "33333333-3333-4333-8333-333333333341",
        "issued_at": "2026-09-21T00:00:00Z",
        "not_before": "2026-09-21T00:00:00Z",
        "expires_at": "2026-09-21T00:05:00Z",
        "key_id": "https://kv-spec001-au.vault.azure.net/keys/prewrite/00000000000000000000000000000001",
        "reviewer_identifier": "reviewer-0000000000000001",
        "reviewer_role": "security",
        "attested_at": "2026-09-21T00:00:00Z",
    }


def test_collect_prewrite_boundary_uses_shared_audit_authorization_attestation_and_replay(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    operator = _load_operator_script()
    events: list[str] = []
    transport = _CollectTransport(events)
    shared_calls: list[dict[str, object]] = []
    shared_evaluator = operator.evaluate_storage_blob_authorization

    def evaluate(inventory: dict[str, object]) -> object:
        shared_calls.append(inventory)
        return shared_evaluator(inventory)

    monkeypatch.setattr(operator, "evaluate_storage_blob_authorization", evaluate)

    def verify(compact_jws: str, trust_bundle: dict[str, object]) -> dict[str, object]:
        events.append("attestation.verify")
        assert compact_jws == "header.collect.signature"
        assert trust_bundle["schema_version"] == "1.0"
        assert transport.request is not None
        return _claims_for_request(transport.request)

    result = operator.run_collect(
        _collect_request(operator),
        lifecycle=_verified_lifecycle(operator),
        transport=transport,
        audit=_RecordingAudit(events),
        nonce_factory=lambda: "a" * 64,
        clock=lambda: "2026-09-21T00:00:00Z",
        signature_verifier=verify,
    )

    assert result == operator.OperatorResult(status="completed-fake", qualifying=False, persisted=False)
    assert len(shared_calls) == 1
    assert events == [
        f"audit.begin:external.collect:{_collect_request(operator).target_blob_name}",
        "verify:storage",
        "verify:control_plane",
        "verify:key_vault",
        "authorization",
        "attestation.post",
        "attestation.verify",
        "marker.create",
        "fragment.create",
        f"audit.complete:external.collect:{_collect_request(operator).target_blob_name}:succeeded",
    ]
    assert transport.written_payload is not None
    boundary = transport.written_payload["storage_boundary"]
    assert isinstance(boundary, dict)
    assert boundary["replay_marker_created"] is True
    assert boundary["write_operation"] == "collect-fragment"


@pytest.mark.parametrize(
    "lifecycle_change",
    [
        {"dispatcher_invocation": False},
        {"peer_authenticated": False},
        {"bootstrap_checks": ("protected-state",)},
        {"fake_transport": False},
    ],
)
def test_collect_prewrite_boundary_rejects_direct_or_incomplete_lifecycle_before_payload_creation(
    lifecycle_change: dict[str, object],
) -> None:
    operator = _load_operator_script()
    lifecycle_values = {
        field: getattr(_verified_lifecycle(operator), field)
        for field in operator.OperatorLifecycle.__dataclass_fields__
    }
    lifecycle_values.update(lifecycle_change)
    payload_calls: list[str] = []
    transport = _CollectTransport([])
    with pytest.raises(RuntimeError, match="dispatcher|lifecycle|fake"):
        operator.run_collect(
            _collect_request(operator),
            lifecycle=operator.OperatorLifecycle(**lifecycle_values),
            transport=transport,
            audit=_RecordingAudit([]),
            nonce_factory=lambda: "a" * 64,
            clock=lambda: "2026-09-21T00:00:00Z",
            signature_verifier=lambda *_: {},
            payload_observer=lambda: payload_calls.append("created"),
        )
    assert payload_calls == []
    assert transport.events == []


def test_collect_prewrite_boundary_rejects_replay_before_fragment_write() -> None:
    operator = _load_operator_script()
    events: list[str] = []
    transport = _CollectTransport(events, marker_created=False)

    def verify(_: str, __: dict[str, object]) -> dict[str, object]:
        assert transport.request is not None
        return _claims_for_request(transport.request)

    with pytest.raises(RuntimeError, match="replay"):
        operator.run_collect(
            _collect_request(operator),
            lifecycle=_verified_lifecycle(operator),
            transport=transport,
            audit=_RecordingAudit(events),
            nonce_factory=lambda: "a" * 64,
            clock=lambda: "2026-09-21T00:00:00Z",
            signature_verifier=verify,
        )
    assert "fragment.create" not in events


def test_collect_prewrite_boundary_trust_resource_is_readable() -> None:
    resource = importlib.resources.files("specify_cli").joinpath("trusted_attestation_keys.json")
    trust_bundle = json.loads(resource.read_text(encoding="utf-8"))
    assert trust_bundle["schema_version"] == "1.0"
    assert trust_bundle["attestation_endpoint"] == "https://attestation.private.example.invalid/spec001/prewrite"
    assert "d" not in trust_bundle["signing_keys"][0]["public_jwk"]


def test_finalize_prewrite_boundary_rechecks_controls_and_creates_marker_before_final_write() -> None:
    operator = _load_operator_script()
    fragments, _, _ = _hosted_inputs()
    events: list[str] = []
    transport = _FinalizeTransport(events, fragments)

    def verify(_: str, __: dict[str, object]) -> dict[str, object]:
        events.append("attestation.verify")
        assert transport.request is not None
        claims = _claims_for_request(transport.request)
        claims["jti"] = "33333333-3333-4333-8333-333333333349"
        claims["nonce"] = "f" * 64
        return claims

    result = operator.run_finalize(
        _finalize_request(operator),
        lifecycle=_verified_lifecycle(operator),
        transport=transport,
        audit=_RecordingAudit(events),
        nonce_factory=lambda: "f" * 64,
        clock=lambda: "2026-09-21T00:00:00Z",
        signature_verifier=verify,
    )

    assert result == operator.OperatorResult(status="completed-fake", qualifying=False, persisted=False)
    assert events == [
        f"audit.begin:external.finalize:{FINAL_KEY}",
        "verify:storage",
        "verify:control_plane",
        "verify:key_vault",
        "authorization",
        "attestation.post",
        "attestation.verify",
        "marker.create",
        "fragments.read",
        "final.create",
        f"audit.complete:external.finalize:{FINAL_KEY}:succeeded",
    ]
    assert transport.written_payload is not None
    assert transport.written_payload["review"] == _finalize_request(operator).review
    assert _mapping(transport.written_payload["storage_boundary"])["write_operation"] == "finalize-canonical"


def test_finalize_prewrite_boundary_rejects_direct_invocation_before_fragment_access() -> None:
    operator = _load_operator_script()
    fragments, _, _ = _hosted_inputs()
    transport = _FinalizeTransport([], fragments)
    lifecycle = _verified_lifecycle(operator)
    values = {field: getattr(lifecycle, field) for field in operator.OperatorLifecycle.__dataclass_fields__}
    values["dispatcher_invocation"] = False
    with pytest.raises(RuntimeError, match="dispatcher"):
        operator.run_finalize(
            _finalize_request(operator),
            lifecycle=operator.OperatorLifecycle(**values),
            transport=transport,
            audit=_RecordingAudit([]),
            nonce_factory=lambda: "f" * 64,
            clock=lambda: "2026-09-21T00:00:00Z",
            signature_verifier=lambda *_: {},
        )
    assert transport.events == []


def test_finalize_prewrite_boundary_rejects_existing_marker_before_fragment_access() -> None:
    operator = _load_operator_script()
    fragments, _, _ = _hosted_inputs()
    events: list[str] = []
    transport = _FinalizeTransport(events, fragments, marker_created=False)

    def verify(_: str, __: dict[str, object]) -> dict[str, object]:
        assert transport.request is not None
        claims = _claims_for_request(transport.request)
        claims["jti"] = "33333333-3333-4333-8333-333333333349"
        claims["nonce"] = "f" * 64
        return claims

    with pytest.raises(RuntimeError, match="replay"):
        operator.run_finalize(
            _finalize_request(operator),
            lifecycle=_verified_lifecycle(operator),
            transport=transport,
            audit=_RecordingAudit(events),
            nonce_factory=lambda: "f" * 64,
            clock=lambda: "2026-09-21T00:00:00Z",
            signature_verifier=verify,
        )
    assert "fragments.read" not in events
    assert "final.create" not in events


@pytest.mark.parametrize(
    "review",
    [
        {"reviewer_name": "prohibited"},
        {"decision": "approved", "decision_reason_code": "evidence-rejected"},
        {"reviewer_identifier": "person@example.invalid"},
    ],
)
def test_finalize_prewrite_boundary_requires_pseudonymous_closed_review(review: dict[str, str]) -> None:
    operator = _load_operator_script()
    request = _finalize_request(operator)
    invalid_review = {**request.review, **review}
    values = {field: getattr(request, field) for field in operator.FinalizeRequest.__dataclass_fields__}
    values["review"] = invalid_review
    with pytest.raises(RuntimeError, match="review"):
        operator.run_finalize(
            operator.FinalizeRequest(**values),
            lifecycle=_verified_lifecycle(operator),
            transport=_FinalizeTransport([], _hosted_inputs()[0]),
            audit=_RecordingAudit([]),
            nonce_factory=lambda: "f" * 64,
            clock=lambda: "2026-09-21T00:00:00Z",
            signature_verifier=lambda *_: {},
        )


def test_finalize_prewrite_boundary_requires_fresh_attestation_and_exact_fragment_agreement() -> None:
    operator = _load_operator_script()
    fragments, _, _ = _hosted_inputs()
    second = list(fragments.values())[1]
    second_record = _mapping(second["record"])
    _mapping(second_record["package"])["version"] = "different"
    _digest_record(second_record)
    transport = _FinalizeTransport([], fragments)

    def verify(_: str, __: dict[str, object]) -> dict[str, object]:
        assert transport.request is not None
        claims = _claims_for_request(transport.request)
        claims["jti"] = "33333333-3333-4333-8333-333333333349"
        claims["nonce"] = "f" * 64
        return claims

    with pytest.raises(ValueError, match="agreement"):
        operator.run_finalize(
            _finalize_request(operator),
            lifecycle=_verified_lifecycle(operator),
            transport=transport,
            audit=_RecordingAudit([]),
            nonce_factory=lambda: "f" * 64,
            clock=lambda: "2026-09-21T00:00:00Z",
            signature_verifier=verify,
        )


def _digest_record(record: dict[str, object]) -> None:
    unsigned = {key: value for key, value in record.items() if key != "evidence_digest"}
    record["evidence_digest"] = hashlib.sha256(rfc8785.dumps(cast(Any, unsigned))).hexdigest()


def _configure_boundary(
    boundary: dict[str, object], *, operation: str, target_key: str, jti: str, nonce: str, compact_jws: str
) -> None:
    marker_name = f"spec001-extension-list/attestation-jti/{jti}"
    boundary.update(
        {
            "replay_marker_blob_name": marker_name,
            "replay_marker_blob_uri": f"https://amaevidence.blob.core.windows.net/evidence/{marker_name}",
            "replay_marker_created": True,
            "replay_marker_created_at": "2026-09-21T00:00:00Z",
            "replay_marker_retain_until": "2026-09-22T00:00:00Z",
            "immutability_policy_mode": "Locked",
            "write_operation": operation,
        }
    )
    attestation = boundary["attestation"]
    assert isinstance(attestation, dict)
    attestation.update(
        {
            "jti": jti,
            "nonce": nonce,
            "operation": operation,
            "target_blob_name": target_key,
            "compact_jws": compact_jws,
            "attestation_digest": hashlib.sha256(compact_jws.encode()).hexdigest(),
        }
    )


def _hosted_inputs() -> tuple[dict[str, dict[str, object]], dict[str, object], HostedLifecycleContext]:
    document = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    assert isinstance(document, dict)
    records = document["records"]
    assert isinstance(records, list)
    fragments: dict[str, dict[str, object]] = {}
    writes: list[HostedWriteContext] = []
    jtis = (
        "33333333-3333-4333-8333-333333333331",
        "33333333-3333-4333-8333-333333333332",
    )
    for index, record in enumerate(records):
        assert isinstance(record, dict)
        _digest_record(record)
        key = f"spec001-extension-list/{SESSION_ID}/fragments/{record['os']}-{record['vm_id']}.json"
        boundary = deepcopy(document["storage_boundary"])
        assert isinstance(boundary, dict)
        _configure_boundary(
            boundary,
            operation="collect-fragment",
            target_key=key,
            jti=jtis[index],
            nonce=str(index + 1) * 64,
            compact_jws=f"header0{index + 1}.payload0{index + 1}.signature0{index + 1}",
        )
        fragments[key] = {
            "schema_version": "1.0",
            "feature": "001-extension-list",
            "category": "sovereign-external-platform-fragment",
            "validation_session_id": SESSION_ID,
            "script_path": "scripts/spec001/run_external_platform_validation.py",
            "storage_boundary": boundary,
            "record": deepcopy(record),
        }
        writes.append(
            HostedWriteContext(
                target_key=key,
                operation="collect-fragment",
                conditional_create=True,
                marker_created_before_write=True,
                audit_action="external.collect",
            )
        )

    final_boundary = document["storage_boundary"]
    assert isinstance(final_boundary, dict)
    _configure_boundary(
        final_boundary,
        operation="finalize-canonical",
        target_key=FINAL_KEY,
        jti="33333333-3333-4333-8333-333333333333",
        nonce="f" * 64,
        compact_jws="header03.payload03.signature03",
    )
    writes.append(
        HostedWriteContext(
            target_key=FINAL_KEY,
            operation="finalize-canonical",
            conditional_create=True,
            marker_created_before_write=True,
            audit_action="external.finalize",
        )
    )
    lifecycle = HostedLifecycleContext(
        writes=tuple(writes),
        human_review_audited=True,
        human_lifecycle_actions_audited=True,
        fake=True,
    )
    return fragments, document, lifecycle


def _schema_validate(fragments: dict[str, dict[str, object]], document: dict[str, object]) -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    checker = FormatChecker()
    Draft202012Validator(schema, format_checker=checker).validate(document)
    definitions = _mapping(schema["$defs"])
    fragment_schema = {**_mapping(definitions["platformFragment"]), "$defs": definitions}
    validator = Draft202012Validator(fragment_schema, format_checker=checker)
    for fragment in fragments.values():
        validator.validate(fragment)


def test_hosted_lifecycle_semantics_accepts_exact_fragments_and_final_document() -> None:
    fragments, document, lifecycle = _hosted_inputs()
    _schema_validate(fragments, document)
    result = validate_hosted_platform_semantics(fragments, document, lifecycle)
    assert result.status == "validated-fake"
    assert result.qualifying is False
    assert result.persisted is False


def test_hosted_lifecycle_semantics_recomputes_record_digests_and_exact_fragment_keys() -> None:
    fragments, document, lifecycle = _hosted_inputs()
    first_key = next(iter(fragments))
    _mapping(fragments[first_key]["record"])["evidence_digest"] = "0" * 64
    with pytest.raises(ValueError, match="digest"):
        validate_hosted_platform_semantics(fragments, document, lifecycle)

    fragments, document, lifecycle = _hosted_inputs()
    first_key = next(iter(fragments))
    fragments[f"{first_key}.wrong"] = fragments.pop(first_key)
    with pytest.raises(ValueError, match="key"):
        validate_hosted_platform_semantics(fragments, document, lifecycle)


def test_hosted_lifecycle_semantics_enforces_cardinality_and_cross_fragment_agreement() -> None:
    fragments, document, lifecycle = _hosted_inputs()
    fragments.pop(next(iter(fragments)))
    with pytest.raises(ValueError, match="cardinality"):
        validate_hosted_platform_semantics(fragments, document, lifecycle)

    fragments, document, lifecycle = _hosted_inputs()
    second = list(fragments.values())[1]
    second_record = _mapping(second["record"])
    _mapping(second_record["package"])["version"] = "0.2.0"
    _digest_record(second_record)
    with pytest.raises(ValueError, match="agreement"):
        validate_hosted_platform_semantics(fragments, document, lifecycle)


def test_hosted_lifecycle_semantics_requires_pseudonymous_closed_review() -> None:
    fragments, document, lifecycle = _hosted_inputs()
    _mapping(document["review"])["decision_reason_code"] = "evidence-rejected"
    with pytest.raises(ValueError, match="review"):
        validate_hosted_platform_semantics(fragments, document, lifecycle)

    fragments, document, lifecycle = _hosted_inputs()
    _mapping(document["review"])["reviewer_name"] = "prohibited"
    with pytest.raises(ValueError, match="review"):
        validate_hosted_platform_semantics(fragments, document, lifecycle)


@pytest.mark.parametrize("field", ["jti", "nonce", "compact_jws"])
def test_hosted_lifecycle_semantics_requires_distinct_attestation_values(field: str) -> None:
    fragments, document, lifecycle = _hosted_inputs()
    boundaries = [_mapping(fragment["storage_boundary"]) for fragment in fragments.values()]
    boundaries.append(_mapping(document["storage_boundary"]))
    first_attestation = _mapping(boundaries[0]["attestation"])
    second_attestation = _mapping(boundaries[1]["attestation"])
    second_attestation[field] = first_attestation[field]
    if field == "jti":
        marker_name = f"spec001-extension-list/attestation-jti/{first_attestation[field]}"
        boundaries[1]["replay_marker_blob_name"] = marker_name
        boundaries[1]["replay_marker_blob_uri"] = f"https://amaevidence.blob.core.windows.net/evidence/{marker_name}"
    elif field == "compact_jws":
        second_attestation["attestation_digest"] = hashlib.sha256(str(first_attestation[field]).encode()).hexdigest()
    with pytest.raises(ValueError, match="distinct"):
        validate_hosted_platform_semantics(fragments, document, lifecycle)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("replay_marker_created", False),
        ("replay_marker_blob_uri", "https://amaevidence.blob.core.windows.net/evidence/wrong"),
        ("replay_marker_retain_until", "2026-09-21T00:00:00Z"),
        ("immutability_policy_mode", "Unlocked"),
        ("write_operation", "finalize-canonical"),
    ],
)
def test_hosted_lifecycle_semantics_requires_immutable_marker_before_each_write(field: str, value: object) -> None:
    fragments, document, lifecycle = _hosted_inputs()
    boundary = _mapping(next(iter(fragments.values()))["storage_boundary"])
    boundary[field] = value
    with pytest.raises(ValueError, match="marker|operation|immutability"):
        validate_hosted_platform_semantics(fragments, document, lifecycle)


@pytest.mark.parametrize(
    "change",
    ["conditional_create", "marker_created_before_write", "collect_audit", "finalize_audit", "human_review"],
)
def test_hosted_lifecycle_semantics_requires_conditional_creation_and_audited_actions(change: str) -> None:
    fragments, document, lifecycle = _hosted_inputs()
    writes = list(lifecycle.writes)
    if change == "conditional_create":
        writes[0] = HostedWriteContext(**{**writes[0].__dict__, "conditional_create": False})
    elif change == "marker_created_before_write":
        writes[0] = HostedWriteContext(**{**writes[0].__dict__, "marker_created_before_write": False})
    elif change == "collect_audit":
        writes[0] = HostedWriteContext(**{**writes[0].__dict__, "audit_action": "missing"})
    elif change == "finalize_audit":
        writes[-1] = HostedWriteContext(**{**writes[-1].__dict__, "audit_action": "missing"})
    else:
        lifecycle = HostedLifecycleContext(
            writes=tuple(writes),
            human_review_audited=False,
            human_lifecycle_actions_audited=False,
            fake=True,
        )
    if change != "human_review":
        lifecycle = HostedLifecycleContext(
            writes=tuple(writes),
            human_review_audited=True,
            human_lifecycle_actions_audited=True,
            fake=True,
        )
    with pytest.raises(ValueError, match="conditional|marker|audit|human"):
        validate_hosted_platform_semantics(fragments, document, lifecycle)
