from __future__ import annotations

import inspect
import json
import os
import socket
import stat
import subprocess
import sys
import tempfile
import zipfile
from collections.abc import Iterator
from pathlib import Path

import pytest

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = PACKAGE_ROOT / "src"
FORBIDDEN_CLIENT_MODULES = {
    "requests",
    "jsonschema",
    "specify_cli.extensions.catalogs",
    "specify_cli.extensions.catalog_transport",
}


def _current_uid() -> int:
    getuid = getattr(os, "getuid", None)
    if getuid is None:
        raise RuntimeError("current UID is unavailable")
    return int(getuid())


@pytest.fixture(scope="module")
def clean_installed_wheel() -> Iterator[tuple[Path, Path]]:
    with tempfile.TemporaryDirectory(prefix="spec001-package-isolation-") as raw_directory:
        external_root = Path(raw_directory)
        external_root.chmod(0o700)
        wheel_directory = external_root / "wheel"
        environment_directory = external_root / "venv"
        wheel_directory.mkdir()

        build_environment = os.environ.copy()
        build_environment["VIRTUAL_ENV"] = sys.prefix
        subprocess.run(
            [
                "uv",
                "build",
                "--wheel",
                "--no-build-isolation",
                "--out-dir",
                str(wheel_directory),
                str(PACKAGE_ROOT),
            ],
            cwd=external_root,
            env=build_environment,
            check=True,
            capture_output=True,
            text=True,
        )
        wheels = list(wheel_directory.glob("*.whl"))
        assert len(wheels) == 1
        with zipfile.ZipFile(wheels[0]) as archive:
            assert "specify_cli/daemon.py" in archive.namelist()

        sync_environment = os.environ.copy()
        sync_environment["UV_PROJECT_ENVIRONMENT"] = str(environment_directory)
        sync_environment.pop("UV_FROZEN", None)
        subprocess.run(
            ["uv", "sync", "--project", str(PACKAGE_ROOT), "--locked", "--offline"],
            cwd=external_root,
            env=sync_environment,
            check=True,
            capture_output=True,
            text=True,
        )
        installed_python = environment_directory / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        subprocess.run(
            ["uv", "pip", "install", "--offline", "--no-deps", "--python", str(installed_python), str(wheels[0])],
            cwd=external_root,
            check=True,
            capture_output=True,
            text=True,
        )
        yield installed_python, external_root


def _run_installed_probe(installed_python: Path, external_root: Path, source: str) -> set[str]:
    process = subprocess.run(
        [str(installed_python), "-c", source],
        cwd=external_root,
        check=True,
        capture_output=True,
        text=True,
    )
    return set(json.loads(process.stdout.splitlines()[-1]))


def _run_cold_client(entry_point: str, cwd: Path) -> set[str]:
    bootstrap = """
import json
import runpy
import sys
from specify_cli.daemon_protocol import AuditReceipt, ClientResponse
import specify_cli.daemon_client as client

client.request_extension_list = lambda **_: ClientResponse(
    stdout='[]\\n',
    stderr='',
    exit_code=0,
    audit=AuditReceipt(intent_event_id='intent', result_event_id='result', outcome='succeeded'),
)
if ENTRY_POINT == 'console':
    from typer.testing import CliRunner
    from specify_cli.cli import app
    result = CliRunner().invoke(app, ['extension', 'list', '--json'], catch_exceptions=False)
    assert result.exit_code == 0
else:
    sys.argv = ['python -m specify_cli', 'extension', 'list', '--json']
    try:
        runpy.run_module('specify_cli', run_name='__main__')
    except SystemExit as error:
        assert error.code in (None, 0)
print(json.dumps(sorted(sys.modules)))
""".replace("ENTRY_POINT", repr(entry_point))
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(SOURCE_ROOT)
    process = subprocess.run(
        [sys.executable, "-c", bootstrap],
        cwd=cwd,
        env=environment,
        check=True,
        capture_output=True,
        text=True,
    )
    return set(json.loads(process.stdout.splitlines()[-1]))


@pytest.mark.parametrize("entry_point", ["console", "module"])
def test_import_boundary_cold_installed_clients_exclude_heavy_modules(entry_point: str) -> None:
    with tempfile.TemporaryDirectory(prefix="spec001-cold-client-") as raw_directory:
        directory = Path(raw_directory)
        directory.chmod(0o700)
        loaded = _run_cold_client(entry_point, directory)

    assert loaded.isdisjoint(FORBIDDEN_CLIENT_MODULES)


def test_import_boundary_daemon_installed_handler_loads_no_catalog_stack(tmp_path: Path) -> None:
    from specify_cli.daemon import handle_installed_request
    from specify_cli.daemon_protocol import ListRequest

    before = set(sys.modules)
    response = handle_installed_request(
        ListRequest(view="installed", output_json=True, discovery_start=tmp_path),
        session_id="session-local",
        execution_mode="local-synthetic",
        inventory_loader=lambda _: [],
    )
    newly_loaded = set(sys.modules) - before

    assert response.exit_code == 0
    assert newly_loaded.isdisjoint(FORBIDDEN_CLIENT_MODULES)


@pytest.mark.parametrize("entry_point", ["console", "module"])
def test_package_isolation_clean_wheel_cold_clients_exclude_heavy_modules(
    clean_installed_wheel: tuple[Path, Path], entry_point: str
) -> None:
    installed_python, external_root = clean_installed_wheel
    bootstrap = """
import json
import runpy
import sys
from specify_cli.daemon_protocol import AuditReceipt, ClientResponse
import specify_cli.daemon_client as client

client.request_extension_list = lambda **_: ClientResponse(
    stdout='[]\\n',
    stderr='',
    exit_code=0,
    audit=AuditReceipt(intent_event_id='intent', result_event_id='result', outcome='succeeded'),
)
if ENTRY_POINT == 'console':
    from typer.testing import CliRunner
    from specify_cli.cli import app
    result = CliRunner().invoke(app, ['extension', 'list', '--json'], catch_exceptions=False)
    assert result.exit_code == 0
else:
    sys.argv = ['python -m specify_cli', 'extension', 'list', '--json']
    try:
        runpy.run_module('specify_cli', run_name='__main__')
    except SystemExit as error:
        assert error.code in (None, 0)
print(json.dumps(sorted(sys.modules)))
""".replace("ENTRY_POINT", repr(entry_point))

    loaded = _run_installed_probe(installed_python, external_root, bootstrap)

    assert loaded.isdisjoint(FORBIDDEN_CLIENT_MODULES)


def test_package_isolation_clean_wheel_daemon_handler_loads_no_catalog_stack(
    clean_installed_wheel: tuple[Path, Path],
) -> None:
    installed_python, external_root = clean_installed_wheel
    bootstrap = """
import json
import pathlib
import sys
import tempfile
from specify_cli.daemon import handle_installed_request
from specify_cli.daemon_protocol import ListRequest

before = set(sys.modules)
with tempfile.TemporaryDirectory(prefix='spec001-installed-handler-') as raw_directory:
    response = handle_installed_request(
        ListRequest(view='installed', output_json=True, discovery_start=pathlib.Path(raw_directory)),
        session_id='session-local',
        execution_mode='local-synthetic',
        inventory_loader=lambda _: [],
    )
assert response.exit_code == 0
print(json.dumps(sorted(set(sys.modules) - before)))
"""

    newly_loaded = _run_installed_probe(installed_python, external_root, bootstrap)

    assert newly_loaded.isdisjoint(FORBIDDEN_CLIENT_MODULES)


def test_import_boundary_packaged_daemon_surface_exists() -> None:
    package = SOURCE_ROOT / "specify_cli"
    for module_name in ("daemon.py", "daemon_client.py", "daemon_protocol.py"):
        assert (package / module_name).is_file()


def test_import_boundary_handshake_binds_peer_mode_repository_temp_and_audit() -> None:
    from specify_cli.daemon_protocol import Handshake, ProtocolError, validate_handshake

    expected = Handshake(
        protocol_version="1.0",
        peer_identity="owner",
        session_id="session-1",
        execution_mode="local-synthetic",
        repository_digest="a" * 64,
        temp_policy="owner-only",
        audit_head="b" * 64,
    )
    validate_handshake(expected, expected)

    for field_name in (
        "peer_identity",
        "session_id",
        "execution_mode",
        "repository_digest",
        "temp_policy",
        "audit_head",
    ):
        changed = expected.replaced(**{field_name: f"wrong-{field_name}"})
        with pytest.raises(ProtocolError, match=field_name.replace("_", " ")):
            validate_handshake(changed, expected)


@pytest.mark.skipif(os.name == "nt", reason="Unix socket policy")
def test_import_boundary_linux_xdg_and_uid_fallback_are_owner_only(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from specify_cli.daemon_client import linux_endpoint

    xdg = tmp_path / "xdg"
    xdg.mkdir(mode=0o700)
    xdg.chmod(0o700)
    uid = _current_uid()
    endpoint = linux_endpoint({"XDG_RUNTIME_DIR": str(xdg), "TMPDIR": str(tmp_path)}, uid)
    assert endpoint == xdg / "ama-specify" / "daemon.sock"
    assert stat.S_IMODE(endpoint.parent.stat().st_mode) == 0o700

    xdg.chmod(0o755)
    fallback = linux_endpoint({"XDG_RUNTIME_DIR": str(xdg), "TMPDIR": str(tmp_path)}, uid)
    assert fallback == tmp_path / f"ama-specify-{uid}" / "daemon.sock"
    assert stat.S_IMODE(fallback.parent.stat().st_mode) == 0o700


@pytest.mark.skipif(os.name != "nt", reason="Windows named-pipe policy")
def test_import_boundary_windows_pipe_uses_ctypes_sid_and_system_dacl() -> None:
    import specify_cli.daemon_client as daemon_client

    source = inspect.getsource(daemon_client)
    assert "ctypes" in source
    assert "kernel32" in source
    assert "advapi32" in source
    assert "SYSTEM" in source
    assert daemon_client.windows_pipe_name("S-1-5-21-owner").endswith("S-1-5-21-owner")


@pytest.mark.skipif(not hasattr(socket, "SO_PEERCRED"), reason="SO_PEERCRED unavailable")
def test_import_boundary_linux_peer_credentials_reject_other_uid() -> None:
    from specify_cli.daemon_client import validate_linux_peer_uid

    uid = _current_uid()
    validate_linux_peer_uid(uid, uid)
    with pytest.raises(PermissionError, match="peer uid"):
        validate_linux_peer_uid(uid + 1, uid)


def test_import_boundary_local_fixture_policy_rejects_live_and_bad_markers(tmp_path: Path) -> None:
    from specify_cli.extensions.inventory import ProjectContext, validate_local_fixture_access

    session_temp = tmp_path / "session"
    fixture_root = session_temp / "fixture"
    extensions_root = fixture_root / ".specify" / "extensions"
    extensions_root.mkdir(parents=True)
    marker = fixture_root / ".spec001-synthetic-fixture.json"
    marker.write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "feature": "001-extension-list",
                "fixture_id": "fixture-1",
                "source_digest": "a" * 64,
            }
        ),
        encoding="utf-8",
    )
    context = ProjectContext(fixture_root, extensions_root, None)

    validate_local_fixture_access(context, session_temp, "a" * 64, synthetic_mode=True)
    with pytest.raises(PermissionError, match="source digest"):
        validate_local_fixture_access(context, session_temp, "b" * 64, synthetic_mode=True)
    with pytest.raises(PermissionError, match="session temporary root"):
        validate_local_fixture_access(context, tmp_path / "other", "a" * 64, synthetic_mode=True)
    with pytest.raises(PermissionError, match="synthetic mode"):
        validate_local_fixture_access(context, session_temp, "a" * 64, synthetic_mode=False)


def test_import_boundary_runtime_audit_is_mode_bound_and_response_linked(tmp_path: Path) -> None:
    from specify_cli.daemon import LocalAuditJournal, handle_installed_request
    from specify_cli.daemon_protocol import ListRequest, validate_client_response

    journal = LocalAuditJournal(tmp_path / "audit.ndjson", session_id="session-1", execution_mode="local-synthetic")
    response = handle_installed_request(
        ListRequest(view="installed", output_json=True, discovery_start=tmp_path),
        session_id="session-1",
        execution_mode="local-synthetic",
        inventory_loader=lambda _: [],
        journal=journal,
    )

    validate_client_response(response)
    records = journal.read_records()
    assert [record["phase"] for record in records] == ["intent", "result"]
    assert {record["execution_mode"] for record in records} == {"local-synthetic"}
    assert records[1]["intent_event_id"] == records[0]["event_id"]


def test_import_boundary_fake_sovereign_controls_are_required_without_live_calls() -> None:
    from specify_cli.daemon import SovereignBoundary, validate_runtime_boundary

    valid = SovereignBoundary(
        vm_location="australiaeast",
        encrypted_temp=True,
        immutable_ledger=True,
        peer_authenticated=True,
        fake_transport=True,
    )
    validate_runtime_boundary("sovereign", valid)

    with pytest.raises(PermissionError, match="immutable ledger"):
        validate_runtime_boundary("sovereign", valid.replaced(immutable_ledger=False))
    with pytest.raises(PermissionError, match="cross-mode"):
        validate_runtime_boundary("local-synthetic", valid)
