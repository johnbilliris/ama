from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import stat
from typing import Callable, Mapping, Protocol

from specify_cli.evidence import EvidenceBindingContext, EvidenceValidationResult


class EphemeralPerformanceStore(Protocol):
    owner_only: bool

    def write(self, value: dict[str, object]) -> None: ...

    def logical_delete(self) -> None: ...


@dataclass(frozen=True)
class FixtureBinding:
    root: Path
    fixture_id: str
    record_count: int


def _owner_only_directory(path: Path, label: str) -> Path:
    if path.is_symlink():
        raise PermissionError(f"{label} must not be a symlink")
    resolved = path.resolve(strict=True)
    metadata = resolved.stat()
    if hasattr(os, "getuid") and metadata.st_uid != os.getuid():
        raise PermissionError(f"{label} must be owned by the current user")
    if os.name != "nt" and stat.S_IMODE(metadata.st_mode) != 0o700:
        raise PermissionError(f"{label} must have mode 0700")
    return resolved


def _read_json_file(path: Path, label: str) -> object:
    if not path.is_file() or path.is_symlink():
        raise PermissionError(f"{label} must be a regular non-symlink file")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(f"{label} is invalid") from error


def _validate_fixture(
    *,
    seed_path: Path,
    session_temp: Path,
    fixture_root: Path | None,
    expected_source_digest: str,
    expected_fixture_id: str,
) -> FixtureBinding:
    resolved_session = _owner_only_directory(session_temp, "session temporary root")
    if fixture_root is None:
        raise ValueError("performance benchmark requires the 100-record fixture")
    if fixture_root.is_symlink():
        raise PermissionError("fixture root must not be a symlink")
    resolved_fixture = fixture_root.resolve(strict=True)
    if not resolved_fixture.is_relative_to(resolved_session):
        raise PermissionError("fixture root must be beneath the session temporary root")
    _owner_only_directory(resolved_fixture, "fixture root")

    marker = _read_json_file(resolved_fixture / ".spec001-synthetic-fixture.json", "fixture marker")
    if not isinstance(marker, dict):
        raise ValueError("fixture marker must contain an object")
    expected_marker = {
        "schema_version": "1.0",
        "feature": "001-extension-list",
        "fixture_id": expected_fixture_id,
        "source_digest": expected_source_digest,
    }
    if marker != expected_marker:
        if marker.get("source_digest") != expected_source_digest:
            raise PermissionError("fixture marker source digest mismatch")
        raise PermissionError("fixture marker binding mismatch")

    seed = _read_json_file(seed_path, "performance seed")
    if not isinstance(seed, list) or len(seed) != 100:
        raise ValueError("performance seed must contain exactly 100 records")
    seen_paths: set[str] = set()
    extensions_root = resolved_fixture / ".specify" / "extensions"
    for record in seed:
        if not isinstance(record, dict) or set(record) != {"path", "manifest"}:
            raise ValueError("performance seed record is invalid")
        relative_path = record["path"]
        if not isinstance(relative_path, str) or not relative_path or relative_path in seen_paths:
            raise ValueError("performance seed paths must be unique non-empty strings")
        seen_paths.add(relative_path)
        manifest_path = extensions_root / relative_path / "extension.yml"
        if not manifest_path.is_file() or manifest_path.is_symlink():
            raise PermissionError("materialized performance manifest is invalid")
        if not manifest_path.resolve(strict=True).is_relative_to(extensions_root.resolve(strict=True)):
            raise PermissionError("materialized performance manifest escapes the fixture")
    return FixtureBinding(resolved_fixture, expected_fixture_id, len(seed))


def _require_producer_boundaries(
    *,
    context: EvidenceBindingContext,
    temporary_store: EphemeralPerformanceStore,
    daemon_prestarted: bool,
    private_network_verified: bool,
) -> None:
    if not context.fake:
        raise PermissionError("local performance producer tests require fake boundaries")
    if temporary_store.owner_only is not True or context.owner_only_temporary_storage is not True:
        raise PermissionError("performance producer requires owner-only temporary storage")
    if not daemon_prestarted or not context.peer_authenticated:
        raise PermissionError("performance producer requires a peer-authenticated pre-started daemon")
    if not private_network_verified:
        raise PermissionError("performance producer requires a verified private network")


def run_ephemeral_performance_benchmark(
    *,
    seed_path: Path,
    session_temp: Path,
    fixture_root: Path | None,
    expected_source_digest: str,
    expected_fixture_id: str,
    environment: Mapping[str, str],
    context: EvidenceBindingContext,
    machine_metadata: Mapping[str, object],
    monotonic: Callable[[], float],
    cold_client: Callable[[Path], int],
    schema_validate: Callable[[dict[str, object]], None],
    semantic_validate: Callable[[dict[str, object], EvidenceBindingContext], EvidenceValidationResult],
    temporary_store: EphemeralPerformanceStore,
    daemon_prestarted: bool,
    private_network_verified: bool,
    execution_mode: str,
    qualifying: bool,
) -> EvidenceValidationResult:
    if qualifying and execution_mode != "sovereign":
        raise PermissionError("local-synthetic cannot produce qualifying performance evidence")
    if qualifying:
        raise PermissionError("fake boundaries cannot produce qualifying performance evidence")
    if execution_mode == "local-synthetic" and environment.get("SPEC001_TEST_MODE") != "synthetic":
        raise PermissionError("local-synthetic performance requires SPEC001_TEST_MODE=synthetic")
    _require_producer_boundaries(
        context=context,
        temporary_store=temporary_store,
        daemon_prestarted=daemon_prestarted,
        private_network_verified=private_network_verified,
    )
    fixture = _validate_fixture(
        seed_path=seed_path,
        session_temp=session_temp,
        fixture_root=fixture_root,
        expected_source_digest=expected_source_digest,
        expected_fixture_id=expected_fixture_id,
    )

    warmup_outcomes: list[dict[str, object]] = []
    for _ in range(3):
        before = monotonic()
        exit_code = cold_client(fixture.root)
        after = monotonic()
        if after < before:
            raise ValueError("monotonic clock moved backwards")
        warmup_outcomes.append({"exit_code": exit_code, "passed": exit_code == 0})
    if not all(outcome["passed"] for outcome in warmup_outcomes):
        raise RuntimeError("performance warmup failed")

    durations: list[float] = []
    for _ in range(30):
        before = monotonic()
        exit_code = cold_client(fixture.root)
        after = monotonic()
        if exit_code != 0:
            raise RuntimeError("performance cold client failed")
        duration = after - before
        if duration < 0:
            raise ValueError("monotonic clock moved backwards")
        durations.append(duration)
    p95_seconds = sorted(durations)[28]

    evidence = {
        **dict(machine_metadata),
        "network_disabled": True,
        "fixture_id": fixture.fixture_id,
        "fixture_count": fixture.record_count,
        "warmup_outcomes": warmup_outcomes,
        "durations_seconds": durations,
        "rank": 29,
        "p95_seconds": p95_seconds,
        "threshold_seconds": 2.0,
        "passed": p95_seconds <= 2.0,
        "execution_mode": "sovereign",
        "audit_sink": "immutable-au",
        "sovereign_session_id": context.sovereign_session_id,
        "preflight_attestation_digest": context.preflight_attestation_digest,
        "execution_vm_resource_id": context.execution_vm_resource_id,
        "audit_intent_event_id": context.audit_intent_event_id,
        "audit_intent_event_digest": context.audit_intent_event_digest,
    }
    temporary_store.write(evidence)
    try:
        schema_validate(evidence)
        semantic_result = semantic_validate(evidence, context)
        if semantic_result.qualifying or semantic_result.persisted:
            raise ValueError("fake performance semantic validation cannot qualify or persist")
        return EvidenceValidationResult(status="passed-fake", qualifying=False, persisted=False)
    finally:
        temporary_store.logical_delete()