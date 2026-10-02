from __future__ import annotations

import argparse
import ast
import importlib.util
import json
import sys
from dataclasses import asdict
from pathlib import Path
from types import ModuleType
from typing import Any, Protocol, cast

import pytest

# isort: split
from specify_cli.daemon_protocol import PROTOCOL_VERSION, AuditReceipt, Handshake, ProtocolError, validate_handshake
from specify_cli.evidence import READ_ONLY_FIELDS

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
SCRIPTS_ROOT = REPOSITORY_ROOT / "scripts" / "spec001"
PACKAGE_SOURCE = REPOSITORY_ROOT / "tools" / "specify-cli" / "src" / "specify_cli"
CONTRACT_ROOT = REPOSITORY_ROOT / "specs" / "001-extension-list" / "contracts"
SEQUENCE_PATH = SCRIPTS_ROOT / "local_gate_sequence.py"
CURRENT_SCHEMAS = (
    "agent-action-audit.schema.json",
    "catalog-config.schema.json",
    "catalog-source.schema.json",
    "extension-list.schema.json",
    "external-validation-status.schema.json",
    "implementation-prerequisite-attestation.schema.json",
    "platform-evidence.schema.json",
    "root-regression-baseline.schema.json",
    "usability-evidence.schema.json",
)
PLANNED_EPHEMERAL_SCHEMAS = ("read-only-evidence.schema.json", "performance-evidence.schema.json")
SOVEREIGN_BINDINGS = {
    "execution_mode",
    "audit_sink",
    "sovereign_session_id",
    "preflight_attestation_digest",
    "execution_vm_resource_id",
    "audit_intent_event_id",
    "audit_intent_event_digest",
}


class _ProtectedStateModule(Protocol):
    BOOTSTRAP_PATHS: tuple[str, ...]


class _RootRegressionModule(Protocol):
    RuntimeBinding: Any
    RootRegressionBaseline: Any
    ROOT_REGRESSION_COMMAND: tuple[str, ...]

    def validate_restart_policy(self, execution_mode: str, custody_lost: bool, product_edited: bool) -> None: ...


class _DispatcherModule(Protocol):
    def _parser(self) -> argparse.ArgumentParser: ...

    def validate_partition_capacity(self, sequence: int, finalizing: bool) -> None: ...

    def validate_fixture_access(
        self, project_root: Path | None, session_temp: Path, environment: dict[str, str]
    ) -> None: ...

    def validate_sovereign_environment(self, environment: dict[str, str]) -> None: ...


class _ExternalModule(Protocol):
    OperatorResult: Any


def _load_script(name: str) -> ModuleType:
    path = SCRIPTS_ROOT / f"{name}.py"
    specification = importlib.util.spec_from_file_location(f"spec001_final_{name}", path)
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    sys.modules[specification.name] = module
    sys.path.insert(0, str(SCRIPTS_ROOT))
    try:
        specification.loader.exec_module(module)
    finally:
        sys.path.remove(str(SCRIPTS_ROOT))
    return module


def _schema(name: str) -> dict[str, object]:
    value = json.loads((CONTRACT_ROOT / name).read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _mapping(value: object) -> dict[str, object]:
    assert isinstance(value, dict)
    return value


def _string_set(value: object) -> set[str]:
    assert isinstance(value, list) and all(isinstance(item, str) for item in value)
    return set(value)


def test_final_dependency_assembly_bootstrap_and_baseline() -> None:
    protected_state = cast(_ProtectedStateModule, _load_script("protected_state"))
    dispatcher = cast(_DispatcherModule, _load_script("run_local_gates"))
    root_regression = cast(_RootRegressionModule, _load_script("root_regression"))

    assert protected_state.BOOTSTRAP_PATHS == (
        "scripts/spec001/protected_state_selfcheck.py",
        "scripts/spec001/dispatcher_selfcheck_cases.py",
        "scripts/spec001/protected_state.py",
        "scripts/spec001/root_regression.py",
        "scripts/spec001/run_local_gates.py",
    )
    start_source = ast.get_source_segment(
        (SCRIPTS_ROOT / "run_local_gates.py").read_text(encoding="utf-8"),
        next(
            node
            for node in ast.parse((SCRIPTS_ROOT / "run_local_gates.py").read_text(encoding="utf-8")).body
            if isinstance(node, ast.FunctionDef) and node.name == "_start_session"
        ),
    )
    assert start_source is not None
    assert "protected_bootstrap_manifest" in start_source
    assert "session_manifest_digest" in start_source
    assert "execute_root_regression" in start_source
    assert 'state["root_baseline"] = baseline.to_json()' in start_source

    runtime = root_regression.RuntimeBinding("3.14.7", "uv 0.11.21", "Windows", "ARM64")
    baseline = root_regression.RootRegressionBaseline(
        root_regression.ROOT_REGRESSION_COMMAND,
        runtime,
        2,
        (),
        (),
        1,
        1,
        "a" * 64,
        "00000000-0000-4000-8000-000000000127",
        True,
    )
    assert root_regression.RootRegressionBaseline.from_json(baseline.to_json()) == baseline
    root_regression.validate_restart_policy("local-synthetic", True, True)
    with pytest.raises(RuntimeError, match="terminally prohibited"):
        root_regression.validate_restart_policy("sovereign", True, True)
    assert not any(
        option in dispatcher._parser()._option_string_actions for option in ("--resume-session", "--combine-segments")
    )


def test_final_dependency_assembly_ipc_and_audit() -> None:
    dispatcher = cast(_DispatcherModule, _load_script("run_local_gates"))
    expected = Handshake(
        protocol_version=PROTOCOL_VERSION,
        peer_identity="current-owner",
        session_id="00000000-0000-4000-8000-000000000128",
        execution_mode="local-synthetic",
        repository_digest="a" * 64,
        temp_policy="owner-only-ephemeral",
        audit_head="b" * 64,
    )
    validate_handshake(expected, expected)
    with pytest.raises(ProtocolError, match="execution mode mismatch"):
        validate_handshake(expected.replaced(execution_mode="sovereign"), expected)
    receipt = AuditReceipt("intent-event", "result-event", "succeeded")
    assert asdict(receipt) == {
        "intent_event_id": "intent-event",
        "result_event_id": "result-event",
        "outcome": "succeeded",
    }

    dispatcher.validate_partition_capacity(48_997, False)
    with pytest.raises(RuntimeError, match="reserved finalization pair"):
        dispatcher.validate_partition_capacity(48_998, False)
    dispatcher.validate_partition_capacity(48_998, True)
    dispatcher.validate_partition_capacity(48_999, True)
    with pytest.raises(RuntimeError, match="capacity exhausted"):
        dispatcher.validate_partition_capacity(49_000, True)

    daemon_source = (PACKAGE_SOURCE / "daemon.py").read_text(encoding="utf-8")
    client_source = (PACKAGE_SOURCE / "daemon_client.py").read_text(encoding="utf-8")
    assert "AF_UNIX" in daemon_source and "flock" in daemon_source
    assert "SO_PEERCRED" in client_source
    assert 'ctypes.WinDLL("advapi32"' in client_source
    assert 'ctypes.WinDLL("kernel32"' in client_source
    assert all((PACKAGE_SOURCE / name).is_file() for name in ("daemon.py", "daemon_client.py", "daemon_protocol.py"))
    cli_source = (PACKAGE_SOURCE / "cli.py").read_text(encoding="utf-8")
    assert "request_extension_list" in cli_source
    assert "extensions.inventory" not in cli_source and "extensions.catalogs" not in cli_source


def test_final_dependency_assembly_fixture_and_network_policy(tmp_path: Path) -> None:
    dispatcher = cast(_DispatcherModule, _load_script("run_local_gates"))
    fixture_root = tmp_path / "fixture"
    fixture_root.mkdir(mode=0o700)
    marker = {
        "schema_version": "1.0",
        "feature": "001-extension-list",
        "fixture_id": "final-assembly",
        "source_digest": "a" * 64,
    }
    (fixture_root / ".spec001-synthetic-fixture.json").write_text(json.dumps(marker), encoding="utf-8")
    dispatcher.validate_fixture_access(fixture_root, tmp_path, {"SPEC001_TEST_MODE": "synthetic"})
    dispatcher.validate_fixture_access(None, tmp_path, {})

    with pytest.raises(PermissionError, match="beneath owner-only session"):
        dispatcher.validate_fixture_access(REPOSITORY_ROOT, tmp_path, {"SPEC001_TEST_MODE": "synthetic"})
    with pytest.raises(PermissionError, match="requires synthetic mode"):
        dispatcher.validate_fixture_access(fixture_root, tmp_path, {})

    dispatcher.validate_sovereign_environment({})
    for name in ("SPEC001_TEST_MODE", "SPEC001_EXTERNAL_TRANSPORT", "SPEC001_UNKNOWN", "SPECIFY_CLI_UNKNOWN"):
        with pytest.raises(ValueError, match="sovereign mode rejects"):
            dispatcher.validate_sovereign_environment({name: "fake"})


def test_final_dependency_assembly_schema_and_evidence_bindings() -> None:
    schemas = [_schema(name) for name in (*CURRENT_SCHEMAS, *PLANNED_EPHEMERAL_SCHEMAS)]
    assert len(CURRENT_SCHEMAS) == 9
    assert len(PLANNED_EPHEMERAL_SCHEMAS) == 2
    assert all(schema["$schema"] == "https://json-schema.org/draft/2020-12/schema" for schema in schemas)
    identifiers = [schema["$id"] for schema in schemas]
    assert len(set(identifiers)) == 11

    read_only = _schema("read-only-evidence.schema.json")
    performance = _schema("performance-evidence.schema.json")
    assert SOVEREIGN_BINDINGS <= _string_set(read_only["required"])
    assert SOVEREIGN_BINDINGS <= _string_set(performance["required"])
    assert SOVEREIGN_BINDINGS <= READ_ONLY_FIELDS
    for schema in (read_only, performance):
        properties = _mapping(schema["properties"])
        assert _mapping(properties["execution_mode"])["const"] == "sovereign"
        assert _mapping(properties["audit_sink"])["const"] == "immutable-au"


def test_final_dependency_assembly_external_boundaries() -> None:
    external = cast(_ExternalModule, _load_script("run_external_platform_validation"))
    fake_result = external.OperatorResult(status="completed-fake", qualifying=False, persisted=False)
    assert asdict(fake_result) == {"status": "completed-fake", "qualifying": False, "persisted": False}

    source = (SCRIPTS_ROOT / "run_external_platform_validation.py").read_text(encoding="utf-8")
    assert "implementation permits fake transport only" in source
    assert "create_replay_marker_if_absent" in source
    assert "final attestation must be distinct from every fragment" in source
    assert "evaluate_storage_blob_authorization" in source
    assert "Storage Blob Data Contributor authorization is invalid" in source

    live_checklist = (
        REPOSITORY_ROOT / "specs" / "001-extension-list" / "checklists" / "phase4-final-134-live.md"
    ).read_text(encoding="utf-8")
    assert "pending-external" in live_checklist
    assert "do not mean implementation" in live_checklist
    assert "pseudonymous" in live_checklist


def test_final_dependency_assembly_responsibility_split() -> None:
    source = SEQUENCE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(SEQUENCE_PATH))
    functions = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}
    assert {"assemble_package_commands", "parse_package_coverage", "run_local_gate_sequence"} <= functions.keys()

    assembly_calls = {
        node.func.id
        for node in ast.walk(functions["run_local_gate_sequence"])
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    assert {"assemble_package_commands", "parse_package_coverage"} <= assembly_calls
    assert "root_regression" not in source
    assert "subprocess" not in source

    root_source = (SCRIPTS_ROOT / "root_regression.py").read_text(encoding="utf-8")
    assert "def execute_root_regression(" in root_source
    assert "def compare_root_regression(" in root_source
