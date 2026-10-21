from __future__ import annotations

import os
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import pytest
from typer.testing import CliRunner

# isort: split
import specify_cli.daemon as daemon
import specify_cli.daemon_client as client
from specify_cli.cli import app
from specify_cli.daemon_protocol import (
    PROTOCOL_VERSION,
    AuditReceipt,
    ClientResponse,
    Handshake,
    ListRequest,
    ProtocolError,
    decode_message,
    encode_message,
    validate_client_response,
    validate_handshake,
)


def _handshake(**changes: object) -> Handshake:
    values: dict[str, object] = {
        "protocol_version": PROTOCOL_VERSION,
        "peer_identity": "1000",
        "session_id": "session-1",
        "execution_mode": "local-synthetic",
        "repository_digest": "a" * 64,
        "temp_policy": "owner-only",
        "audit_head": "b" * 64,
    }
    values.update(changes)
    return Handshake(**values)  # type: ignore[arg-type]


def _response(*, exit_code: int = 0, stderr: str = "") -> ClientResponse:
    outcome = "succeeded" if exit_code == 0 else "failed"
    return ClientResponse(
        stdout="[]\n" if exit_code == 0 else "",
        stderr=stderr,
        exit_code=exit_code,
        audit=AuditReceipt(intent_event_id="intent-1", result_event_id="result-1", outcome=outcome),
    )


def _request(*, view: str = "installed", output_json: bool = True, start: Path | None = None) -> ListRequest:
    return ListRequest(view=view, output_json=output_json, discovery_start=start or Path("/synthetic"))


@pytest.mark.parametrize(
    ("factory", "message"),
    [
        (lambda: AuditReceipt("", "result", "succeeded"), "non-empty"),
        (lambda: AuditReceipt("same", "same", "succeeded"), "distinct"),
        (lambda: AuditReceipt("intent", "result", "unknown"), "outcome"),
        (lambda: ListRequest("installed", True, Path("."), protocol_version="2.0"), "protocol version"),
        (lambda: ListRequest("unknown", True, Path(".")), "view"),
        (lambda: ListRequest("installed", cast(bool, 1), Path(".")), "boolean"),
        (lambda: ListRequest("installed", True, cast(Path, "not-a-path")), "path"),
        (lambda: ClientResponse("", "", 0, None, protocol_version="2.0"), "protocol version"),
        (lambda: ClientResponse(cast(str, 1), "", 0, None), "streams"),
        (lambda: ClientResponse("", "", True, None), "exit code"),
        (lambda: ClientResponse("", "", 3, None), "exit code"),
        (lambda: _handshake(protocol_version="2.0"), "protocol version"),
        (lambda: _handshake(peer_identity=""), "peer identity"),
        (lambda: _handshake(session_id=""), "session id"),
        (lambda: _handshake(execution_mode="other"), "execution mode"),
        (lambda: _handshake(repository_digest="A" * 64), "repository digest"),
        (lambda: _handshake(audit_head="short"), "audit head"),
        (lambda: _handshake(temp_policy=""), "temp policy"),
    ],
)
def test_runtime_protocol_constructors_reject_invalid_values(factory: Any, message: str) -> None:
    with pytest.raises(ProtocolError, match=message):
        factory()


def test_runtime_protocol_mapping_round_trips_and_rejects_unknown_shapes(tmp_path: Path) -> None:
    request = _request(view="all", output_json=False, start=tmp_path)
    assert ListRequest.from_mapping(request.to_mapping()) == request
    with pytest.raises(ProtocolError, match="request fields"):
        ListRequest.from_mapping({**request.to_mapping(), "extra": True})
    with pytest.raises(ProtocolError, match="protocol version"):
        ListRequest.from_mapping({**request.to_mapping(), "protocol_version": 1})

    response = _response()
    assert ClientResponse.from_mapping(response.to_mapping()) == response
    without_audit = ClientResponse("", "", 0, None)
    assert ClientResponse.from_mapping(without_audit.to_mapping()) == without_audit
    with pytest.raises(ProtocolError, match="response fields"):
        ClientResponse.from_mapping({"stdout": ""})
    with pytest.raises(ProtocolError, match="audit receipt fields"):
        ClientResponse.from_mapping({**response.to_mapping(), "audit": {"outcome": "succeeded"}})


def test_runtime_protocol_validation_and_wire_format_fail_closed() -> None:
    expected = _handshake()
    validate_handshake(expected, expected)
    with pytest.raises(TypeError, match="unexpected handshake"):
        expected.replaced(unknown="value")
    for field_name in expected.__dataclass_fields__:
        changed = expected.replaced(**{field_name: "different"})
        with pytest.raises(ProtocolError, match=field_name.replace("_", " ")):
            validate_handshake(changed, expected)

    validate_client_response(_response())
    with pytest.raises(ProtocolError, match="linked audit"):
        validate_client_response(ClientResponse("", "", 0, None))
    with pytest.raises(ProtocolError, match="outcome"):
        validate_client_response(ClientResponse("", "", 1, AuditReceipt("i", "r", "succeeded")))

    for value in (_request(), _response(), expected):
        payload = encode_message(value)
        assert payload.endswith(b"\n")
        assert decode_message(payload)
    for payload, message in (
        (b"{}", "one line"),
        (b"{}\n{}\n", "one line"),
        (b"not-json\n", "valid JSON"),
        (b"[]\n", "object"),
    ):
        with pytest.raises(ProtocolError, match=message):
            decode_message(payload)


def test_runtime_client_directory_endpoint_and_platform_guards(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    uid = tmp_path.stat().st_uid
    missing = tmp_path / "missing"
    assert not client._validate_runtime_directory(missing, uid)
    file_path = tmp_path / "file"
    file_path.write_text("x", encoding="utf-8")
    assert not client._validate_runtime_directory(file_path, uid)

    runtime = tmp_path / "runtime"
    runtime.mkdir(mode=0o700)
    runtime.chmod(0o700)
    monkeypatch.setattr(
        client,
        "_validate_runtime_directory",
        lambda path, expected_uid: path in {runtime, runtime / "ama-specify"},
    )
    endpoint = client.linux_endpoint({"XDG_RUNTIME_DIR": str(runtime), "TMPDIR": str(tmp_path)}, uid)
    assert endpoint == runtime / "ama-specify" / "daemon.sock"
    assert endpoint.parent.is_dir()
    monkeypatch.setattr(client, "_validate_runtime_directory", lambda path, expected_uid: False)
    with pytest.raises(PermissionError, match="mode 0700"):
        client._ensure_runtime_directory(endpoint.parent, uid)

    with pytest.raises(ValueError, match="SID"):
        client.windows_pipe_name("")
    if os.name != "nt":
        with pytest.raises(RuntimeError, match="Windows-only"):
            client.current_windows_sid()
        with pytest.raises(RuntimeError, match="Windows-only"):
            client.windows_security_descriptor("owner")

    if os.name == "nt":
        monkeypatch.setattr(client, "current_windows_sid", lambda: "owner")
        assert client.endpoint_for_current_user({}) == r"\\.\pipe\ama-specify-owner"
    else:
        monkeypatch.setattr(os, "getuid", lambda: 1234)
        monkeypatch.setattr(client, "linux_endpoint", lambda environment, uid: Path(f"/{uid}/daemon.sock"))
        assert client.endpoint_for_current_user({}) == Path("/1234/daemon.sock")


def test_runtime_client_linux_fallback_peer_and_endpoint_dispatch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    ensured: list[tuple[Path, int]] = []

    def ensure(path: Path, uid: int) -> Path:
        ensured.append((path, uid))
        return path

    monkeypatch.setattr(client, "_validate_runtime_directory", lambda *_: False)
    monkeypatch.setattr(client, "_ensure_runtime_directory", ensure)
    endpoint = client.linux_endpoint({"XDG_RUNTIME_DIR": str(tmp_path / "bad"), "TMPDIR": str(tmp_path)}, 42)
    assert endpoint == tmp_path / "ama-specify-42" / "daemon.sock"
    assert ensured == [(tmp_path / "ama-specify-42", 42)]

    with pytest.raises(PermissionError, match="peer uid"):
        client.validate_linux_peer_uid(41, 42)

    expected = tmp_path / "daemon.sock"
    monkeypatch.setattr(os, "name", "posix")
    monkeypatch.setattr(os, "getuid", lambda: 42, raising=False)
    monkeypatch.setattr(client, "linux_endpoint", lambda environment, uid: expected)
    assert client.endpoint_for_current_user({}) == expected


def test_runtime_client_windows_identity_and_security_descriptor_use_native_apis(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import ctypes

    class Kernel32:
        def GetCurrentProcess(self) -> int:
            return 7

        def LocalFree(self, value: object) -> None:
            return None

        def CloseHandle(self, value: object) -> None:
            return None

    class Advapi32:
        def OpenProcessToken(self, process: object, access: int, token: object) -> bool:
            token._obj.value = 8  # type: ignore[attr-defined]
            return True

        def GetTokenInformation(
            self, token: object, token_class: int, buffer: object, size: object, returned: object
        ) -> bool:
            if buffer is None:
                returned._obj.value = ctypes.sizeof(ctypes.c_void_p)  # type: ignore[attr-defined]
            return True

        def ConvertSidToStringSidW(self, sid: object, text: object) -> bool:
            text._obj.value = "S-1-5-21-owner"  # type: ignore[attr-defined]
            return True

        def ConvertStringSecurityDescriptorToSecurityDescriptorW(
            self, sddl: object, revision: int, descriptor: object, size: object
        ) -> bool:
            descriptor._obj.value = 1234  # type: ignore[attr-defined]
            return True

    libraries = {"advapi32": Advapi32(), "kernel32": Kernel32()}
    monkeypatch.setattr(ctypes, "WinDLL", lambda name, **_: libraries[name])
    assert client.current_windows_sid() == "S-1-5-21-owner"
    assert client.windows_security_descriptor("S-1-5-21-owner") == 1234


def test_runtime_client_platform_guards_and_empty_native_results(monkeypatch: pytest.MonkeyPatch) -> None:
    import ctypes

    monkeypatch.setattr(os, "name", "posix")
    with pytest.raises(RuntimeError, match="Windows-only"):
        client.current_windows_sid()
    with pytest.raises(RuntimeError, match="Windows-only"):
        client.windows_security_descriptor("owner")
    monkeypatch.setattr(os, "name", "nt")

    class Kernel32:
        def GetCurrentProcess(self) -> int:
            return 7

        def LocalFree(self, value: object) -> None:
            return None

        def CloseHandle(self, value: object) -> None:
            return None

    class Advapi32:
        def OpenProcessToken(self, process: object, access: int, token: object) -> bool:
            token._obj.value = 8  # type: ignore[attr-defined]
            return True

        def GetTokenInformation(
            self, token: object, token_class: int, buffer: object, size: object, returned: object
        ) -> bool:
            if buffer is None:
                returned._obj.value = ctypes.sizeof(ctypes.c_void_p)  # type: ignore[attr-defined]
            return True

        def ConvertSidToStringSidW(self, sid: object, text: object) -> bool:
            return True

        def ConvertStringSecurityDescriptorToSecurityDescriptorW(
            self, sddl: object, revision: int, descriptor: object, size: object
        ) -> bool:
            return True

    libraries = {"advapi32": Advapi32(), "kernel32": Kernel32()}
    monkeypatch.setattr(ctypes, "WinDLL", lambda name, **_: libraries[name])
    with pytest.raises(RuntimeError, match="no value"):
        client.current_windows_sid()
    with pytest.raises(RuntimeError, match="no value"):
        client.windows_security_descriptor("owner")


def test_runtime_client_peer_credentials_and_posix_startup_lock(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import struct
    import sys

    monkeypatch.setattr(socket, "SO_PEERCRED", 17, raising=False)
    connection = SimpleNamespace(
        getsockopt=lambda level, option, size: struct.pack("3i", 1, 42, 3),
    )
    assert client._peer_uid(cast(socket.socket, connection)) == 42

    lock_calls: list[int] = []
    fake_fcntl = SimpleNamespace(LOCK_EX=1, LOCK_UN=2, flock=lambda handle, operation: lock_calls.append(operation))
    monkeypatch.setitem(sys.modules, "fcntl", fake_fcntl)
    monkeypatch.setattr(os, "name", "posix")
    windows_path = type(tmp_path)
    monkeypatch.setattr(client, "Path", lambda value: windows_path(value))
    monkeypatch.setattr(tempfile, "gettempdir", lambda: str(tmp_path))
    with client.startup_lock(tmp_path / "daemon.sock"):
        pass
    assert lock_calls == [1, 2]


@pytest.mark.parametrize("failure", ["open", "token", "sid", "descriptor"])
def test_runtime_client_windows_native_api_failures(failure: str, monkeypatch: pytest.MonkeyPatch) -> None:
    import ctypes

    class Kernel32:
        def GetCurrentProcess(self) -> int:
            return 7

        def LocalFree(self, value: object) -> None:
            return None

        def CloseHandle(self, value: object) -> None:
            return None

    class Advapi32:
        def OpenProcessToken(self, process: object, access: int, token: object) -> bool:
            token._obj.value = 8  # type: ignore[attr-defined]
            return failure != "open"

        def GetTokenInformation(
            self, token: object, token_class: int, buffer: object, size: object, returned: object
        ) -> bool:
            if buffer is None:
                returned._obj.value = ctypes.sizeof(ctypes.c_void_p)  # type: ignore[attr-defined]
                return True
            return failure != "token"

        def ConvertSidToStringSidW(self, sid: object, text: object) -> bool:
            if failure != "sid":
                text._obj.value = "S-1-5-21-owner"  # type: ignore[attr-defined]
            return failure != "sid"

        def ConvertStringSecurityDescriptorToSecurityDescriptorW(
            self, sddl: object, revision: int, descriptor: object, size: object
        ) -> bool:
            if failure != "descriptor":
                descriptor._obj.value = 1234  # type: ignore[attr-defined]
            return failure != "descriptor"

    libraries = {"advapi32": Advapi32(), "kernel32": Kernel32()}
    monkeypatch.setattr(ctypes, "WinDLL", lambda name, **_: libraries[name])
    if failure == "descriptor":
        with pytest.raises(OSError):
            client.windows_security_descriptor("S-1-5-21-owner")
    else:
        with pytest.raises(OSError):
            client.current_windows_sid()


def test_runtime_client_peer_launch_lock_and_stream_behaviors(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    credentials = __import__("struct").pack("3i", 10, 20, 30)
    connection = SimpleNamespace(getsockopt=lambda *args: credentials)
    if hasattr(socket, "SO_PEERCRED"):
        assert client._peer_uid(cast(socket.socket, connection)) == 20
    else:
        with pytest.raises(RuntimeError, match="SO_PEERCRED"):
            client._peer_uid(cast(socket.socket, connection))

    validate_calls: list[tuple[int, int]] = []
    monkeypatch.setattr(
        client,
        "validate_linux_peer_uid",
        lambda actual, expected: validate_calls.append((actual, expected)),
    )
    client.validate_linux_peer_uid(4, 4)
    assert validate_calls == [(4, 4)]

    with client.startup_lock(tmp_path / "daemon.sock"):
        pass

    popen_calls: list[tuple[object, dict[str, object]]] = []

    def fake_popen(arguments: object, **kwargs: object) -> object:
        popen_calls.append((arguments, kwargs))
        return object()

    monkeypatch.setattr(subprocess, "Popen", fake_popen)
    result = client.launch_daemon(tmp_path / "daemon.sock", {"EXTRA_BINDING": "yes"})
    assert result is not None
    arguments, options = popen_calls[0]
    assert arguments == [sys.executable, "-m", "specify_cli.daemon", "--endpoint", str(tmp_path / "daemon.sock")]
    assert options["env"]["EXTRA_BINDING"] == "yes"  # type: ignore[index]

    assert client._read_line(SimpleNamespace(readline=lambda: b"ok\n")) == b"ok\n"
    for value in (b"", "text"):
        with pytest.raises(ProtocolError, match="closed"):
            client._read_line(SimpleNamespace(readline=lambda value=value: value))


class _DuplexStream:
    def __init__(self, payloads: list[bytes]) -> None:
        self.payloads = payloads
        self.writes: list[bytes] = []

    def __enter__(self) -> _DuplexStream:
        return self

    def __exit__(self, *_: object) -> None:
        return None

    def readline(self) -> bytes:
        return self.payloads.pop(0)

    def write(self, payload: bytes) -> int:
        self.writes.append(payload)
        return len(payload)


class _FakeConnection:
    def __init__(self, stream: _DuplexStream) -> None:
        self.stream = stream
        self.connected_to: str | None = None

    def __enter__(self) -> _FakeConnection:
        return self

    def __exit__(self, *_: object) -> None:
        return None

    def connect(self, endpoint: str) -> None:
        self.connected_to = endpoint

    def makefile(self, *_: object, **__: object) -> _DuplexStream:
        return self.stream


def test_runtime_client_unix_exchange_and_startup_dispatch(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    endpoint = tmp_path / "daemon.sock"
    stream = _DuplexStream([encode_message(_handshake()), encode_message(_response())])
    connection = _FakeConnection(stream)
    monkeypatch.setattr(socket, "AF_UNIX", 1, raising=False)
    monkeypatch.setattr(socket, "socket", lambda *_: connection)
    monkeypatch.setattr(client, "_peer_uid", lambda _: 1000)
    monkeypatch.setattr(os, "getuid", lambda: 1000, raising=False)
    handshake, response = client._exchange_unix(endpoint, _request())
    assert (handshake, response) == (_handshake(), _response())
    assert connection.connected_to == str(endpoint)
    assert stream.writes == [encode_message(_request())]

    endpoint.write_text("not-a-socket", encoding="utf-8")
    monkeypatch.setattr(Path, "is_symlink", lambda path: path == endpoint)
    with pytest.raises(PermissionError, match="symlink"):
        client._exchange_unix(endpoint, _request())

    monkeypatch.setattr(client, "_exchange_unix", lambda path, request: (_handshake(), _response()))
    assert client._connect_with_startup(endpoint, _request(), {}) == (_handshake(), _response())


def test_runtime_client_windows_exchange_and_startup_paths(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    stream = _DuplexStream([encode_message(_handshake()), encode_message(_response())])
    monkeypatch.setattr("builtins.open", lambda *args, **kwargs: stream)
    handshake, response = client._exchange_windows(r"\\.\pipe\ama-specify-owner", _request())
    assert handshake == _handshake()
    assert response == _response()
    assert stream.writes == [encode_message(_request())]

    direct_calls = 0

    def direct_exchange(endpoint: str, request: ListRequest) -> tuple[Handshake, ClientResponse]:
        nonlocal direct_calls
        direct_calls += 1
        return _handshake(), _response()

    monkeypatch.setattr(client, "_exchange_windows", direct_exchange)
    assert client._connect_with_startup("pipe", _request(), {}) == (_handshake(), _response())
    assert direct_calls == 1

    attempts = 0

    def delayed_exchange(endpoint: str, request: ListRequest) -> tuple[Handshake, ClientResponse]:
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise FileNotFoundError
        return _handshake(), _response()

    launches: list[str] = []
    monkeypatch.setattr(client, "_exchange_windows", delayed_exchange)
    monkeypatch.setattr(client, "launch_daemon", lambda endpoint, environment: launches.append(str(endpoint)))
    monkeypatch.setattr(time, "sleep", lambda _: None)
    assert client._connect_with_startup("pipe", _request(), {}) == (_handshake(), _response())
    assert launches == ["pipe"]

    monkeypatch.setattr(client, "_exchange_windows", lambda *_: (_ for _ in ()).throw(ConnectionRefusedError()))
    monotonic = iter((0.0, 6.0))
    monkeypatch.setattr(time, "monotonic", lambda: next(monotonic))
    with pytest.raises(RuntimeError, match="timed out"):
        client._connect_with_startup("pipe", _request(), {})


def test_runtime_client_request_requires_binding_and_validates_exchange(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    for name in list(os.environ):
        if name.startswith("SPEC001_"):
            monkeypatch.delenv(name, raising=False)
    with pytest.raises(RuntimeError, match="binding is incomplete"):
        client.request_extension_list(view="installed", output_json=True)

    environment = {
        "SPEC001_SESSION_ID": "session-1",
        "SPEC001_EXECUTION_MODE": "local-synthetic",
        "SPEC001_REPOSITORY_DIGEST": "a" * 64,
        "SPEC001_TEMP_POLICY": "owner-only",
        "SPEC001_AUDIT_HEAD": "b" * 64,
    }
    for name, value in environment.items():
        monkeypatch.setenv(name, value)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(client, "endpoint_for_current_user", lambda _: tmp_path / "daemon.sock")
    monkeypatch.setattr(os, "getuid", lambda: 1000, raising=False)
    monkeypatch.setattr(client, "current_windows_sid", lambda: "1000")
    captured: list[ListRequest] = []

    def exchange(endpoint: Path | str, request: ListRequest, values: object) -> tuple[Handshake, ClientResponse]:
        captured.append(request)
        return _handshake(), _response()

    monkeypatch.setattr(client, "_connect_with_startup", exchange)
    assert client.request_extension_list(view="all", output_json=False) == _response()
    assert captured == [_request(view="all", output_json=False, start=tmp_path)]

    monkeypatch.setattr(client, "_connect_with_startup", lambda *_: (_handshake(audit_head="c" * 64), _response()))
    with pytest.raises(ProtocolError, match="audit head mismatch"):
        client.request_extension_list(view="installed", output_json=True)


@pytest.mark.parametrize(
    ("mode", "boundary", "message"),
    [
        ("invalid", daemon.LocalBoundary(True, True, True, True), "execution mode"),
        ("local-synthetic", daemon.SovereignBoundary("australiaeast", True, True, True), "cross-mode"),
        ("local-synthetic", daemon.LocalBoundary(False, True, True, True), "owner-only"),
        ("local-synthetic", daemon.LocalBoundary(True, False, True, True), "authenticated"),
        ("local-synthetic", daemon.LocalBoundary(True, True, False, True), "synthetic"),
        ("local-synthetic", daemon.LocalBoundary(True, True, True, False), "ephemeral"),
        ("sovereign", daemon.LocalBoundary(True, True, True, True), "cross-mode"),
        ("sovereign", daemon.SovereignBoundary("westus", True, True, True), "Australian"),
        ("sovereign", daemon.SovereignBoundary("australiaeast", False, True, True), "encrypted"),
        ("sovereign", daemon.SovereignBoundary("australiaeast", True, False, True), "immutable"),
        ("sovereign", daemon.SovereignBoundary("australiaeast", True, True, False), "authenticated"),
    ],
)
def test_runtime_daemon_boundary_failures(
    mode: str, boundary: daemon.LocalBoundary | daemon.SovereignBoundary, message: str
) -> None:
    with pytest.raises(PermissionError, match=message):
        daemon.validate_runtime_boundary(mode, boundary)


def test_runtime_daemon_journal_and_audit_failure_behavior(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="local-synthetic only"):
        daemon.LocalAuditJournal(tmp_path / "bad.ndjson", session_id="session", execution_mode="sovereign")
    journal = daemon.LocalAuditJournal(
        tmp_path / "journal" / "audit.ndjson", session_id="session", execution_mode="local-synthetic"
    )
    assert journal.read_records() == []
    with pytest.raises(ValueError, match="phase"):
        journal.append("other", {})
    intent = journal.append("intent", {"event_id": "intent"})
    result = journal.append("result", {"event_id": "result", "intent_event_id": "intent"})
    assert result["previous_event_digest"] == intent["event_digest"]
    assert [record["sequence"] for record in journal.read_records()] == [1, 2]

    journal.path.write_bytes(b"{}")
    with pytest.raises(RuntimeError, match="LF terminated"):
        journal.read_records()
    journal.path.write_bytes(b'{"z":1,"a":2}\n')
    with pytest.raises(RuntimeError, match="canonical"):
        journal.read_records()

    response = daemon.handle_installed_request(
        _request(),
        session_id="session",
        execution_mode="local-synthetic",
        inventory_loader=lambda _: (_ for _ in ()).throw(RuntimeError("inventory failed")),
    )
    assert response.exit_code == 1
    assert response.stderr == "inventory failed\n"
    validate_client_response(response)


def test_runtime_daemon_valid_boundaries_memory_journal_and_posix_file_lock(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import sys

    daemon.validate_runtime_boundary("local-synthetic", daemon.LocalBoundary(True, True, True, True))
    daemon.validate_runtime_boundary("sovereign", daemon.SovereignBoundary("australiaeast", True, True, True))
    memory = daemon._MemoryAuditJournal("session", "local-synthetic")
    assert memory.append("intent", {"event_id": "event"}) == {
        "event_id": "event",
        "execution_mode": "local-synthetic",
        "phase": "intent",
        "session_id": "session",
    }

    lock_calls: list[int] = []
    fake_fcntl = SimpleNamespace(LOCK_EX=1, LOCK_UN=2, flock=lambda handle, operation: lock_calls.append(operation))
    monkeypatch.setitem(sys.modules, "fcntl", fake_fcntl)
    monkeypatch.setattr(os, "name", "posix")
    journal = daemon.LocalAuditJournal(
        tmp_path / "posix" / "audit.ndjson",
        session_id="session",
        execution_mode="local-synthetic",
    )
    journal.append("intent", {"event_id": "intent"})
    assert lock_calls == [1, 2]


def test_runtime_daemon_request_handlers_cover_dispatch_and_fallback(tmp_path: Path) -> None:
    with pytest.raises(PermissionError, match="execution mode"):
        daemon.handle_installed_request(
            _request(), session_id="session", execution_mode="invalid", inventory_loader=lambda _: []
        )
    with pytest.raises(PermissionError, match="execution mode"):
        daemon.handle_extension_request(
            _request(),
            session_id="session",
            execution_mode="invalid",
            installed_loader=lambda _: [],
            catalog_loader=lambda _: object(),
        )

    catalog_calls: list[Path] = []
    installed = daemon.handle_extension_request(
        _request(start=tmp_path),
        session_id="session",
        execution_mode="local-synthetic",
        installed_loader=lambda _: [],
        catalog_loader=lambda path: catalog_calls.append(path),
    )
    assert installed.stdout == "[]\n"
    assert catalog_calls == []

    for view, expected in (("available", "[]\n"), ("all", "[]\n")):
        fallback = daemon.handle_extension_request(
            _request(view=view, start=tmp_path),
            session_id="session",
            execution_mode="local-synthetic",
            installed_loader=lambda _: [],
            catalog_loader=lambda _: SimpleNamespace(records=(), warning="catalog unavailable"),
        )
        assert fallback.stdout == expected
        assert fallback.stderr == "catalog unavailable\n"

    success = daemon.handle_extension_request(
        _request(view="available", start=tmp_path),
        session_id="session",
        execution_mode="local-synthetic",
        installed_loader=lambda _: [],
        catalog_loader=lambda _: SimpleNamespace(records=(), warning=None),
    )
    assert success.exit_code == 0
    assert success.stdout == "[]\n"

    invalid = daemon.handle_extension_request(
        _request(view="all", start=tmp_path),
        session_id="session",
        execution_mode="local-synthetic",
        installed_loader=lambda _: [],
        catalog_loader=lambda _: SimpleNamespace(records=[], warning=1),
    )
    assert invalid.exit_code == 1
    assert "catalog loader result is invalid" in invalid.stderr


def test_runtime_daemon_parse_default_loader_handshake_and_main(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    request = _request(start=tmp_path)
    assert daemon._parse_request(encode_message(request)) == request
    assert daemon._default_inventory_loader(tmp_path) == []

    with pytest.raises(RuntimeError, match="binding is incomplete"):
        daemon._handshake_from_environment({})
    environment = {
        "SPEC001_SESSION_ID": "session-1",
        "SPEC001_EXECUTION_MODE": "local-synthetic",
        "SPEC001_REPOSITORY_DIGEST": "a" * 64,
        "SPEC001_TEMP_POLICY": "owner-only",
        "SPEC001_AUDIT_HEAD": "b" * 64,
        "SPEC001_PEER_IDENTITY": "1000",
    }
    assert daemon._handshake_from_environment(environment) == _handshake()

    served: list[tuple[Path, Handshake]] = []
    monkeypatch.setattr(daemon, "_handshake_from_environment", lambda _: _handshake())
    monkeypatch.setattr(daemon, "_serve_unix", lambda endpoint, handshake: served.append((endpoint, handshake)))
    monkeypatch.setattr(os, "name", "posix")
    assert daemon.main(["--endpoint", str(tmp_path / "daemon.sock")]) == 0
    assert len(served) == 1
    assert str(served[0][0]).endswith("daemon.sock")
    assert served[0][1] == _handshake()

    monkeypatch.setattr(os, "name", "nt")
    with pytest.raises(RuntimeError, match="named-pipe"):
        daemon.main(["--endpoint", "pipe"])


def test_runtime_daemon_default_loader_rejects_live_project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import specify_cli.extensions.inventory as inventory

    monkeypatch.setattr(
        inventory,
        "discover_project",
        lambda _: SimpleNamespace(project_root=tmp_path),
    )
    with pytest.raises(PermissionError, match="live extension inventory"):
        daemon._default_inventory_loader(tmp_path)


def test_runtime_daemon_serves_one_fake_unix_request(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    endpoint = tmp_path / "runtime" / "daemon.sock"
    endpoint.parent.mkdir(parents=True)
    endpoint.write_text("stale", encoding="utf-8")
    request = _request(start=tmp_path)
    stream = _DuplexStream([encode_message(request)])
    connection = _FakeConnection(stream)

    class FakeServer:
        def __init__(self) -> None:
            self.accepted = False

        def __enter__(self) -> FakeServer:
            return self

        def __exit__(self, *_: object) -> None:
            return None

        def bind(self, value: str) -> None:
            Path(value).touch()

        def listen(self) -> None:
            return None

        def accept(self) -> tuple[_FakeConnection, object]:
            if self.accepted:
                raise StopIteration
            self.accepted = True
            return connection, object()

    server = FakeServer()
    monkeypatch.setattr(socket, "AF_UNIX", 1, raising=False)
    monkeypatch.setattr(socket, "socket", lambda *_: server)
    monkeypatch.setattr(
        daemon,
        "LocalAuditJournal",
        lambda *args, **kwargs: daemon._MemoryAuditJournal("session-1", "local-synthetic"),
    )
    with pytest.raises(StopIteration):
        daemon._serve_unix(endpoint, _handshake())

    assert endpoint.exists()
    assert len(stream.writes) == 2
    assert Handshake(**decode_message(stream.writes[0])) == _handshake()
    validate_client_response(ClientResponse.from_mapping(decode_message(stream.writes[1])))


@pytest.mark.parametrize(
    ("arguments", "expected_error"),
    [
        (
            ["extension", "list", "--available", "--all", "--json"],
            '{"error":"--available and --all are mutually exclusive"}\n',
        ),
        (["extension", "list", "--available", "--all"], "--available and --all are mutually exclusive"),
    ],
)
def test_runtime_cli_rejects_conflicting_views(arguments: list[str], expected_error: str) -> None:
    result = CliRunner().invoke(app, arguments)
    assert result.exit_code == 2
    assert expected_error in result.stderr
    if "--json" in arguments:
        assert result.stdout == ""


def test_runtime_cli_delegates_daemon_failures_and_response_streams(monkeypatch: pytest.MonkeyPatch) -> None:
    import specify_cli.daemon_client as daemon_client

    monkeypatch.setattr(daemon_client, "request_extension_list", lambda **_: _response(exit_code=1, stderr="blocked\n"))
    result = CliRunner().invoke(app, ["extension", "list"])
    assert result.exit_code == 1
    assert result.stdout == ""
    assert result.stderr == "blocked\n"

    monkeypatch.setattr(
        daemon_client,
        "request_extension_list",
        lambda **_: (_ for _ in ()).throw(RuntimeError("offline")),
    )
    human = CliRunner().invoke(app, ["extension", "list"])
    assert human.exit_code == 1
    assert human.stderr == "offline\n"
    json_result = CliRunner().invoke(app, ["extension", "list", "--json"])
    assert json_result.exit_code == 1
    assert json_result.stdout == ""
    assert json_result.stderr == '{"error":"offline"}\n'
