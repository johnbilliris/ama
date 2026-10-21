from __future__ import annotations

import hashlib
import os
import socket
import stat
import struct
import subprocess
import sys
import tempfile
import time
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from pathlib import Path

from specify_cli.daemon_protocol import (
    ClientResponse,
    Handshake,
    ListRequest,
    ProtocolError,
    decode_message,
    encode_message,
    validate_client_response,
    validate_handshake,
)

_SOCKET_MODE = 0o600
_DIRECTORY_MODE = 0o700


def _validate_runtime_directory(path: Path, uid: int) -> bool:
    try:
        metadata = path.stat(follow_symlinks=False)
    except (FileNotFoundError, OSError):
        return False
    return not path.is_symlink() and metadata.st_uid == uid and stat.S_IMODE(metadata.st_mode) == _DIRECTORY_MODE


def _ensure_runtime_directory(path: Path, uid: int) -> Path:
    try:
        path.mkdir(mode=_DIRECTORY_MODE, parents=True, exist_ok=False)
    except FileExistsError:
        pass
    if not _validate_runtime_directory(path, uid):
        raise PermissionError("runtime directory must be current-UID owned, non-symlink, and mode 0700")
    return path


def linux_endpoint(environment: Mapping[str, str], uid: int) -> Path:
    runtime_value = environment.get("XDG_RUNTIME_DIR")
    if runtime_value:
        runtime = Path(runtime_value)
        if _validate_runtime_directory(runtime, uid):
            return _ensure_runtime_directory(runtime / "ama-specify", uid) / "daemon.sock"
    temporary_root = Path(environment.get("TMPDIR", tempfile.gettempdir()))
    return _ensure_runtime_directory(temporary_root / f"ama-specify-{uid}", uid) / "daemon.sock"


def validate_linux_peer_uid(peer_uid: int, expected_uid: int) -> None:
    if peer_uid != expected_uid:
        raise PermissionError("peer uid does not match the current uid")


def _peer_uid(connection: socket.socket) -> int:
    if not hasattr(socket, "SO_PEERCRED"):
        raise RuntimeError("SO_PEERCRED is required for Unix daemon authentication")
    credentials = connection.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, struct.calcsize("3i"))
    _, uid, _ = struct.unpack("3i", credentials)
    return int(uid)


def windows_pipe_name(sid: str) -> str:
    if not sid:
        raise ValueError("current SID is required")
    return rf"\\.\pipe\ama-specify-{sid}"


def current_windows_sid() -> str:
    if os.name != "nt":
        raise RuntimeError("Windows SID lookup is Windows-only")
    import ctypes
    from ctypes import wintypes

    advapi32 = ctypes.WinDLL("advapi32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    token = wintypes.HANDLE()
    if not advapi32.OpenProcessToken(kernel32.GetCurrentProcess(), 0x0008, ctypes.byref(token)):
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        size = wintypes.DWORD()
        advapi32.GetTokenInformation(token, 1, None, 0, ctypes.byref(size))
        buffer = ctypes.create_string_buffer(size.value)
        if not advapi32.GetTokenInformation(token, 1, buffer, size, ctypes.byref(size)):
            raise ctypes.WinError(ctypes.get_last_error())
        sid_pointer = ctypes.cast(buffer, ctypes.POINTER(ctypes.c_void_p))[0]
        text = wintypes.LPWSTR()
        if not advapi32.ConvertSidToStringSidW(sid_pointer, ctypes.byref(text)):
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            value = text.value
            if value is None:
                raise RuntimeError("current SID conversion returned no value")
            return value
        finally:
            kernel32.LocalFree(text)
    finally:
        kernel32.CloseHandle(token)


def windows_security_descriptor(sid: str) -> int:
    if os.name != "nt":
        raise RuntimeError("Windows security descriptors are Windows-only")
    import ctypes
    from ctypes import wintypes

    advapi32 = ctypes.WinDLL("advapi32", use_last_error=True)
    descriptor = ctypes.c_void_p()
    sddl = f"D:P(A;;GA;;;SYSTEM)(A;;GA;;;{sid})"
    if not advapi32.ConvertStringSecurityDescriptorToSecurityDescriptorW(
        wintypes.LPWSTR(sddl), 1, ctypes.byref(descriptor), None
    ):
        raise ctypes.WinError(ctypes.get_last_error())
    value = descriptor.value
    if value is None:
        raise RuntimeError("security descriptor conversion returned no value")
    return int(value)


def endpoint_for_current_user(environment: Mapping[str, str] | None = None) -> Path | str:
    values = os.environ if environment is None else environment
    if os.name == "nt":
        return windows_pipe_name(current_windows_sid())
    return linux_endpoint(values, os.getuid())  # type: ignore[attr-defined]


@contextmanager
def startup_lock(endpoint: Path | str) -> Iterator[None]:
    identity = hashlib.sha256(str(endpoint).encode("utf-8")).hexdigest()[:24]
    lock_root = Path(tempfile.gettempdir()) / "ama-specify-locks"
    lock_root.mkdir(mode=_DIRECTORY_MODE, exist_ok=True)
    if os.name != "nt":
        lock_root.chmod(_DIRECTORY_MODE)
    lock_path = lock_root / f"{identity}.lock"
    with lock_path.open("a+b") as handle:
        if os.name == "nt":
            import msvcrt

            handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_LOCK, 1)
        else:
            import fcntl

            os.chmod(lock_path, _SOCKET_MODE)
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)  # type: ignore[attr-defined]
        try:
            yield
        finally:
            if os.name == "nt":
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)  # type: ignore[attr-defined]


def launch_daemon(endpoint: Path | str, environment: Mapping[str, str] | None = None) -> subprocess.Popen[bytes]:
    child_environment = os.environ.copy()
    if environment is not None:
        child_environment.update(environment)
    return subprocess.Popen(
        [sys.executable, "-m", "specify_cli.daemon", "--endpoint", str(endpoint)],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env=child_environment,
        close_fds=True,
    )


def _read_line(stream: object) -> bytes:
    payload = stream.readline()  # type: ignore[attr-defined]
    if not isinstance(payload, bytes) or not payload:
        raise ProtocolError("daemon closed the IPC channel")
    return payload


def _exchange_unix(endpoint: Path, request: ListRequest) -> tuple[Handshake, ClientResponse]:
    if endpoint.is_symlink():
        raise PermissionError("daemon socket must not be a symlink")
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection:  # type: ignore[attr-defined]
        connection.connect(str(endpoint))
        validate_linux_peer_uid(_peer_uid(connection), os.getuid())  # type: ignore[attr-defined]
        with connection.makefile("rwb", buffering=0) as stream:
            stream.write(encode_message(request))
            handshake = Handshake(**decode_message(_read_line(stream)))
            response = ClientResponse.from_mapping(decode_message(_read_line(stream)))
    return handshake, response


def _exchange_windows(endpoint: str, request: ListRequest) -> tuple[Handshake, ClientResponse]:
    with open(endpoint, "r+b", buffering=0) as stream:
        stream.write(encode_message(request))
        handshake = Handshake(**decode_message(_read_line(stream)))
        response = ClientResponse.from_mapping(decode_message(_read_line(stream)))
    return handshake, response


def _expected_handshake(environment: Mapping[str, str]) -> Handshake:
    peer_identity = current_windows_sid() if os.name == "nt" else str(os.getuid())  # type: ignore[attr-defined]
    return Handshake(
        protocol_version="1.0",
        peer_identity=peer_identity,
        session_id=environment["SPEC001_SESSION_ID"],
        execution_mode=environment["SPEC001_EXECUTION_MODE"],
        repository_digest=environment["SPEC001_REPOSITORY_DIGEST"],
        temp_policy=environment["SPEC001_TEMP_POLICY"],
        audit_head=environment["SPEC001_AUDIT_HEAD"],
    )


def _connect_with_startup(
    endpoint: Path | str,
    request: ListRequest,
    environment: Mapping[str, str],
) -> tuple[Handshake, ClientResponse]:
    def exchange() -> tuple[Handshake, ClientResponse]:
        if isinstance(endpoint, str):
            return _exchange_windows(endpoint, request)
        return _exchange_unix(endpoint, request)

    try:
        return exchange()
    except (FileNotFoundError, ConnectionRefusedError):
        with startup_lock(endpoint):
            launch_daemon(endpoint, environment)
            deadline = time.monotonic() + 5.0
            while True:
                try:
                    return exchange()
                except (FileNotFoundError, ConnectionRefusedError):
                    if time.monotonic() >= deadline:
                        raise RuntimeError("daemon startup timed out") from None
                    time.sleep(0.01)


def request_extension_list(*, view: str, output_json: bool) -> ClientResponse:
    environment = os.environ
    required = {
        "SPEC001_SESSION_ID",
        "SPEC001_EXECUTION_MODE",
        "SPEC001_REPOSITORY_DIGEST",
        "SPEC001_TEMP_POLICY",
        "SPEC001_AUDIT_HEAD",
    }
    missing = sorted(required - set(environment))
    if missing:
        raise RuntimeError(f"daemon binding is incomplete: {', '.join(missing)}")
    endpoint = endpoint_for_current_user(environment)
    request = ListRequest(view=view, output_json=output_json, discovery_start=Path.cwd())
    handshake, response = _connect_with_startup(endpoint, request, environment)
    validate_handshake(handshake, _expected_handshake(environment))
    validate_client_response(response)
    return response
