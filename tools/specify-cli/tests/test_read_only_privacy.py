from __future__ import annotations

import json
from collections.abc import Callable
from copy import deepcopy
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker, ValidationError

# isort: split
from specify_cli.evidence import (
    EvidenceBindingContext,
    EvidenceValidationResult,
    produce_read_only_evidence,
    validate_read_only_semantics,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
SCHEMA_PATH = REPOSITORY_ROOT / "specs" / "001-extension-list" / "contracts" / "read-only-evidence.schema.json"
SESSION_ID = "11111111-1111-4111-8111-111111111111"
VM_RESOURCE_ID = "/subscriptions/sub/resourceGroups/rg/providers/Microsoft.Compute/virtualMachines/runner"
INTENT_ID = "77777777-7777-4777-8777-777777777777"
READ_ONLY_FIELDS = {
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
    "execution_mode",
    "audit_sink",
    "sovereign_session_id",
    "preflight_attestation_digest",
    "execution_vm_resource_id",
    "audit_intent_event_id",
    "audit_intent_event_digest",
    "peer_authenticated",
    "au_vm_verified",
    "encrypted_temporary_storage",
    "audit_transaction_complete",
    "raw_output_deleted",
    "repository_payload_persisted",
}


def _evidence() -> dict[str, object]:
    return {
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
        "execution_mode": "sovereign",
        "audit_sink": "immutable-au",
        "sovereign_session_id": SESSION_ID,
        "preflight_attestation_digest": "a" * 64,
        "execution_vm_resource_id": VM_RESOURCE_ID,
        "audit_intent_event_id": INTENT_ID,
        "audit_intent_event_digest": "b" * 64,
        "peer_authenticated": True,
        "au_vm_verified": True,
        "encrypted_temporary_storage": True,
        "audit_transaction_complete": True,
        "raw_output_deleted": True,
        "repository_payload_persisted": False,
    }


def _context(*, fake: bool = True, execution_mode: str = "sovereign") -> EvidenceBindingContext:
    return EvidenceBindingContext(
        execution_mode=execution_mode,
        audit_sink="immutable-au" if execution_mode == "sovereign" else "ephemeral-local",
        sovereign_session_id=SESSION_ID,
        preflight_attestation_digest="a" * 64,
        execution_vm_resource_id=VM_RESOURCE_ID,
        audit_intent_event_id=INTENT_ID,
        audit_intent_event_digest="b" * 64,
        audit_result_intent_event_id=INTENT_ID,
        preflight_signature_verified=True,
        live_imds_verified=True,
        live_imds_resource_id=VM_RESOURCE_ID,
        live_imds_location="australiaeast",
        standalone_vm_verified=True,
        immutable_ledger_verified=True,
        peer_authenticated=True,
        encrypted_temporary_storage=True,
        owner_only_temporary_storage=True,
        fake=fake,
    )


def _schema_validate(evidence: dict[str, object]) -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(evidence)


def test_read_only_semantic_validator_accepts_only_exact_fake_bound_shape() -> None:
    evidence = _evidence()
    _schema_validate(evidence)
    result = validate_read_only_semantics(evidence, _context())

    assert set(evidence) == READ_ONLY_FIELDS
    assert result.status == "validated-fake"
    assert result.qualifying is False
    assert result.persisted is False
    assert result.details is None


@pytest.mark.parametrize(
    ("field", "replacement", "message"),
    [
        ("source_state_after_sha256", "f" * 64, "source state"),
        ("protected_state_after_sha256", "f" * 64, "protected state"),
        ("coverage_state_after_sha256", "f" * 64, "coverage state"),
        ("exit_code", 1, "outcome"),
        ("peer_authenticated", False, "peer"),
        ("au_vm_verified", False, "AU VM"),
        ("encrypted_temporary_storage", False, "encrypted"),
        ("audit_transaction_complete", False, "audit transaction"),
        ("raw_output_deleted", False, "raw output"),
        ("repository_payload_persisted", True, "repository payload"),
    ],
)
def test_read_only_semantic_validator_rejects_state_or_lifecycle_drift(
    field: str, replacement: object, message: str
) -> None:
    evidence = {**_evidence(), field: replacement}
    with pytest.raises(ValueError, match=message):
        validate_read_only_semantics(evidence, _context())


@pytest.mark.parametrize(
    ("field", "replacement"),
    [
        ("execution_mode", "local-synthetic"),
        ("audit_sink", "ephemeral-local"),
        ("sovereign_session_id", "99999999-9999-4999-8999-999999999999"),
        ("preflight_attestation_digest", "f" * 64),
        (
            "execution_vm_resource_id",
            "/subscriptions/sub/resourceGroups/rg/providers/Microsoft.Compute/virtualMachines/other",
        ),
        ("audit_intent_event_id", "88888888-8888-4888-8888-888888888888"),
        ("audit_intent_event_digest", "f" * 64),
    ],
)
def test_read_only_semantic_validator_cross_checks_all_seven_bindings(field: str, replacement: object) -> None:
    evidence = {**_evidence(), field: replacement}
    with pytest.raises(ValueError, match="binding"):
        validate_read_only_semantics(evidence, _context())


def test_read_only_semantic_validator_rejects_unsigned_nonlive_or_mutable_contexts() -> None:
    context = _context()
    for field in (
        "preflight_signature_verified",
        "live_imds_verified",
        "standalone_vm_verified",
        "immutable_ledger_verified",
        "peer_authenticated",
        "encrypted_temporary_storage",
        "owner_only_temporary_storage",
    ):
        invalid = context.replaced(**{field: False})
        with pytest.raises(ValueError, match="boundary"):
            validate_read_only_semantics(_evidence(), invalid)
    with pytest.raises(ValueError, match="intent linkage"):
        validate_read_only_semantics(
            _evidence(),
            context.replaced(audit_result_intent_event_id="88888888-8888-4888-8888-888888888888"),
        )
    with pytest.raises(ValueError, match="live IMDS"):
        validate_read_only_semantics(
            _evidence(),
            context.replaced(
                live_imds_resource_id="/subscriptions/sub/resourceGroups/rg/providers/Microsoft.Compute/virtualMachines/other"
            ),
        )


def test_read_only_semantic_validator_rejects_private_or_unallowlisted_fields() -> None:
    for field in (
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
        evidence = deepcopy(_evidence())
        evidence[field] = "prohibited"
        with pytest.raises(ValueError, match="field set"):
            validate_read_only_semantics(evidence, _context())


def test_read_only_semantic_validator_local_synthetic_never_qualifies() -> None:
    with pytest.raises(PermissionError, match="local-synthetic"):
        validate_read_only_semantics(_evidence(), _context(execution_mode="local-synthetic"))
    with pytest.raises(PermissionError, match="fake"):
        validate_read_only_semantics(_evidence(), _context(fake=False))


class FakeEphemeralStore:
    def __init__(self, events: list[str], *, owner_only: bool = True) -> None:
        self.events = events
        self.owner_only = owner_only
        self.value: dict[str, object] | None = None
        self.logically_deleted = False

    def write(self, value: dict[str, object]) -> None:
        self.events.append("write")
        self.value = deepcopy(value)

    def logical_delete(self) -> None:
        self.events.append("delete")
        self.value = None
        self.logically_deleted = True


def _schema_validator(events: list[str]) -> Callable[[dict[str, object]], None]:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema, format_checker=FormatChecker())

    def validate(value: dict[str, object]) -> None:
        events.append("schema")
        validator.validate(value)

    return validate


def _semantic_validator(
    events: list[str],
) -> Callable[[dict[str, object], EvidenceBindingContext], EvidenceValidationResult]:
    def validate(value: dict[str, object], context: EvidenceBindingContext) -> EvidenceValidationResult:
        events.append("semantic")
        return validate_read_only_semantics(value, context)

    return validate


def _recording_evidence_factory(events: list[str]) -> Callable[[], dict[str, object]]:
    def create() -> dict[str, object]:
        events.append("factory")
        return _evidence()

    return create


def _copy_factory(evidence: dict[str, object]) -> Callable[[], dict[str, object]]:
    def create() -> dict[str, object]:
        return deepcopy(evidence)

    return create


def test_ephemeral_read_only_producer_fake_path_validates_then_deletes_without_qualifying() -> None:
    events: list[str] = []
    store = FakeEphemeralStore(events)

    result = produce_read_only_evidence(
        evidence_factory=_recording_evidence_factory(events),
        schema_validate=_schema_validator(events),
        semantic_validate=_semantic_validator(events),
        context=_context(),
        temporary_store=store,
        execution_mode="local-synthetic",
        qualifying=False,
    )

    assert events == ["factory", "write", "schema", "semantic", "delete"]
    assert store.logically_deleted is True
    assert store.value is None
    assert result.status == "passed-fake"
    assert result.qualifying is False
    assert result.persisted is False
    assert result.details is None


def test_ephemeral_read_only_producer_rejects_local_qualification_before_factory() -> None:
    events: list[str] = []
    store = FakeEphemeralStore(events)
    with pytest.raises(PermissionError, match="local-synthetic"):
        produce_read_only_evidence(
            evidence_factory=_recording_evidence_factory(events),
            schema_validate=_schema_validator(events),
            semantic_validate=_semantic_validator(events),
            context=_context(),
            temporary_store=store,
            execution_mode="local-synthetic",
            qualifying=True,
        )
    assert events == []
    assert store.value is None


def test_ephemeral_read_only_producer_requires_fake_owner_only_boundaries() -> None:
    for context, store, message in (
        (_context(fake=False), FakeEphemeralStore([]), "fake"),
        (_context(), FakeEphemeralStore([], owner_only=False), "owner-only"),
    ):
        with pytest.raises(PermissionError, match=message):
            produce_read_only_evidence(
                evidence_factory=_evidence,
                schema_validate=lambda _: None,
                semantic_validate=validate_read_only_semantics,
                context=context,
                temporary_store=store,
                execution_mode="local-synthetic",
                qualifying=False,
            )


def test_ephemeral_read_only_producer_deletes_after_schema_or_semantic_failure() -> None:
    for evidence, expected_error, message in (
        ({**_evidence(), "raw_output": "prohibited"}, ValidationError, "Additional properties"),
        ({**_evidence(), "source_state_after_sha256": "f" * 64}, ValueError, "source state"),
    ):
        events: list[str] = []
        store = FakeEphemeralStore(events)
        with pytest.raises(expected_error, match=message):
            produce_read_only_evidence(
                evidence_factory=_copy_factory(evidence),
                schema_validate=_schema_validator(events),
                semantic_validate=_semantic_validator(events),
                context=_context(),
                temporary_store=store,
                execution_mode="local-synthetic",
                qualifying=False,
            )
        assert store.logically_deleted is True
        assert store.value is None
