from __future__ import annotations

import hashlib
import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from typing import Protocol

import rfc8785

READ_ONLY_FIELDS = frozenset(
    {
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
)


@dataclass(frozen=True)
class EvidenceBindingContext:
    execution_mode: str
    audit_sink: str
    sovereign_session_id: str
    preflight_attestation_digest: str
    execution_vm_resource_id: str
    audit_intent_event_id: str
    audit_intent_event_digest: str
    audit_result_intent_event_id: str
    preflight_signature_verified: bool
    live_imds_verified: bool
    live_imds_resource_id: str
    live_imds_location: str
    standalone_vm_verified: bool
    immutable_ledger_verified: bool
    peer_authenticated: bool
    encrypted_temporary_storage: bool
    owner_only_temporary_storage: bool
    fake: bool

    def replaced(self, **changes: object) -> EvidenceBindingContext:
        return replace(self, **changes)  # type: ignore[arg-type]


@dataclass(frozen=True)
class EvidenceValidationResult:
    status: str
    qualifying: bool
    persisted: bool
    details: None = None


@dataclass(frozen=True)
class UsabilityLifecycleContext:
    execution_mode: str
    audit_sink: str
    authorized_au_store: bool
    collect_audited: bool
    finalize_audited: bool
    human_lifecycle_actions_audited: bool
    fake: bool


@dataclass(frozen=True)
class UsabilityValidationResult:
    status: str
    sc_001_count: int
    sc_001_passed: bool
    sc_006_count: int
    sc_006_passed: bool


@dataclass(frozen=True)
class HostedWriteContext:
    target_key: str
    operation: str
    conditional_create: bool
    marker_created_before_write: bool
    audit_action: str


@dataclass(frozen=True)
class HostedLifecycleContext:
    writes: tuple[HostedWriteContext, ...]
    human_review_audited: bool
    human_lifecycle_actions_audited: bool
    fake: bool


class EphemeralEvidenceStore(Protocol):
    owner_only: bool

    def write(self, value: dict[str, object]) -> None: ...

    def logical_delete(self) -> None: ...


def _require_exact_fields(evidence: Mapping[str, object]) -> None:
    if frozenset(evidence) != READ_ONLY_FIELDS:
        raise ValueError("read-only evidence field set is not the exact allowlist")


def _require_equal_pair(evidence: Mapping[str, object], prefix: str, label: str) -> None:
    if evidence[f"{prefix}_before_sha256"] != evidence[f"{prefix}_after_sha256"]:
        raise ValueError(f"{label} digest changed")


def _require_boundaries(context: EvidenceBindingContext) -> None:
    checks = (
        context.preflight_signature_verified,
        context.live_imds_verified,
        context.standalone_vm_verified,
        context.immutable_ledger_verified,
        context.peer_authenticated,
        context.encrypted_temporary_storage,
        context.owner_only_temporary_storage,
    )
    if not all(checks):
        raise ValueError("read-only evidence boundary verification failed")
    if context.live_imds_location not in {"australiaeast", "australiasoutheast"}:
        raise ValueError("live IMDS location is outside the allowed AU regions")
    if context.live_imds_resource_id != context.execution_vm_resource_id:
        raise ValueError("live IMDS resource binding mismatch")
    if context.audit_result_intent_event_id != context.audit_intent_event_id:
        raise ValueError("immutable ledger intent linkage mismatch")


def validate_read_only_semantics(
    evidence: Mapping[str, object], context: EvidenceBindingContext
) -> EvidenceValidationResult:
    if context.execution_mode == "local-synthetic":
        raise PermissionError("local-synthetic cannot produce qualifying read-only evidence")
    if not context.fake:
        raise PermissionError("local validation requires fake read-only evidence boundaries")
    _require_exact_fields(evidence)
    _require_equal_pair(evidence, "source_state", "source state")
    _require_equal_pair(evidence, "protected_state", "protected state")
    _require_equal_pair(evidence, "coverage_state", "coverage state")

    succeeded = evidence["outcome"] == "succeeded"
    if succeeded != (evidence["exit_code"] == 0):
        raise ValueError("read-only evidence outcome and exit code are inconsistent")

    lifecycle_checks = (
        ("peer_authenticated", True, "peer authentication"),
        ("au_vm_verified", True, "AU VM verification"),
        ("encrypted_temporary_storage", True, "encrypted temporary storage"),
        ("audit_transaction_complete", True, "audit transaction completion"),
        ("raw_output_deleted", True, "raw output deletion"),
        ("repository_payload_persisted", False, "repository payload persistence"),
    )
    for field, expected, label in lifecycle_checks:
        if evidence[field] is not expected:
            raise ValueError(f"read-only evidence {label} is invalid")

    _require_boundaries(context)
    bindings = {
        "execution_mode": context.execution_mode,
        "audit_sink": context.audit_sink,
        "sovereign_session_id": context.sovereign_session_id,
        "preflight_attestation_digest": context.preflight_attestation_digest,
        "execution_vm_resource_id": context.execution_vm_resource_id,
        "audit_intent_event_id": context.audit_intent_event_id,
        "audit_intent_event_digest": context.audit_intent_event_digest,
    }
    if any(evidence[field] != expected for field, expected in bindings.items()):
        raise ValueError("read-only evidence sovereign binding mismatch")
    if evidence["execution_vm_resource_id"] != context.live_imds_resource_id:
        raise ValueError("read-only evidence live IMDS binding mismatch")

    return EvidenceValidationResult(status="validated-fake", qualifying=False, persisted=False)


def validate_performance_semantics(
    evidence: Mapping[str, object], context: EvidenceBindingContext
) -> EvidenceValidationResult:
    if not context.fake:
        raise PermissionError("local validation requires fake performance evidence boundaries")
    _require_boundaries(context)
    if evidence["fixture_count"] != 100:
        raise ValueError("performance fixture count must equal 100")
    warmups = evidence["warmup_outcomes"]
    if not isinstance(warmups, list) or len(warmups) != 3:
        raise ValueError("performance evidence requires exactly 3 warmup outcomes")
    durations = evidence["durations_seconds"]
    if not isinstance(durations, list) or len(durations) != 30:
        raise ValueError("performance evidence requires exactly 30 durations")
    if evidence["rank"] != 29:
        raise ValueError("performance evidence requires nearest rank 29")
    computed_p95 = sorted(float(duration) for duration in durations)[28]
    if evidence["p95_seconds"] != computed_p95:
        raise ValueError("performance evidence P95 does not match rank 29")
    if evidence["threshold_seconds"] != 2.0:
        raise ValueError("performance evidence threshold must equal 2.000 seconds")
    if evidence["passed"] is not (computed_p95 <= 2.0):
        raise ValueError("performance evidence passed value is inconsistent")
    if evidence["network_disabled"] is not True:
        raise ValueError("performance evidence network must be disabled")

    bindings = {
        "execution_mode": context.execution_mode,
        "audit_sink": context.audit_sink,
        "sovereign_session_id": context.sovereign_session_id,
        "preflight_attestation_digest": context.preflight_attestation_digest,
        "execution_vm_resource_id": context.execution_vm_resource_id,
        "audit_intent_event_id": context.audit_intent_event_id,
        "audit_intent_event_digest": context.audit_intent_event_digest,
    }
    if any(evidence[field] != expected for field, expected in bindings.items()):
        raise ValueError("performance evidence sovereign binding mismatch")
    if evidence["execution_vm_resource_id"] != context.live_imds_resource_id:
        raise ValueError("performance evidence live IMDS binding mismatch")

    return EvidenceValidationResult(status="validated-fake", qualifying=False, persisted=False)


def _mapping(value: object, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError(f"usability {label} must be an object")
    return value


def _list(value: object, label: str) -> list[object]:
    if not isinstance(value, list):
        raise ValueError(f"usability {label} must be an array")
    return value


def _timestamp(value: object, label: str) -> datetime:
    if not isinstance(value, str):
        raise ValueError(f"usability {label} must be an RFC 3339 timestamp")
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError(f"usability {label} must be an RFC 3339 timestamp") from error


def _reject_prohibited_fields(value: object) -> None:
    prohibited = {
        "name",
        "participant_name",
        "reviewer_name",
        "email",
        "email_address",
        "employer",
        "precise_location",
        "medical_detail",
        "medical_details",
        "note",
        "notes",
        "free_text",
        "free_text_notes",
    }
    if isinstance(value, Mapping):
        for key, child in value.items():
            normalized = str(key).casefold()
            if normalized in prohibited:
                raise ValueError("usability evidence contains a prohibited identity or free-text field")
            _reject_prohibited_fields(child)
    elif isinstance(value, list):
        for child in value:
            _reject_prohibited_fields(child)


def _require_usability_lifecycle(context: UsabilityLifecycleContext) -> None:
    if context.execution_mode != "sovereign":
        raise PermissionError("usability lifecycle requires sovereign external execution")
    if context.audit_sink != "immutable-au":
        raise ValueError("usability lifecycle requires an immutable AU audit sink")
    if not all(
        (
            context.authorized_au_store,
            context.collect_audited,
            context.finalize_audited,
            context.human_lifecycle_actions_audited,
        )
    ):
        raise ValueError("usability lifecycle requires audited external collect, finalize, and human actions")


def validate_usability_semantics(
    evidence: Mapping[str, object], context: UsabilityLifecycleContext
) -> UsabilityValidationResult:
    _require_usability_lifecycle(context)
    _reject_prohibited_fields(evidence)

    privacy = _mapping(evidence.get("privacy"), "privacy")
    required_privacy = (
        "consent_recorded_for_all_included_and_excluded",
        "no_direct_identifiers",
        "reidentification_key_separated",
        "recruitment_records_separated",
        "least_privilege_named_study_team_access",
        "immutable_access_audit",
        "encrypted_in_transit",
        "encrypted_at_rest",
        "withdrawal_process_confirmed",
        "breach_response_process_confirmed",
        "verified_deletion_required",
    )
    if any(privacy.get(field) is not True for field in required_privacy):
        raise ValueError("usability privacy controls are incomplete")
    reviewed_at = _timestamp(privacy.get("reviewed_at"), "privacy review")
    delete_by = _timestamp(privacy.get("retention_delete_by"), "retention deadline")
    if delete_by < reviewed_at:
        raise ValueError("usability retention deadline precedes review")
    if privacy.get("legal_hold_approved") is not True and delete_by - reviewed_at > timedelta(days=90):
        raise ValueError("usability retention exceeds 90 days without an approved legal hold")

    participants = _mapping(evidence.get("participants"), "participants")
    strata: dict[str, list[Mapping[str, object]]] = {}
    included_by_id: dict[str, tuple[str, Mapping[str, object]]] = {}
    sc_001_count = 0
    sc_006_count = 0
    for stratum in ("novice", "experienced"):
        raw_members = _list(participants.get(stratum), f"{stratum} participants")
        if len(raw_members) != 10:
            raise ValueError("usability cohort requires exactly 10 participants per stratum")
        members = [_mapping(member, f"{stratum} participant") for member in raw_members]
        strata[stratum] = members
        for member in members:
            participant_id = member.get("participant_id")
            if not isinstance(participant_id, str) or participant_id in included_by_id:
                raise ValueError("usability participant identifiers must be unique")
            included_by_id[participant_id] = (stratum, member)
            if not (
                member.get("is_adult") is True
                and member.get("uses_cli_monthly") is True
                and member.get("prior_feature_exposure") is False
            ):
                raise ValueError("usability participant eligibility is invalid")
            workflows = member.get("spec_kit_workflows_last_6_months")
            if not isinstance(workflows, int) or isinstance(workflows, bool):
                raise ValueError("usability participant eligibility workflow count is invalid")
            experienced = member.get("used_extension_management") is True
            if stratum == "novice" and not (0 <= workflows <= 2 and not experienced):
                raise ValueError("usability novice eligibility is invalid")
            if stratum == "experienced" and not (workflows >= 5 and experienced):
                raise ValueError("usability experienced eligibility is invalid")
            requested = _list(member.get("requested_accommodations"), "requested accommodations")
            provided = _list(member.get("provided_accommodations"), "provided accommodations")
            if set(requested) != set(provided):
                raise ValueError("usability requested accommodation was not provided")

            elapsed = member.get("elapsed_seconds")
            if not isinstance(elapsed, (int, float)) or isinstance(elapsed, bool):
                raise ValueError("usability elapsed time is invalid")
            sc_001_success = (
                member.get("installed_answer_correct") is True
                and member.get("enabled_answer_correct") is True
                and elapsed <= 30
            )
            if member.get("sc_001_success") is not sc_001_success:
                raise ValueError("usability SC-001 result is inconsistent")
            sc_001_count += int(sc_001_success)

            rating = member.get("sc_006_clarity_rating")
            sc_006_clear = (
                isinstance(rating, int)
                and not isinstance(rating, bool)
                and rating >= 4
                and member.get("consulted_installation_directories") is False
                and member.get("attempted_extension_command") is False
            )
            if member.get("sc_006_clear") is not sc_006_clear:
                raise ValueError("usability SC-006 result is inconsistent")
            sc_006_count += int(sc_006_clear)

    if len(included_by_id) != 20:
        raise ValueError("usability cohort requires exactly 20 unique participants")

    seed = evidence.get("allocation_seed")
    variants = _list(evidence.get("task_variants"), "task variants")
    if not isinstance(seed, str) or not variants:
        raise ValueError("usability allocation configuration is invalid")
    expected_allocations: dict[str, tuple[str, int, object]] = {}
    for stratum, members in strata.items():
        ordered_ids = sorted(str(member["participant_id"]) for member in members)
        ordered_ids.sort(
            key=lambda participant_id: (
                hashlib.sha256(f"{seed}:{stratum}:{participant_id}".encode()).hexdigest(),
                participant_id,
            )
        )
        for position, participant_id in enumerate(ordered_ids, start=1):
            variant = variants[(position - 1) % len(variants)]
            expected_allocations[participant_id] = (stratum, position, variant)
            member = included_by_id[participant_id][1]
            if member.get("task_variant") != variant:
                raise ValueError("usability participant task allocation is inconsistent")

    allocation_records = _list(evidence.get("allocation_records"), "allocation records")
    if len(allocation_records) != len(expected_allocations):
        raise ValueError("usability allocation cardinality is invalid")
    observed_allocations: set[str] = set()
    for raw_record in allocation_records:
        record = _mapping(raw_record, "allocation record")
        participant_id = record.get("participant_id")
        if not isinstance(participant_id, str) or participant_id in observed_allocations:
            raise ValueError("usability allocation participant is missing or duplicated")
        observed_allocations.add(participant_id)
        expected = expected_allocations.get(participant_id)
        if (
            expected is None
            or (
                record.get("experience_stratum"),
                record.get("allocation_position"),
                record.get("task_variant"),
            )
            != expected
        ):
            raise ValueError("usability allocation does not match deterministic recomputation")

    excluded_ids: set[str] = set()
    for raw_excluded in _list(evidence.get("excluded_participants"), "excluded participants"):
        excluded = _mapping(raw_excluded, "excluded participant")
        participant_id = excluded.get("participant_id")
        if not isinstance(participant_id, str) or participant_id in included_by_id or participant_id in excluded_ids:
            raise ValueError("usability exclusion participant is included or duplicated")
        excluded_ids.add(participant_id)
        excluded_stratum = excluded.get("experience_stratum")
        replacement_id = excluded.get("replacement_participant_id")
        replacement = included_by_id.get(str(replacement_id))
        if replacement_id == participant_id or replacement is None or replacement[0] != excluded_stratum:
            raise ValueError("usability replacement must be distinct, included, and in the same stratum")
        unavailable = _list(excluded.get("unavailable_accommodations"), "unavailable accommodations")
        reason = excluded.get("exclusion_reason")
        if excluded.get("excluded_before_task_exposure") is not True:
            raise ValueError("usability exclusion must occur before task exposure")
        if reason == "required-accommodation-unavailable" and not unavailable:
            raise ValueError("usability accommodation exclusion requires a closed unavailable category")
        if reason == "documented-technical-interruption" and unavailable:
            raise ValueError("usability technical exclusion cannot contain accommodation categories")
        if reason not in {"required-accommodation-unavailable", "documented-technical-interruption"}:
            raise ValueError("usability exclusion reason is invalid")

    aggregates = _mapping(evidence.get("aggregates"), "aggregates")
    if (
        aggregates.get("included_participant_count") != 20
        or aggregates.get("sc_001_success_count") != sc_001_count
        or aggregates.get("sc_006_clear_count") != sc_006_count
    ):
        raise ValueError("usability aggregate values do not match participant records")

    review = _mapping(evidence.get("review"), "review")
    decision = review.get("decision")
    expected_reason = (
        {"approved": "study-verified", "rejected": "study-rejected"}.get(decision)
        if isinstance(decision, str)
        else None
    )
    if expected_reason is None or review.get("decision_reason_code") != expected_reason:
        raise ValueError("usability review decision and reason are inconsistent")

    return UsabilityValidationResult(
        status="validated-fake" if context.fake else "validated",
        sc_001_count=sc_001_count,
        sc_001_passed=sc_001_count >= 19,
        sc_006_count=sc_006_count,
        sc_006_passed=sc_006_count >= 18,
    )


def _validate_platform_digest(record: Mapping[str, object]) -> None:
    observed = record.get("evidence_digest")
    unsigned = {key: value for key, value in record.items() if key != "evidence_digest"}
    expected = hashlib.sha256(rfc8785.dumps(unsigned)).hexdigest()  # type: ignore[arg-type]
    if observed != expected:
        raise ValueError("hosted platform record digest is invalid")


def _validate_hosted_boundary(
    boundary: Mapping[str, object], *, session_id: object, operation: str, target_key: str
) -> tuple[str, str, str]:
    if boundary.get("write_operation") != operation:
        raise ValueError("hosted write operation does not match lifecycle operation")
    retention_days = boundary.get("immutability_retention_days")
    if (
        boundary.get("immutability_policy_mode") != "Locked"
        or not isinstance(retention_days, int)
        or isinstance(retention_days, bool)
        or retention_days < 1
    ):
        raise ValueError("hosted immutability policy is invalid")
    if boundary.get("replay_marker_created") is not True:
        raise ValueError("hosted replay marker was not created")
    marker_created = _timestamp(boundary.get("replay_marker_created_at"), "hosted marker creation")
    marker_retained = _timestamp(boundary.get("replay_marker_retain_until"), "hosted marker retention")
    if marker_retained - marker_created < timedelta(days=1):
        raise ValueError("hosted replay marker retention is too short")

    attestation = _mapping(boundary.get("attestation"), "hosted attestation")
    jti = attestation.get("jti")
    nonce = attestation.get("nonce")
    compact_jws = attestation.get("compact_jws")
    if not all(isinstance(value, str) for value in (jti, nonce, compact_jws)):
        raise ValueError("hosted attestation identity values are invalid")
    assert isinstance(jti, str) and isinstance(nonce, str) and isinstance(compact_jws, str)
    marker_name = boundary.get("replay_marker_blob_name")
    marker_uri = boundary.get("replay_marker_blob_uri")
    if marker_name != f"spec001-extension-list/attestation-jti/{jti}":
        raise ValueError("hosted replay marker name does not match attestation JTI")
    if not isinstance(marker_uri, str) or not marker_uri.endswith(f"/{marker_name}"):
        raise ValueError("hosted replay marker URI does not match attestation JTI")
    if attestation.get("attestation_digest") != hashlib.sha256(compact_jws.encode()).hexdigest():
        raise ValueError("hosted attestation digest is invalid")
    if (
        attestation.get("operation") != operation
        or attestation.get("target_blob_name") != target_key
        or attestation.get("validation_session_id") != session_id
    ):
        raise ValueError("hosted attestation operation or target binding is invalid")
    repeated_claims = (
        "managed_identity_principal_id",
        "role_definition_id",
        "storage_account_resource_id",
        "private_endpoint_connection_resource_id",
        "container_scope",
        "no_broader_data_plane_write_role",
    )
    if any(attestation.get(field) != boundary.get(field) for field in repeated_claims):
        raise ValueError("hosted attestation repeated claims do not match the storage boundary")
    reviewer_identifier = attestation.get("reviewer_identifier")
    if not isinstance(reviewer_identifier, str) or re.fullmatch(r"reviewer-[0-9a-f]{16}", reviewer_identifier) is None:
        raise ValueError("hosted attestation reviewer is not pseudonymous")
    return jti, nonce, compact_jws


def validate_hosted_platform_semantics(
    fragments: Mapping[str, Mapping[str, object]],
    document: Mapping[str, object],
    lifecycle: HostedLifecycleContext,
) -> EvidenceValidationResult:
    if len(fragments) != 2:
        raise ValueError("hosted fragment cardinality must be exactly two")
    session_id = document.get("validation_session_id")
    fragment_records: dict[str, Mapping[str, object]] = {}
    agreement_values: set[bytes] = set()
    attestation_values: list[tuple[str, str, str]] = []
    expected_targets: dict[str, str] = {}

    for key, fragment in fragments.items():
        if fragment.get("validation_session_id") != session_id:
            raise ValueError("hosted fragments do not share the final validation session")
        record = _mapping(fragment.get("record"), "hosted fragment record")
        _validate_platform_digest(record)
        operating_system = record.get("os")
        vm_id = record.get("vm_id")
        if operating_system not in {"windows", "ubuntu"} or not isinstance(vm_id, str):
            raise ValueError("hosted fragment OS cardinality is invalid")
        expected_key = f"spec001-extension-list/{session_id}/fragments/{operating_system}-{vm_id}.json"
        if key != expected_key:
            raise ValueError("hosted fragment key does not match OS and VM identity")
        if str(operating_system) in fragment_records:
            raise ValueError("hosted fragment OS cardinality is invalid")
        fragment_records[str(operating_system)] = record
        agreement_values.add(
            rfc8785.dumps(
                {
                    "package": record.get("package"),  # type: ignore[dict-item]
                    "lock": record.get("lock"),  # type: ignore[dict-item]
                    "script_version": record.get("script_version"),  # type: ignore[dict-item]
                }
            )
        )
        boundary = _mapping(fragment.get("storage_boundary"), "hosted fragment storage boundary")
        attestation_values.append(
            _validate_hosted_boundary(
                boundary,
                session_id=session_id,
                operation="collect-fragment",
                target_key=key,
            )
        )
        expected_targets[key] = "collect-fragment"

    if set(fragment_records) != {"windows", "ubuntu"}:
        raise ValueError("hosted fragment OS cardinality must be one Windows and one Ubuntu")
    if len(agreement_values) != 1:
        raise ValueError("hosted fragment package, lock, and script agreement is invalid")

    final_records = _list(document.get("records"), "hosted final records")
    if len(final_records) != 2:
        raise ValueError("hosted final record cardinality must be exactly two")
    final_by_os: dict[str, Mapping[str, object]] = {}
    for raw_record in final_records:
        record = _mapping(raw_record, "hosted final record")
        _validate_platform_digest(record)
        operating_system = record.get("os")
        if not isinstance(operating_system, str) or operating_system in final_by_os:
            raise ValueError("hosted final OS cardinality is invalid")
        final_by_os[operating_system] = record
    if set(final_by_os) != {"windows", "ubuntu"}:
        raise ValueError("hosted final OS cardinality must be one Windows and one Ubuntu")
    if any(final_by_os[operating_system] != fragment_records[operating_system] for operating_system in final_by_os):
        raise ValueError("hosted final records do not agree with collected fragments")

    final_key = f"spec001-extension-list/{session_id}/final/platform-evidence.json"
    final_boundary = _mapping(document.get("storage_boundary"), "hosted final storage boundary")
    attestation_values.append(
        _validate_hosted_boundary(
            final_boundary,
            session_id=session_id,
            operation="finalize-canonical",
            target_key=final_key,
        )
    )
    expected_targets[final_key] = "finalize-canonical"

    for index, label in enumerate(("JTI", "nonce", "JWS")):
        if len({values[index] for values in attestation_values}) != len(attestation_values):
            raise ValueError(f"hosted attestations require distinct {label} values")

    review = _mapping(document.get("review"), "hosted review")
    if set(review) != {
        "reviewer_identifier",
        "reviewer_role",
        "reviewed_at",
        "decision",
        "decision_reason_code",
    }:
        raise ValueError("hosted review must be closed and contain no name or free text")
    reviewer_identifier = review.get("reviewer_identifier")
    if not isinstance(reviewer_identifier, str) or re.fullmatch(r"reviewer-[0-9a-f]{16}", reviewer_identifier) is None:
        raise ValueError("hosted review reviewer_identifier is not pseudonymous")
    decision = review.get("decision")
    expected_reason = (
        {"approved": "evidence-verified", "rejected": "evidence-rejected"}.get(decision)
        if isinstance(decision, str)
        else None
    )
    if expected_reason is None or review.get("decision_reason_code") != expected_reason:
        raise ValueError("hosted review decision and reason are inconsistent")

    if not lifecycle.human_review_audited or not lifecycle.human_lifecycle_actions_audited:
        raise ValueError("hosted human review and lifecycle actions must be audited")
    if len(lifecycle.writes) != len(expected_targets):
        raise ValueError("hosted audited write cardinality is invalid")
    observed_targets: set[str] = set()
    for write in lifecycle.writes:
        expected_operation = expected_targets.get(write.target_key)
        if expected_operation is None or write.target_key in observed_targets:
            raise ValueError("hosted audited write target is invalid or duplicated")
        observed_targets.add(write.target_key)
        expected_audit = "external.collect" if expected_operation == "collect-fragment" else "external.finalize"
        if write.operation != expected_operation or write.audit_action != expected_audit:
            raise ValueError("hosted collect or finalize audit action is invalid")
        if not write.conditional_create:
            raise ValueError("hosted writes require conditional creation")
        if not write.marker_created_before_write:
            raise ValueError("hosted replay marker must be created before each write")
    if lifecycle.writes[-1].target_key != final_key:
        raise ValueError("hosted finalization write must follow fragment writes")

    return EvidenceValidationResult(
        status="validated-fake" if lifecycle.fake else "validated",
        qualifying=False,
        persisted=False,
    )


def produce_read_only_evidence(
    *,
    evidence_factory: Callable[[], dict[str, object]],
    schema_validate: Callable[[dict[str, object]], None],
    semantic_validate: Callable[[dict[str, object], EvidenceBindingContext], EvidenceValidationResult],
    context: EvidenceBindingContext,
    temporary_store: EphemeralEvidenceStore,
    execution_mode: str,
    qualifying: bool,
) -> EvidenceValidationResult:
    if qualifying and execution_mode != "sovereign":
        raise PermissionError("local-synthetic cannot produce qualifying read-only evidence")
    if context.fake is not True:
        raise PermissionError("local read-only producer tests require fake boundaries")
    if temporary_store.owner_only is not True or context.owner_only_temporary_storage is not True:
        raise PermissionError("read-only producer requires owner-only temporary storage")
    if qualifying:
        raise PermissionError("fake boundaries cannot produce qualifying read-only evidence")

    evidence = evidence_factory()
    temporary_store.write(evidence)
    try:
        schema_validate(evidence)
        semantic_result = semantic_validate(evidence, context)
        if semantic_result.qualifying or semantic_result.persisted:
            raise ValueError("fake read-only semantic validation cannot qualify or persist")
        return EvidenceValidationResult(status="passed-fake", qualifying=False, persisted=False)
    finally:
        temporary_store.logical_delete()
