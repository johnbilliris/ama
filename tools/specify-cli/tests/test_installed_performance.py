from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import stat
import sys
from collections.abc import Callable
from copy import deepcopy
from pathlib import Path
from typing import Any, cast

import pytest
import rfc8785
from jsonschema import Draft202012Validator, FormatChecker

# isort: split
from specify_cli.evidence import EvidenceBindingContext, EvidenceValidationResult, validate_performance_semantics

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
SCHEMA_PATH = REPOSITORY_ROOT / "specs" / "001-extension-list" / "contracts" / "performance-evidence.schema.json"
SESSION_ID = "11111111-1111-4111-8111-111111111111"
VM_RESOURCE_ID = "/subscriptions/sub/resourceGroups/rg/providers/Microsoft.Compute/virtualMachines/runner"
INTENT_ID = "77777777-7777-4777-8777-777777777777"
SEED_PATH = Path(__file__).parent / "fixtures" / "extensions" / "installed" / "performance-100" / "records.json"
BUILDER_PATH = Path(__file__)


def _load_benchmark_runner() -> Any:
    path = REPOSITORY_ROOT / "scripts" / "spec001" / "benchmark_installed.py"
    specification = importlib.util.spec_from_file_location("spec001_benchmark_installed", path)
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    sys.modules[specification.name] = module
    specification.loader.exec_module(module)
    return module.run_ephemeral_performance_benchmark


run_ephemeral_performance_benchmark = _load_benchmark_runner()


def _recording_client(calls: list[str]) -> Callable[[Path], int]:
    def run(_: Path) -> int:
        calls.append("client")
        return 0

    return run


def _performance_evidence() -> dict[str, object]:
    durations = [value / 100 for value in range(30, 0, -1)]
    return {
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
        "durations_seconds": durations,
        "rank": 29,
        "p95_seconds": 0.29,
        "threshold_seconds": 2.0,
        "passed": True,
        "execution_mode": "sovereign",
        "audit_sink": "immutable-au",
        "sovereign_session_id": SESSION_ID,
        "preflight_attestation_digest": "a" * 64,
        "execution_vm_resource_id": VM_RESOURCE_ID,
        "audit_intent_event_id": INTENT_ID,
        "audit_intent_event_digest": "b" * 64,
    }


def _context(*, fake: bool = True) -> EvidenceBindingContext:
    return EvidenceBindingContext(
        execution_mode="sovereign",
        audit_sink="immutable-au",
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


def test_performance_semantic_validator_recomputes_rank_29_p95_threshold_and_passed() -> None:
    evidence = _performance_evidence()
    _schema_validate(evidence)
    result = validate_performance_semantics(evidence, _context())

    assert sorted(cast(list[float], evidence["durations_seconds"]))[28] == 0.29
    assert result.status == "validated-fake"
    assert result.qualifying is False
    assert result.persisted is False
    assert result.details is None


@pytest.mark.parametrize(
    ("field", "replacement", "message"),
    [
        ("fixture_count", 99, "fixture count"),
        ("warmup_outcomes", [{"exit_code": 0, "passed": True}] * 2, "warmup"),
        ("durations_seconds", [0.1] * 29, "30 durations"),
        ("rank", 28, "rank 29"),
        ("p95_seconds", 0.30, "P95"),
        ("threshold_seconds", 2.001, "threshold"),
        ("passed", False, "passed"),
        ("network_disabled", False, "network"),
    ],
)
def test_performance_semantic_validator_rejects_measurement_drift(
    field: str, replacement: object, message: str
) -> None:
    evidence = {**_performance_evidence(), field: replacement}
    with pytest.raises(ValueError, match=message):
        validate_performance_semantics(evidence, _context())


@pytest.mark.parametrize(
    ("field", "replacement"),
    [
        ("execution_mode", "local-synthetic"),
        ("audit_sink", "ephemeral-local"),
        ("sovereign_session_id", "99999999-9999-4999-8999-999999999999"),
        ("preflight_attestation_digest", "e" * 64),
        (
            "execution_vm_resource_id",
            "/subscriptions/sub/resourceGroups/rg/providers/Microsoft.Compute/virtualMachines/other",
        ),
        ("audit_intent_event_id", "88888888-8888-4888-8888-888888888888"),
        ("audit_intent_event_digest", "e" * 64),
    ],
)
def test_performance_semantic_validator_cross_checks_all_seven_bindings(field: str, replacement: object) -> None:
    evidence = {**_performance_evidence(), field: replacement}
    with pytest.raises(ValueError, match="binding"):
        validate_performance_semantics(evidence, _context())


def test_performance_semantic_validator_requires_signed_preflight_live_imds_and_ledger() -> None:
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
        with pytest.raises(ValueError, match="boundary"):
            validate_performance_semantics(_performance_evidence(), context.replaced(**{field: False}))
    with pytest.raises(ValueError, match="intent linkage"):
        validate_performance_semantics(
            _performance_evidence(),
            context.replaced(audit_result_intent_event_id="88888888-8888-4888-8888-888888888888"),
        )


def test_performance_semantic_validator_never_qualifies_local_fake_vectors() -> None:
    with pytest.raises(PermissionError, match="fake"):
        validate_performance_semantics(_performance_evidence(), _context(fake=False))
    local = deepcopy(_performance_evidence())
    local["execution_mode"] = "local-synthetic"
    with pytest.raises(ValueError, match="binding"):
        validate_performance_semantics(local, _context())


def _fixture_source_digest() -> str:
    source_files = sorted((BUILDER_PATH, SEED_PATH), key=lambda path: path.relative_to(REPOSITORY_ROOT).as_posix())
    manifest = [
        {
            "path": path.relative_to(REPOSITORY_ROOT).as_posix(),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        }
        for path in source_files
    ]
    return hashlib.sha256(rfc8785.dumps(manifest)).hexdigest()


def _materialize_performance_fixture(session_temp: Path) -> tuple[Path, str, str]:
    session_temp.chmod(0o700)
    fixture_root = session_temp / "performance-fixture"
    fixture_root.mkdir(mode=0o700)
    fixture_root.chmod(0o700)
    records = json.loads(SEED_PATH.read_text(encoding="utf-8"))
    assert isinstance(records, list) and len(records) == 100
    extensions_root = fixture_root / ".specify" / "extensions"
    extensions_root.mkdir(parents=True)
    for record in records:
        manifest_path = extensions_root / record["path"] / "extension.yml"
        manifest_path.parent.mkdir()
        manifest_path.write_text(json.dumps(record["manifest"], sort_keys=True) + "\n", encoding="utf-8")
    fixture_id = "performance-100"
    source_digest = _fixture_source_digest()
    (fixture_root / ".spec001-synthetic-fixture.json").write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "feature": "001-extension-list",
                "fixture_id": fixture_id,
                "source_digest": source_digest,
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return fixture_root, fixture_id, source_digest


class FakeClock:
    def __init__(self, durations: list[float]) -> None:
        self.value = 0.0
        self.durations = iter(durations)

    def monotonic(self) -> float:
        return self.value

    def advance_client(self) -> None:
        self.value += next(self.durations)


class FakePerformanceStore:
    def __init__(self, events: list[str]) -> None:
        self.events = events
        self.owner_only = True
        self.value: dict[str, object] | None = None
        self.logically_deleted = False

    def write(self, value: dict[str, object]) -> None:
        self.events.append("write")
        self.value = deepcopy(value)

    def logical_delete(self) -> None:
        self.events.append("delete")
        self.value = None
        self.logically_deleted = True


def _machine_metadata() -> dict[str, object]:
    return {
        "os": "synthetic-os",
        "architecture": "x64",
        "cpu_model": "Synthetic CPU",
        "logical_cpu_count": 8,
        "total_memory_bytes": 17179869184,
        "python_version": "3.12.1",
        "package_version": "0.1.0",
        "lock_sha256": "f" * 64,
        "runner_id": "synthetic-runner",
        "executed_at": "2026-09-21T00:00:00Z",
    }


def test_ephemeral_performance_producer_uses_100_records_3_warmups_30_cold_clients_and_deletes(
    tmp_path: Path,
) -> None:
    fixture_root, fixture_id, source_digest = _materialize_performance_fixture(tmp_path)
    durations = [0.01, 0.02, 0.03, *[value / 100 for value in range(30, 0, -1)]]
    clock = FakeClock(durations)
    events: list[str] = []
    observed: list[dict[str, object]] = []
    store = FakePerformanceStore(events)

    def cold_client(root: Path) -> int:
        assert root == fixture_root
        events.append("client")
        clock.advance_client()
        return 0

    def schema_validate(value: dict[str, object]) -> None:
        events.append("schema")
        observed.append(deepcopy(value))
        _schema_validate(value)

    def semantic_validate(value: dict[str, object], context: EvidenceBindingContext) -> EvidenceValidationResult:
        events.append("semantic")
        return validate_performance_semantics(value, context)

    result = run_ephemeral_performance_benchmark(
        seed_path=SEED_PATH,
        session_temp=tmp_path,
        fixture_root=fixture_root,
        expected_source_digest=source_digest,
        expected_fixture_id=fixture_id,
        environment={"SPEC001_TEST_MODE": "synthetic", "SPECIFY_CLI_NETWORK_DISABLED": "1"},
        context=_context(),
        machine_metadata=_machine_metadata(),
        monotonic=clock.monotonic,
        cold_client=cold_client,
        schema_validate=schema_validate,
        semantic_validate=semantic_validate,
        temporary_store=store,
        daemon_prestarted=True,
        private_network_verified=True,
        execution_mode="local-synthetic",
        qualifying=False,
    )

    assert events.count("client") == 33
    assert events[-4:] == ["write", "schema", "semantic", "delete"]
    assert len(observed) == 1
    evidence = observed[0]
    assert evidence["fixture_count"] == 100
    assert len(cast(list[dict[str, object]], evidence["warmup_outcomes"])) == 3
    durations = cast(list[float], evidence["durations_seconds"])
    assert len(durations) == 30
    assert evidence["rank"] == 29
    assert evidence["p95_seconds"] == sorted(durations)[28]
    assert store.logically_deleted is True and store.value is None
    assert result.status == "passed-fake"
    assert result.qualifying is False and result.persisted is False and result.details is None


def test_ephemeral_performance_producer_rejects_qualification_or_live_repository_before_access(tmp_path: Path) -> None:
    calls: list[str] = []
    with pytest.raises(PermissionError, match="local-synthetic"):
        run_ephemeral_performance_benchmark(
            seed_path=SEED_PATH,
            session_temp=tmp_path,
            fixture_root=REPOSITORY_ROOT,
            expected_source_digest=_fixture_source_digest(),
            expected_fixture_id="performance-100",
            environment={"SPEC001_TEST_MODE": "synthetic"},
            context=_context(),
            machine_metadata=_machine_metadata(),
            monotonic=lambda: 0.0,
            cold_client=_recording_client(calls),
            schema_validate=lambda _: calls.append("schema"),
            semantic_validate=validate_performance_semantics,
            temporary_store=FakePerformanceStore(calls),
            daemon_prestarted=True,
            private_network_verified=True,
            execution_mode="local-synthetic",
            qualifying=True,
        )
    assert calls == []

    with pytest.raises(PermissionError, match="session temporary root"):
        run_ephemeral_performance_benchmark(
            seed_path=SEED_PATH,
            session_temp=tmp_path,
            fixture_root=REPOSITORY_ROOT,
            expected_source_digest=_fixture_source_digest(),
            expected_fixture_id="performance-100",
            environment={"SPEC001_TEST_MODE": "synthetic"},
            context=_context(),
            machine_metadata=_machine_metadata(),
            monotonic=lambda: 0.0,
            cold_client=_recording_client(calls),
            schema_validate=lambda _: calls.append("schema"),
            semantic_validate=validate_performance_semantics,
            temporary_store=FakePerformanceStore(calls),
            daemon_prestarted=True,
            private_network_verified=True,
            execution_mode="local-synthetic",
            qualifying=False,
        )
    assert calls == []


def test_ephemeral_performance_producer_rejects_bad_marker_symlink_and_environment_before_clients(
    tmp_path: Path,
) -> None:
    fixture_root, fixture_id, source_digest = _materialize_performance_fixture(tmp_path)
    marker_path = fixture_root / ".spec001-synthetic-fixture.json"
    marker = json.loads(marker_path.read_text(encoding="utf-8"))
    calls: list[str] = []

    for environment, digest, message in (
        ({}, source_digest, "SPEC001_TEST_MODE"),
        ({"SPEC001_TEST_MODE": "synthetic"}, "0" * 64, "source digest"),
    ):
        with pytest.raises((PermissionError, ValueError), match=message):
            run_ephemeral_performance_benchmark(
                seed_path=SEED_PATH,
                session_temp=tmp_path,
                fixture_root=fixture_root,
                expected_source_digest=digest,
                expected_fixture_id=fixture_id,
                environment=environment,
                context=_context(),
                machine_metadata=_machine_metadata(),
                monotonic=lambda: 0.0,
                cold_client=_recording_client(calls),
                schema_validate=lambda _: None,
                semantic_validate=validate_performance_semantics,
                temporary_store=FakePerformanceStore(calls),
                daemon_prestarted=True,
                private_network_verified=True,
                execution_mode="local-synthetic",
                qualifying=False,
            )
    assert calls == []

    if hasattr(os, "symlink"):
        marker_path.unlink()
        target = fixture_root / "marker-target.json"
        target.write_text(json.dumps(marker), encoding="utf-8")
        try:
            marker_path.symlink_to(target)
        except OSError:
            pytest.skip("symlink creation is unavailable")
        with pytest.raises(PermissionError, match="marker"):
            run_ephemeral_performance_benchmark(
                seed_path=SEED_PATH,
                session_temp=tmp_path,
                fixture_root=fixture_root,
                expected_source_digest=source_digest,
                expected_fixture_id=fixture_id,
                environment={"SPEC001_TEST_MODE": "synthetic"},
                context=_context(),
                machine_metadata=_machine_metadata(),
                monotonic=lambda: 0.0,
                cold_client=_recording_client(calls),
                schema_validate=lambda _: None,
                semantic_validate=validate_performance_semantics,
                temporary_store=FakePerformanceStore(calls),
                daemon_prestarted=True,
                private_network_verified=True,
                execution_mode="local-synthetic",
                qualifying=False,
            )
    assert stat.S_IMODE(tmp_path.stat().st_mode) == (
        0o700 if os.name != "nt" else stat.S_IMODE(tmp_path.stat().st_mode)
    )
    assert calls == []
