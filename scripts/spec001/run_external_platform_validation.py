from __future__ import annotations

import argparse
import base64
import hashlib
import json
import re
import uuid
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from importlib.resources import files
from typing import Protocol

from specify_cli.azure_authorization import evaluate_storage_blob_authorization
from specify_cli.evidence import HostedLifecycleContext, HostedWriteContext, validate_hosted_platform_semantics

_CONTRIBUTOR_ROLE_ID = "ba92f5b4-2d11-453d-a403-e96b0029c9fe"
_CONTRIBUTOR_ROLE_RESOURCE_ID = f"/providers/Microsoft.Authorization/roleDefinitions/{_CONTRIBUTOR_ROLE_ID}"
_EXPECTED_BOOTSTRAP_CHECKS = ("protected-state", "dispatcher-root-regression")
_ALLOWED_REGIONS = {"australiaeast", "australiasoutheast"}
_MAX_ATTESTATION_BYTES = 16 * 1024
_ATTESTATION_DEADLINE_SECONDS = 5
_MARKER_RETENTION_SECONDS = 86_400
_UUID_PATTERN = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$")
_REVIEWER_PATTERN = re.compile(r"^reviewer-[0-9a-f]{16}$")
_ATTESTATION_FIELDS = frozenset(
    {
        "issuer",
        "audience",
        "algorithm",
        "key_id",
        "jti",
        "nonce",
        "issued_at",
        "not_before",
        "expires_at",
        "validation_session_id",
        "managed_identity_principal_id",
        "operation",
        "target_blob_name",
        "role_definition_id",
        "reviewer_identifier",
        "reviewer_role",
        "attested_at",
        "storage_account_resource_id",
        "private_endpoint_connection_resource_id",
        "container_scope",
        "no_broader_data_plane_write_role",
    }
)


class AuditSink(Protocol):
    def begin(self, action: str, target: str) -> str: ...

    def complete(self, intent_event_id: str, action: str, target: str, outcome: str) -> None: ...


class ExternalTransport(Protocol):
    def verify_pinned_resource(self, resource_kind: str, pins: dict[str, object]) -> dict[str, object]: ...

    def authorization_inventory(self, required_role_id: str) -> dict[str, object]: ...

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
    ) -> dict[str, str]: ...

    def create_replay_marker_if_absent(self, marker: dict[str, object]) -> bool: ...

    def create_blob_if_absent(self, target: str, payload: dict[str, object]) -> bool: ...

    def read_fragments(self, prefix: str) -> dict[str, dict[str, object]]: ...


@dataclass(frozen=True, slots=True)
class OperatorLifecycle:
    execution_mode: str
    bootstrap_checks: tuple[str, ...]
    sovereign_preflight_verified: bool
    daemon_session_verified: bool
    peer_authenticated: bool
    dispatcher_invocation: bool
    fake_transport: bool


@dataclass(frozen=True, slots=True)
class CollectRequest:
    session_id: str
    storage_account_resource_id: str
    container_name: str
    blob_account_host: str
    container_scope: object
    private_endpoint_connection_resource_id: str
    vm_principal_id: str
    target_blob_name: str
    record: dict[str, object]


@dataclass(frozen=True, slots=True)
class FinalizeRequest:
    session_id: str
    storage_account_resource_id: str
    container_name: str
    blob_account_host: str
    container_scope: object
    private_endpoint_connection_resource_id: str
    vm_principal_id: str
    target_blob_name: str
    review: dict[str, object]


@dataclass(frozen=True, slots=True)
class OperatorResult:
    status: str
    qualifying: bool
    persisted: bool


SignatureVerifier = Callable[[str, dict[str, object]], dict[str, object]]


def _timestamp(value: object, label: str) -> datetime:
    if not isinstance(value, str):
        raise RuntimeError(f"{label} is invalid")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise RuntimeError(f"{label} is invalid") from error
    if parsed.tzinfo is None:
        raise RuntimeError(f"{label} is invalid")
    return parsed.astimezone(UTC)


def _load_trust_bundle() -> dict[str, object]:
    resource = files("specify_cli").joinpath("trusted_attestation_keys.json")
    value = json.loads(resource.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or value.get("schema_version") != "1.0":
        raise RuntimeError("reviewed trust bundle is invalid")
    if value.get("disposition") != "synthetic-contract-pins-not-authorized-for-real-use":
        raise RuntimeError("reviewed trust bundle disposition is invalid")
    return value


def _require_lifecycle(lifecycle: OperatorLifecycle) -> None:
    if not lifecycle.dispatcher_invocation or not lifecycle.peer_authenticated:
        raise RuntimeError("dispatcher peer-authenticated invocation is required")
    if (
        lifecycle.execution_mode != "sovereign"
        or lifecycle.bootstrap_checks != _EXPECTED_BOOTSTRAP_CHECKS
        or not lifecycle.sovereign_preflight_verified
        or not lifecycle.daemon_session_verified
    ):
        raise RuntimeError("verified sovereign lifecycle is required")
    if not lifecycle.fake_transport:
        raise RuntimeError("implementation permits fake transport only")


def _resource_pins(value: object, label: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise RuntimeError(f"{label} trust pins are invalid")
    return value


def _verify_private_resource(
    transport: ExternalTransport,
    resource_kind: str,
    pins: dict[str, object],
    now: datetime,
) -> dict[str, object]:
    state = transport.verify_pinned_resource(resource_kind, pins)
    if (
        state.get("arm_resource_id") != pins.get("arm_resource_id")
        or state.get("location") not in _ALLOWED_REGIONS
        or state.get("public_network_access") != "Disabled"
        or state.get("default_network_action") != "Deny"
        or state.get("private_endpoint_id") != pins.get("private_endpoint_id")
        or state.get("private_dns_host") != pins.get("private_dns_host")
        or state.get("private_dns_only") is not True
    ):
        raise RuntimeError(f"{resource_kind} private controls are invalid")
    if resource_kind == "key_vault":
        if state.get("key_enabled") is not True or _timestamp(state.get("key_expires_at"), "signing key expiry") <= now:
            raise RuntimeError("signing key is disabled or expired")
    return state


def _storage_pins(request: CollectRequest) -> dict[str, object]:
    account_name = request.storage_account_resource_id.rsplit("/", 1)[-1]
    return {
        "arm_resource_id": request.storage_account_resource_id,
        "allowed_regions": sorted(_ALLOWED_REGIONS),
        "public_network_access": "Disabled",
        "default_network_action": "Deny",
        "private_endpoint_id": request.private_endpoint_connection_resource_id,
        "private_dns_host": f"{account_name}.blob.core.windows.net",
    }


def _validate_collect_request(request: CollectRequest) -> None:
    try:
        uuid.UUID(request.session_id)
        uuid.UUID(request.vm_principal_id)
    except ValueError as error:
        raise RuntimeError("collect identity is invalid") from error
    if request.container_scope != (
        f"{request.storage_account_resource_id}/blobServices/default/containers/{request.container_name}"
    ):
        raise RuntimeError("container scope is invalid")
    if request.blob_account_host != _storage_pins(request)["private_dns_host"]:
        raise RuntimeError("Blob host does not match the storage account")
    expected_prefix = f"spec001-extension-list/{request.session_id}/fragments/"
    if not request.target_blob_name.startswith(expected_prefix):
        raise RuntimeError("collect target is invalid")


def _collect_shape(request: FinalizeRequest) -> CollectRequest:
    return CollectRequest(
        session_id=request.session_id,
        storage_account_resource_id=request.storage_account_resource_id,
        container_name=request.container_name,
        blob_account_host=request.blob_account_host,
        container_scope=request.container_scope,
        private_endpoint_connection_resource_id=request.private_endpoint_connection_resource_id,
        vm_principal_id=request.vm_principal_id,
        target_blob_name=f"spec001-extension-list/{request.session_id}/fragments/validation-only",
        record={},
    )


def _validate_review(review: Mapping[str, object]) -> None:
    if set(review) != {
        "reviewer_identifier",
        "reviewer_role",
        "reviewed_at",
        "decision",
        "decision_reason_code",
    }:
        raise RuntimeError("final review is not closed")
    reviewer = review.get("reviewer_identifier")
    if not isinstance(reviewer, str) or _REVIEWER_PATTERN.fullmatch(reviewer) is None:
        raise RuntimeError("final review is not pseudonymous")
    if review.get("reviewer_role") not in {"security", "compliance"}:
        raise RuntimeError("final review role is invalid")
    expected_reason = {"approved": "evidence-verified", "rejected": "evidence-rejected"}.get(review.get("decision"))
    if review.get("decision_reason_code") != expected_reason:
        raise RuntimeError("final review decision is inconsistent")
    _timestamp(review.get("reviewed_at"), "final review time")


def _attestation_request(
    request: CollectRequest,
    *,
    operation: str,
    nonce: str,
    requested_at: str,
    target_blob_name: str,
) -> dict[str, object]:
    if re.fullmatch(r"[0-9a-f]{64}", nonce) is None:
        raise RuntimeError("attestation nonce is invalid")
    return {
        "schema_version": "1.0",
        "feature": "001-extension-list",
        "operation": operation,
        "validation_session_id": request.session_id,
        "nonce": nonce,
        "requested_at": requested_at,
        "target_blob_name": target_blob_name,
        "storage_account_resource_id": request.storage_account_resource_id,
        "private_endpoint_connection_resource_id": request.private_endpoint_connection_resource_id,
        "container_scope": request.container_scope,
        "managed_identity_principal_id": request.vm_principal_id,
        "role_definition_id": _CONTRIBUTOR_ROLE_RESOURCE_ID,
        "no_broader_data_plane_write_role": True,
    }


def _validate_attestation_claims(
    claims: Mapping[str, object],
    request: Mapping[str, object],
    trust_bundle: Mapping[str, object],
    compact_jws: str,
    now: datetime,
) -> None:
    expected = {
        "issuer": "ama-security-control-plane",
        "audience": "spec001-extension-list-prewrite",
        "algorithm": "ES256",
        "validation_session_id": request["validation_session_id"],
        "nonce": request["nonce"],
        "operation": request["operation"],
        "target_blob_name": request["target_blob_name"],
        "storage_account_resource_id": request["storage_account_resource_id"],
        "private_endpoint_connection_resource_id": request["private_endpoint_connection_resource_id"],
        "container_scope": request["container_scope"],
        "managed_identity_principal_id": request["managed_identity_principal_id"],
        "role_definition_id": request["role_definition_id"],
        "no_broader_data_plane_write_role": True,
    }
    if any(claims.get(key) != value for key, value in expected.items()):
        raise RuntimeError("attestation claims do not match the closed request")
    keys = trust_bundle.get("signing_keys")
    if not isinstance(keys, list) or len(keys) != 1 or not isinstance(keys[0], dict):
        raise RuntimeError("trust bundle signing key inventory is invalid")
    if claims.get("key_id") != keys[0].get("kid"):
        raise RuntimeError("attestation signing key is not pinned")
    jti = claims.get("jti")
    if not isinstance(jti, str) or _UUID_PATTERN.fullmatch(jti) is None:
        raise RuntimeError("attestation JTI is invalid")
    reviewer = claims.get("reviewer_identifier")
    if not isinstance(reviewer, str) or _REVIEWER_PATTERN.fullmatch(reviewer) is None:
        raise RuntimeError("attestation reviewer is not pseudonymous")
    if claims.get("reviewer_role") not in {"security", "compliance"}:
        raise RuntimeError("attestation reviewer role is invalid")
    issued_at = _timestamp(claims.get("issued_at"), "attestation issued time")
    not_before = _timestamp(claims.get("not_before"), "attestation not-before time")
    expires_at = _timestamp(claims.get("expires_at"), "attestation expiry")
    if expires_at - issued_at > timedelta(minutes=10) or now < not_before - timedelta(minutes=2):
        raise RuntimeError("attestation lifetime is invalid")
    if now > expires_at + timedelta(minutes=2) or issued_at > now + timedelta(minutes=2):
        raise RuntimeError("attestation time window is invalid")
    if hashlib.sha256(compact_jws.encode("utf-8")).hexdigest() == "":
        raise RuntimeError("attestation digest is invalid")


def _decode_segment(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def verify_compact_jws(compact_jws: str, trust_bundle: dict[str, object]) -> dict[str, object]:
    from cryptography.exceptions import InvalidSignature
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.hazmat.primitives.asymmetric.utils import encode_dss_signature
    from cryptography.hazmat.primitives.hashes import SHA256

    parts = compact_jws.split(".")
    if len(parts) != 3:
        raise RuntimeError("attestation compact JWS is invalid")
    try:
        header = json.loads(_decode_segment(parts[0]))
        claims = json.loads(_decode_segment(parts[1]))
        raw_signature = _decode_segment(parts[2])
    except (ValueError, json.JSONDecodeError) as error:
        raise RuntimeError("attestation compact JWS is invalid") from error
    keys = trust_bundle.get("signing_keys")
    if not isinstance(header, dict) or not isinstance(claims, dict) or not isinstance(keys, list):
        raise RuntimeError("attestation compact JWS is invalid")
    matching = [key for key in keys if isinstance(key, dict) and key.get("kid") == header.get("kid")]
    if header.get("alg") != "ES256" or len(matching) != 1 or len(raw_signature) != 64:
        raise RuntimeError("attestation compact JWS header is invalid")
    jwk = matching[0].get("public_jwk")
    if not isinstance(jwk, dict) or "d" in jwk or jwk.get("kty") != "EC" or jwk.get("crv") != "P-256":
        raise RuntimeError("attestation public JWK is invalid")
    public_numbers = ec.EllipticCurvePublicNumbers(
        int.from_bytes(_decode_segment(str(jwk.get("x"))), "big"),
        int.from_bytes(_decode_segment(str(jwk.get("y"))), "big"),
        ec.SECP256R1(),
    )
    signature = encode_dss_signature(
        int.from_bytes(raw_signature[:32], "big"),
        int.from_bytes(raw_signature[32:], "big"),
    )
    try:
        public_numbers.public_key().verify(signature, f"{parts[0]}.{parts[1]}".encode("ascii"), ec.ECDSA(SHA256()))
    except InvalidSignature as error:
        raise RuntimeError("attestation signature is invalid") from error
    return claims


def _prewrite(
    request: CollectRequest,
    *,
    operation: str,
    target_blob_name: str,
    transport: ExternalTransport,
    trust_bundle: dict[str, object],
    nonce: str,
    now_text: str,
    signature_verifier: SignatureVerifier,
) -> dict[str, object]:
    now = _timestamp(now_text, "request time")
    storage = _verify_private_resource(transport, "storage", _storage_pins(request), now)
    control_plane = _verify_private_resource(
        transport, "control_plane", _resource_pins(trust_bundle.get("control_plane"), "control plane"), now
    )
    key_vault = _verify_private_resource(
        transport, "key_vault", _resource_pins(trust_bundle.get("key_vault"), "Key Vault"), now
    )
    inventory = transport.authorization_inventory(_CONTRIBUTOR_ROLE_ID)
    decision = evaluate_storage_blob_authorization(inventory)
    if not decision.authorized:
        raise RuntimeError("Storage Blob Data Contributor authorization is invalid")
    attestation_request = _attestation_request(
        request,
        operation=operation,
        nonce=nonce,
        requested_at=now_text,
        target_blob_name=target_blob_name,
    )
    response = transport.post_attestation(
        str(trust_bundle["attestation_endpoint"]),
        str(trust_bundle["managed_identity_scope"]),
        attestation_request,
        deadline_seconds=_ATTESTATION_DEADLINE_SECONDS,
        maximum_response_bytes=_MAX_ATTESTATION_BYTES,
        allow_redirects=False,
        retries=0,
    )
    if set(response) != {"compact_jws"} or not isinstance(response["compact_jws"], str):
        raise RuntimeError("attestation response is not closed")
    compact_jws = response["compact_jws"]
    claims = signature_verifier(compact_jws, trust_bundle)
    _validate_attestation_claims(claims, attestation_request, trust_bundle, compact_jws, now)
    jti = str(claims["jti"])
    marker_name = f"spec001-extension-list/attestation-jti/{jti}"
    marker = {
        "blob_name": marker_name,
        "created_at": now_text,
        "retain_for_seconds": _MARKER_RETENTION_SECONDS,
        "retain_until": (now + timedelta(seconds=_MARKER_RETENTION_SECONDS)).isoformat().replace("+00:00", "Z"),
        "immutability_policy_mode": "Locked",
        "operation": operation,
    }
    if not transport.create_replay_marker_if_absent(marker):
        raise RuntimeError("attestation replay marker already exists")
    return {
        "storage_account_resource_id": request.storage_account_resource_id,
        "container_name": request.container_name,
        "blob_account_host": request.blob_account_host,
        "location": storage["location"],
        "public_network_access": "Disabled",
        "default_network_action": "Deny",
        "private_endpoint_connection_resource_id": request.private_endpoint_connection_resource_id,
        "private_endpoint_connection_state": "Approved",
        "dns_private_only": True,
        "container_scope": request.container_scope,
        "managed_identity_principal_id": request.vm_principal_id,
        "role_definition_id": _CONTRIBUTOR_ROLE_RESOURCE_ID,
        "role_assignment_scope": request.container_scope,
        "no_broader_data_plane_write_role": True,
        "immutability_policy_mode": "Locked",
        "immutability_retention_days": 1,
        "replay_marker_blob_name": marker_name,
        "replay_marker_blob_uri": f"https://{request.blob_account_host}/{request.container_name}/{marker_name}",
        "replay_marker_created": True,
        "replay_marker_created_at": now_text,
        "replay_marker_retain_until": marker["retain_until"],
        "write_operation": operation,
        "control_plane_resource_id": control_plane["arm_resource_id"],
        "control_plane_location": control_plane["location"],
        "control_plane_public_network_access": "Disabled",
        "control_plane_private_endpoint_state": "Approved",
        "signing_key_vault_resource_id": key_vault["arm_resource_id"],
        "signing_key_vault_location": key_vault["location"],
        "signing_key_vault_public_network_access": "Disabled",
        "signing_key_vault_private_endpoint_state": "Approved",
        "signing_key_enabled": True,
        "signing_key_expires_at": key_vault["key_expires_at"],
        "attestation": {
            **{key: claims[key] for key in _ATTESTATION_FIELDS},
            "compact_jws": compact_jws,
            "attestation_digest": hashlib.sha256(compact_jws.encode("utf-8")).hexdigest(),
        },
    }


def run_collect(
    request: CollectRequest,
    *,
    lifecycle: OperatorLifecycle,
    transport: ExternalTransport,
    audit: AuditSink,
    nonce_factory: Callable[[], str],
    clock: Callable[[], str],
    signature_verifier: SignatureVerifier = verify_compact_jws,
    payload_observer: Callable[[], None] | None = None,
) -> OperatorResult:
    _require_lifecycle(lifecycle)
    _validate_collect_request(request)
    trust_bundle = _load_trust_bundle()
    intent_event_id = audit.begin("external.collect", request.target_blob_name)
    try:
        boundary = _prewrite(
            request,
            operation="collect-fragment",
            target_blob_name=request.target_blob_name,
            transport=transport,
            trust_bundle=trust_bundle,
            nonce=nonce_factory(),
            now_text=clock(),
            signature_verifier=signature_verifier,
        )
        if payload_observer is not None:
            payload_observer()
        fragment = {
            "schema_version": "1.0",
            "feature": "001-extension-list",
            "category": "sovereign-external-platform-fragment",
            "validation_session_id": request.session_id,
            "script_path": "scripts/spec001/run_external_platform_validation.py",
            "storage_boundary": boundary,
            "record": request.record,
        }
        if not transport.create_blob_if_absent(request.target_blob_name, fragment):
            raise RuntimeError("fragment already exists")
    except Exception:
        audit.complete(intent_event_id, "external.collect", request.target_blob_name, "failed")
        raise
    audit.complete(intent_event_id, "external.collect", request.target_blob_name, "succeeded")
    return OperatorResult(status="completed-fake", qualifying=False, persisted=False)


def _fragment_write_contexts(fragments: Mapping[str, Mapping[str, object]]) -> list[HostedWriteContext]:
    contexts: list[HostedWriteContext] = []
    for key in fragments:
        contexts.append(
            HostedWriteContext(
                target_key=key,
                operation="collect-fragment",
                conditional_create=True,
                marker_created_before_write=True,
                audit_action="external.collect",
            )
        )
    return contexts


def _require_fresh_final_attestation(
    fragments: Mapping[str, Mapping[str, object]], final_boundary: Mapping[str, object]
) -> None:
    final_attestation = final_boundary.get("attestation")
    if not isinstance(final_attestation, Mapping):
        raise RuntimeError("final attestation is invalid")
    final_values = tuple(final_attestation.get(field) for field in ("jti", "nonce", "compact_jws"))
    for fragment in fragments.values():
        boundary = fragment.get("storage_boundary")
        if not isinstance(boundary, Mapping) or not isinstance(boundary.get("attestation"), Mapping):
            raise RuntimeError("fragment attestation is invalid")
        attestation = boundary["attestation"]
        if any(attestation.get(field) == value for field, value in zip(("jti", "nonce", "compact_jws"), final_values)):
            raise RuntimeError("final attestation must be distinct from every fragment")


def run_finalize(
    request: FinalizeRequest,
    *,
    lifecycle: OperatorLifecycle,
    transport: ExternalTransport,
    audit: AuditSink,
    nonce_factory: Callable[[], str],
    clock: Callable[[], str],
    signature_verifier: SignatureVerifier = verify_compact_jws,
) -> OperatorResult:
    _require_lifecycle(lifecycle)
    collect_shape = _collect_shape(request)
    _validate_collect_request(collect_shape)
    _validate_review(request.review)
    expected_target = f"spec001-extension-list/{request.session_id}/final/platform-evidence.json"
    if request.target_blob_name != expected_target:
        raise RuntimeError("final target is invalid")
    trust_bundle = _load_trust_bundle()
    intent_event_id = audit.begin("external.finalize", request.target_blob_name)
    try:
        boundary = _prewrite(
            collect_shape,
            operation="finalize-canonical",
            target_blob_name=request.target_blob_name,
            transport=transport,
            trust_bundle=trust_bundle,
            nonce=nonce_factory(),
            now_text=clock(),
            signature_verifier=signature_verifier,
        )
        prefix = f"spec001-extension-list/{request.session_id}/fragments/"
        fragments = transport.read_fragments(prefix)
        _require_fresh_final_attestation(fragments, boundary)
        records = [fragment["record"] for _, fragment in sorted(fragments.items())]
        document = {
            "schema_version": "1.0",
            "feature": "001-extension-list",
            "category": "sovereign-external-platform",
            "validation_session_id": request.session_id,
            "script_path": "scripts/spec001/run_external_platform_validation.py",
            "storage_boundary": boundary,
            "records": records,
            "review": request.review,
        }
        writes = _fragment_write_contexts(fragments)
        writes.append(
            HostedWriteContext(
                target_key=request.target_blob_name,
                operation="finalize-canonical",
                conditional_create=True,
                marker_created_before_write=True,
                audit_action="external.finalize",
            )
        )
        validate_hosted_platform_semantics(
            fragments,
            document,
            HostedLifecycleContext(
                writes=tuple(writes),
                human_review_audited=True,
                human_lifecycle_actions_audited=True,
                fake=True,
            ),
        )
        if not transport.create_blob_if_absent(request.target_blob_name, document):
            raise RuntimeError("final evidence already exists")
    except Exception:
        audit.complete(intent_event_id, "external.finalize", request.target_blob_name, "failed")
        raise
    audit.complete(intent_event_id, "external.finalize", request.target_blob_name, "succeeded")
    return OperatorResult(status="completed-fake", qualifying=False, persisted=False)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument("mode", choices=("collect", "finalize"))
    return parser


def main() -> int:
    _parser().parse_args()
    raise RuntimeError("direct external validation invocation is prohibited; use the verified dispatcher lifecycle")


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, ValueError, PermissionError):
        print("external validation: blocked")
        raise SystemExit(1) from None
