from __future__ import annotations

import argparse
import getpass
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import re
import signal
import subprocess
import sys
import tempfile
import time
from typing import Mapping, Sequence
import uuid

from dispatcher_selfcheck_cases import EXPECTED_OPTIONS, SelfCheckApi, run_self_checks
from protected_state import (
    BOOTSTRAP_PATHS,
    PROTECTED_PATHS,
    capture_protected_state,
    ensure_owner_only_directory,
    protected_bootstrap_manifest,
    session_manifest_digest,
)
from root_regression import (
    RootRegressionBaseline,
    RuntimeBinding,
    capture_repository_cache_state,
    compare_repository_cache_state,
    execute_root_regression,
    root_regression_self_check,
)


EXECUTION_MODES = ("local-synthetic", "sovereign")
MAX_RECORDS = 49_000
LAST_ORDINARY_SEQUENCE = 48_998
_DIGEST = re.compile(r"^[0-9a-f]{64}$")
_SESSION_ROOT = Path(tempfile.gettempdir()) / f"spec001-extension-list-{getpass.getuser()}"


def canonical_json(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")


def validate_execution_mode(value: str) -> None:
    if value not in EXECUTION_MODES:
        raise ValueError("unsupported execution mode")


def _command_output(*command: str) -> str:
    return subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True).stdout.strip()


def validate_toolchain() -> dict[str, str]:
    if sys.version_info < (3, 12):
        raise RuntimeError("Python 3.12 or later is required")
    if importlib.util.find_spec("pytest") is None:
        raise RuntimeError("root pytest is not provisioned")
    git_version = _command_output("git", "--version")
    uv_version = _command_output("uv", "--version")
    match = re.search(r"uv (\d+)\.(\d+)\.(\d+)", uv_version)
    if not match or not ((0, 11, 0) <= tuple(map(int, match.groups())) < (1, 0, 0)):
        raise RuntimeError("uv version must be >=0.11,<1")
    if not git_version.startswith("git version "):
        raise RuntimeError("Git is unavailable")
    return {
        "python_executable": str(Path(sys.executable).resolve()),
        "python_version": platform.python_version(),
        "uv_version": uv_version,
        "os": platform.platform(),
        "architecture": platform.machine(),
    }


def validate_sovereign_environment(environment: Mapping[str, str]) -> None:
    forbidden = {
        name
        for name in environment
        if name in {"SPEC001_TEST_MODE", "SPEC001_EXTERNAL_TRANSPORT"}
        or name.startswith("SPEC001_")
        or name.startswith("SPECIFY_CLI_")
    }
    if forbidden:
        raise ValueError("sovereign mode rejects test and unknown feature controls")


def validate_guarded_child(command: Sequence[str], environment: Mapping[str, str]) -> None:
    if not command:
        raise ValueError("guarded child command is required")
    if tuple(command[:2]) != ("uv", "run"):
        return
    if environment.get("UV_FROZEN") != "1":
        raise ValueError("guarded uv run requires UV_FROZEN=1")
    is_pytest = "pytest" in command
    is_mypy = "mypy" in command
    project_selected = "--project" in command
    if is_pytest and environment.get("PYTEST_ADDOPTS") != "-pno:cacheprovider":
        raise ValueError("guarded pytest requires cache-provider denial")
    if is_mypy:
        cache = environment.get("MYPY_CACHE_DIR")
        if not cache or Path(cache).resolve().is_relative_to(Path.cwd().resolve()):
            raise ValueError("guarded mypy requires an external cache directory")
    if project_selected and any(tool in command for tool in ("pytest", "mypy", "ruff")):
        if "--extra" not in command or command[command.index("--extra") + 1] != "dev":
            raise ValueError("package quality child requires --extra dev")
    if is_pytest and not project_selected and "--no-sync" not in command:
        raise ValueError("root pytest child requires --no-sync")


def validate_fixture_access(project_root: Path | None, session_root: Path, environment: Mapping[str, str]) -> None:
    if project_root is None:
        return
    if environment.get("SPEC001_TEST_MODE") != "synthetic":
        raise PermissionError("local data-bearing access requires synthetic mode")
    resolved_session = session_root.resolve(strict=True)
    resolved_project = project_root.resolve(strict=True)
    if project_root.is_symlink() or not resolved_project.is_relative_to(resolved_session):
        raise PermissionError("fixture root must be beneath owner-only session temporary storage")
    marker_path = resolved_project / ".spec001-synthetic-fixture.json"
    if not marker_path.is_file() or marker_path.is_symlink():
        raise PermissionError("closed synthetic fixture marker is required")
    marker = json.loads(marker_path.read_text(encoding="utf-8"))
    if set(marker) != {"schema_version", "feature", "fixture_id", "source_digest"}:
        raise ValueError("synthetic fixture marker is not closed")
    if marker["schema_version"] != "1.0" or marker["feature"] != "001-extension-list":
        raise ValueError("synthetic fixture marker binding mismatch")
    if not isinstance(marker["fixture_id"], str) or not marker["fixture_id"]:
        raise ValueError("synthetic fixture ID is required")
    if not isinstance(marker["source_digest"], str) or not _DIGEST.fullmatch(marker["source_digest"]):
        raise ValueError("synthetic fixture source digest is invalid")


def linux_endpoint(environment: Mapping[str, str], uid: int) -> Path:
    runtime_value = environment.get("XDG_RUNTIME_DIR")
    if runtime_value:
        runtime = Path(runtime_value)
        metadata = runtime.stat(follow_symlinks=False)
        if runtime.is_symlink() or metadata.st_uid != uid or (metadata.st_mode & 0o777) != 0o700:
            raise PermissionError("XDG runtime directory is not owner-only")
        parent = ensure_owner_only_directory(runtime / "ama-specify")
    else:
        parent = ensure_owner_only_directory(Path(environment.get("TMPDIR", tempfile.gettempdir())) / f"ama-specify-{uid}")
    return parent / "daemon.sock"


def windows_pipe_name(sid: str) -> str:
    if not sid:
        raise ValueError("current SID is required")
    return rf"\\.\pipe\ama-specify-{hashlib.sha256(sid.encode('utf-8')).hexdigest()[:24]}"


def validate_partition_capacity(sequence: int, finalizing: bool) -> None:
    if sequence >= MAX_RECORDS:
        raise RuntimeError("audit partition capacity exhausted")
    if not finalizing and sequence >= LAST_ORDINARY_SEQUENCE:
        raise RuntimeError("reserved finalization pair cannot be consumed")


def _stream_summary(value: bytes) -> dict[str, object]:
    return {
        "bytes": len(value),
        "lines": len(value.splitlines()),
        "sha256": hashlib.sha256(value).hexdigest(),
        "summary": "output-present" if value else "empty",
    }


def sanitize(stdout: bytes, stderr: bytes, exit_code: int) -> dict[str, object]:
    return {"exit_code": exit_code, "stdout": _stream_summary(stdout), "stderr": _stream_summary(stderr)}


def _repository_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _state_path(session_id: str) -> Path:
    return _SESSION_ROOT / session_id / "session.json"


def _process_is_alive(pid: int) -> bool:
    if os.name == "nt":
        import ctypes
        from ctypes import wintypes

        process_query_limited_information = 0x1000
        still_active = 259
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.OpenProcess.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
        kernel32.OpenProcess.restype = wintypes.HANDLE
        kernel32.GetExitCodeProcess.argtypes = (wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD))
        kernel32.GetExitCodeProcess.restype = wintypes.BOOL
        kernel32.CloseHandle.argtypes = (wintypes.HANDLE,)
        kernel32.CloseHandle.restype = wintypes.BOOL
        handle = kernel32.OpenProcess(process_query_limited_information, False, pid)
        if not handle:
            return False
        try:
            exit_code = wintypes.DWORD()
            return bool(kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code))) and exit_code.value == still_active
        finally:
            kernel32.CloseHandle(handle)
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _load_state(session_id: str) -> dict[str, object]:
    state_path = _state_path(session_id)
    if not state_path.is_file() or state_path.is_symlink():
        raise RuntimeError("session custody is unavailable")
    state = json.loads(state_path.read_text(encoding="utf-8"))
    if state.get("session_id") != session_id or state.get("owner") != getpass.getuser():
        raise PermissionError("session peer identity mismatch")
    pid = int(state["custodian_pid"])
    if not _process_is_alive(pid):
        raise RuntimeError("session custodian is not alive")
    return state


def _save_state(state: Mapping[str, object]) -> None:
    state_path = _state_path(str(state["session_id"]))
    temporary = state_path.with_suffix(".tmp")
    temporary.write_bytes(canonical_json(state))
    if os.name != "nt":
        os.chmod(temporary, 0o600)
    os.replace(temporary, state_path)


def _path_state(relative_path: str) -> dict[str, str | None]:
    root = _repository_root()
    normalized = Path(relative_path)
    if normalized.is_absolute() or ".." in normalized.parts:
        raise ValueError("target path must be repository-relative")
    path = root / normalized
    if path.is_symlink():
        raise ValueError("target path must not be a symlink")
    if not path.exists():
        return {"state": "absent", "sha256": None}
    if not path.is_file():
        raise ValueError("target path must be a regular file")
    return {"state": "file", "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def _capture_guard(paths: Sequence[str] = PROTECTED_PATHS) -> dict[str, object]:
    captured = capture_protected_state(_repository_root(), paths)
    return {
        "paths": {item.path: {"state": item.state, "sha256": item.sha256} for item in captured.paths},
        "existing_pathspecs": list(captured.existing_pathspecs),
        "staged_diff_sha256": hashlib.sha256(captured.staged_diff).hexdigest(),
        "unstaged_diff_sha256": hashlib.sha256(captured.unstaged_diff).hexdigest(),
    }


def _assert_guard(expected: Mapping[str, object], paths: Sequence[str] = PROTECTED_PATHS) -> None:
    if _capture_guard(paths) != expected:
        raise RuntimeError("protected state or Git diff bytes changed")


def _lock_file(handle: object) -> None:
    if os.name == "nt":
        import msvcrt

        msvcrt.locking(handle.fileno(), msvcrt.LK_LOCK, 1)  # type: ignore[attr-defined]
    else:
        import fcntl

        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)  # type: ignore[attr-defined]


def _unlock_file(handle: object) -> None:
    if os.name == "nt":
        import msvcrt

        handle.seek(0)  # type: ignore[attr-defined]
        msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)  # type: ignore[attr-defined]
    else:
        import fcntl

        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)  # type: ignore[attr-defined]


def _read_and_validate_journal(state: Mapping[str, object]) -> tuple[int, str | None]:
    journal = Path(str(state["journal_path"]))
    sequence = 0
    previous: str | None = None
    if not journal.exists():
        return sequence, previous
    for raw_line in journal.read_bytes().splitlines(keepends=True):
        if not raw_line.endswith(b"\n"):
            raise RuntimeError("journal record is not LF terminated")
        record = json.loads(raw_line)
        if canonical_json(record) + b"\n" != raw_line:
            raise RuntimeError("journal record is not canonical JSON")
        if record["sequence"] != sequence + 1 or record["previous_event_digest"] != previous:
            raise RuntimeError("journal chain is invalid")
        if record["session_manifest_digest"] != state["session_manifest_digest"]:
            raise RuntimeError("session manifest digest changed")
        supplied = record["event_digest"]
        digest_input = dict(record)
        del digest_input["event_digest"]
        if hashlib.sha256(canonical_json(digest_input)).hexdigest() != supplied:
            raise RuntimeError("journal event digest is invalid")
        sequence = record["sequence"]
        previous = supplied
    return sequence, previous


def _append_record(state: dict[str, object], event: dict[str, object], *, finalizing: bool = False) -> str:
    lock_path = Path(str(state["lock_path"]))
    journal_path = Path(str(state["journal_path"]))
    with lock_path.open("a+b") as lock:
        if lock.tell() == 0:
            lock.write(b"0")
            lock.flush()
        lock.seek(0)
        _lock_file(lock)
        try:
            sequence, previous = _read_and_validate_journal(state)
            validate_partition_capacity(sequence, finalizing)
            append_position = journal_path.stat().st_size if journal_path.exists() else 0
            record = {
                **event,
                "append_position_bytes": append_position,
                "audit_sink": state["audit_sink"],
                "execution_mode": state["execution_mode"],
                "ledger_partition": f"spec001-extension-list/{state['session_id']}",
                "previous_event_digest": previous,
                "sequence": sequence + 1,
                "session_id": state["session_id"],
                "session_manifest_digest": state["session_manifest_digest"],
            }
            record["event_digest"] = hashlib.sha256(canonical_json(record)).hexdigest()
            with journal_path.open("ab") as journal:
                journal.write(canonical_json(record) + b"\n")
                journal.flush()
                os.fsync(journal.fileno())
            state["audit_head"] = record["event_digest"]
            state["sequence"] = record["sequence"]
            _save_state(state)
            return str(record["event_id"])
        finally:
            _unlock_file(lock)


def _custodian(session_path: Path) -> int:
    while session_path.exists():
        time.sleep(1)
    return 0


def _spawn_custodian(state_path: Path) -> int:
    command = [sys.executable, str(Path(__file__).resolve()), "--_custodian", str(state_path)]
    flags = 0
    if os.name == "nt":
        flags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
    process = subprocess.Popen(
        command,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        close_fds=True,
        creationflags=flags,
    )
    return process.pid


def _start_session(execution_mode: str) -> int:
    validate_execution_mode(execution_mode)
    if execution_mode != "local-synthetic":
        raise RuntimeError("sovereign session requires external signed preflight and is unavailable locally")
    binding = validate_toolchain()
    ensure_owner_only_directory(_SESSION_ROOT)
    session_id = str(uuid.uuid4())
    session_root = ensure_owner_only_directory(_SESSION_ROOT / session_id)
    state_path = session_root / "session.json"
    manifest = protected_bootstrap_manifest(_repository_root())
    manifest_digest = session_manifest_digest(manifest)
    state: dict[str, object] = {
        "active_action": None,
        "audit_head": None,
        "audit_sink": "ephemeral-local",
        "bootstrap_paths": list(BOOTSTRAP_PATHS),
        "execution_mode": execution_mode,
        "journal_path": str(session_root / "journal.ndjson"),
        "lock_path": str(session_root / "journal.lock"),
        "manifest": manifest,
        "owner": getpass.getuser(),
        "protected_guard": _capture_guard(),
        "runtime": binding,
        "sequence": 0,
        "session_id": session_id,
        "session_manifest_digest": manifest_digest,
        "transition": None,
    }
    _save_state(state)
    state["custodian_pid"] = _spawn_custodian(state_path)
    _save_state(state)
    _append_record(
        state,
        {
            "event_id": str(uuid.uuid4()),
            "event_type": "session.start",
            "outcome": "started",
            "target": {"kind": "session", "identifier": session_id},
        },
    )
    runtime = RuntimeBinding(
        python_version=binding["python_version"],
        uv_version=binding["uv_version"],
        os=binding["os"],
        architecture=binding["architecture"],
    )
    baseline = execute_root_regression(_repository_root(), runtime, session_id)
    state = _load_state(session_id)
    state["root_baseline"] = baseline.to_json()
    _save_state(state)
    print(f"session-id: {session_id}")
    print("local-synthetic custody: active; baseline: captured; qualifying evidence: prohibited")
    return 0


def _begin_action(arguments: argparse.Namespace) -> int:
    state = _load_state(arguments.session_id)
    _assert_guard(state["protected_guard"])
    if state.get("active_action") is not None:
        raise RuntimeError("another action is active")
    pre_state = _path_state(arguments.target_identifier) if arguments.target_kind == "repository-file" else {"state": "stable"}
    event_id = str(uuid.uuid4())
    event = {
        "action": arguments.action,
        "event_id": event_id,
        "event_type": "action.intent",
        "outcome": "started",
        "pre_state": pre_state,
        "target": {"kind": arguments.target_kind, "identifier": arguments.target_identifier},
        "task_id": arguments.task_id,
    }
    _append_record(state, event)
    state = _load_state(arguments.session_id)
    state["active_action"] = event
    _save_state(state)
    print(f"intent-event-id: {event_id}")
    return 0


def _complete_action(arguments: argparse.Namespace) -> int:
    state = _load_state(arguments.session_id)
    active = state.get("active_action")
    if not isinstance(active, dict) or active.get("event_id") != arguments.intent_event_id:
        raise RuntimeError("action intent linkage mismatch")
    target = active["target"]
    expected = (arguments.task_id, arguments.action, arguments.target_kind, arguments.target_identifier)
    actual = (active["task_id"], active["action"], target["kind"], target["identifier"])
    if expected != actual:
        raise RuntimeError("action identity mismatch")
    _assert_guard(state["protected_guard"])
    post_state = _path_state(arguments.target_identifier) if arguments.target_kind == "repository-file" else active["pre_state"]
    _append_record(
        state,
        {
            "action": arguments.action,
            "event_id": str(uuid.uuid4()),
            "event_type": "action.result",
            "intent_event_id": arguments.intent_event_id,
            "outcome": arguments.outcome,
            "post_state": post_state,
            "pre_state": active["pre_state"],
            "target": target,
            "task_id": arguments.task_id,
        },
    )
    state = _load_state(arguments.session_id)
    state["active_action"] = None
    _save_state(state)
    print("action: complete")
    return 0


def _sha256_file(relative_path: str) -> str:
    path = _repository_root() / relative_path
    if not path.is_file() or path.is_symlink():
        raise ValueError("transition target must be a regular file")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _workflow_index_state(path: str) -> dict[str, str]:
    root = _repository_root()
    blob = subprocess.run(
        ["git", "show", f":{path}"], cwd=root, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False
    )
    cached = subprocess.run(
        ["git", "diff", "--cached", "--binary", "--no-ext-diff", "--", path],
        cwd=root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    ).stdout
    return {
        "blob": hashlib.sha256(blob.stdout).hexdigest() if blob.returncode == 0 else "absent",
        "cached_diff": hashlib.sha256(cached).hexdigest(),
    }


def _authorize_transition(arguments: argparse.Namespace) -> int:
    state = _load_state(arguments.session_id)
    _assert_guard(state["protected_guard"])
    if state.get("active_action") is not None or state.get("transition") is not None:
        raise RuntimeError("session already has an active action or transition")
    if arguments.path != ".github/workflows/ci.yml" or _sha256_file(arguments.path) != arguments.expected_before_sha:
        raise RuntimeError("workflow transition pre-state mismatch")
    event_id = str(uuid.uuid4())
    _append_record(
        state,
        {
            "action": "workflow.transition",
            "event_id": event_id,
            "event_type": "action.intent",
            "outcome": "started",
            "pre_state": {"sha256": arguments.expected_before_sha},
            "target": {"kind": "repository-file", "identifier": arguments.path},
            "task_id": "T011",
        },
    )
    state = _load_state(arguments.session_id)
    other_paths = tuple(path for path in PROTECTED_PATHS if path != arguments.path)
    state["active_action"] = {"event_id": event_id, "task_id": "T011"}
    state["transition"] = {
        "expires_at": time.time() + 600,
        "index_state": _workflow_index_state(arguments.path),
        "other_guard": _capture_guard(other_paths),
        "path": arguments.path,
        "pre_sha": arguments.expected_before_sha,
        "transition_id": arguments.transition_id,
    }
    _save_state(state)
    print(f"transition-intent-event-id: {event_id}")
    return 0


def _accept_transition(arguments: argparse.Namespace) -> int:
    state = _load_state(arguments.session_id)
    transition = state.get("transition")
    active = state.get("active_action")
    if not isinstance(transition, dict) or not isinstance(active, dict):
        raise RuntimeError("no workflow transition is active")
    if transition["transition_id"] != arguments.transition_id or transition["path"] != arguments.path:
        raise RuntimeError("workflow transition identity mismatch")
    if time.time() > float(transition["expires_at"]):
        raise RuntimeError("workflow transition permit expired")
    if _sha256_file(arguments.path) != arguments.expected_after_sha:
        raise RuntimeError("workflow transition post-state mismatch")
    other_paths = tuple(path for path in PROTECTED_PATHS if path != arguments.path)
    _assert_guard(transition["other_guard"], other_paths)
    if _workflow_index_state(arguments.path) != transition["index_state"]:
        raise RuntimeError("workflow index or staging state changed")
    _append_record(
        state,
        {
            "action": "workflow.transition",
            "event_id": str(uuid.uuid4()),
            "event_type": "action.result",
            "intent_event_id": active["event_id"],
            "outcome": "succeeded",
            "post_state": {"sha256": arguments.expected_after_sha},
            "pre_state": {"sha256": transition["pre_sha"]},
            "target": {"kind": "repository-file", "identifier": arguments.path},
            "task_id": "T011",
        },
    )
    state = _load_state(arguments.session_id)
    state["active_action"] = None
    state["transition"] = None
    state["protected_guard"] = _capture_guard()
    _save_state(state)
    print("workflow transition: accepted")
    return 0


def _parse_environment(values: Sequence[str]) -> dict[str, str]:
    environment: dict[str, str] = {}
    for value in values:
        if "=" not in value:
            raise ValueError("--env requires NAME=VALUE")
        name, setting = value.split("=", 1)
        if not name:
            raise ValueError("environment name is required")
        environment[name] = setting
    return environment


def _run_child(arguments: argparse.Namespace, child: Sequence[str]) -> int:
    state = _load_state(arguments.session_id)
    if state.get("active_action") is not None:
        raise RuntimeError("cannot launch a child while an action is active")
    _assert_guard(state["protected_guard"])
    requested_environment = _parse_environment(arguments.env)
    if state["execution_mode"] == "sovereign":
        validate_sovereign_environment(requested_environment)
    validate_guarded_child(child, requested_environment)
    before_caches = capture_repository_cache_state(_repository_root())
    event_id = str(uuid.uuid4())
    target = {"kind": "guarded-child", "identifier": hashlib.sha256(canonical_json(list(child))).hexdigest()}
    _append_record(
        state,
        {
            "action": "validation.execute",
            "event_id": event_id,
            "event_type": "action.intent",
            "outcome": "started",
            "pre_state": {"state": "not-run"},
            "target": target,
            "task_id": "guarded-command",
        },
    )
    environment = os.environ.copy()
    environment.update(requested_environment)
    process = subprocess.run(
        child,
        cwd=_repository_root(),
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    _assert_guard(state["protected_guard"])
    compare_repository_cache_state(before_caches, capture_repository_cache_state(_repository_root()))
    state = _load_state(arguments.session_id)
    _append_record(
        state,
        {
            "action": "validation.execute",
            "event_id": str(uuid.uuid4()),
            "event_type": "action.result",
            "intent_event_id": event_id,
            "outcome": "succeeded" if process.returncode == 0 else "failed",
            "post_state": {"state": "complete", "exit_code": process.returncode},
            "pre_state": {"state": "not-run"},
            "target": target,
            "task_id": "guarded-command",
        },
    )
    summary = sanitize(process.stdout, process.stderr, process.returncode)
    print(canonical_json(summary).decode("utf-8"))
    return process.returncode


def _finalize_session(session_id: str) -> int:
    state = _load_state(session_id)
    if state.get("active_action") is not None or state.get("transition") is not None:
        raise RuntimeError("cannot finalize an incomplete session")
    _assert_guard(state["protected_guard"])
    intent_id = str(uuid.uuid4())
    _append_record(
        state,
        {
            "action": "session.finalize",
            "event_id": intent_id,
            "event_type": "action.intent",
            "outcome": "started",
            "pre_state": {"state": "active"},
            "target": {"kind": "session", "identifier": session_id},
            "task_id": "T134",
        },
        finalizing=True,
    )
    state = _load_state(session_id)
    _append_record(
        state,
        {
            "action": "session.finalize",
            "event_id": str(uuid.uuid4()),
            "event_type": "action.result",
            "intent_event_id": intent_id,
            "outcome": "succeeded",
            "post_state": {"state": "finalized"},
            "pre_state": {"state": "active"},
            "target": {"kind": "session", "identifier": session_id},
            "task_id": "T134",
        },
        finalizing=True,
    )
    session_root = _state_path(session_id).parent
    state_path = _state_path(session_id)
    state_path.unlink(missing_ok=True)
    for child in session_root.iterdir():
        child.unlink(missing_ok=True)
    session_root.rmdir()
    print("session: finalized; local journal: deleted")
    return 0


def _self_check() -> int:
    if not _process_is_alive(os.getpid()):
        raise AssertionError("current process liveness check failed")
    api = SelfCheckApi(
        parser_options=EXPECTED_OPTIONS,
        canonical_json=canonical_json,
        validate_toolchain=validate_toolchain,
        validate_guarded_child=validate_guarded_child,
        validate_fixture_access=validate_fixture_access,
        linux_endpoint=linux_endpoint,
        windows_pipe_name=windows_pipe_name,
        sanitize=sanitize,
        validate_execution_mode=validate_execution_mode,
        validate_sovereign_environment=validate_sovereign_environment,
        validate_partition_capacity=validate_partition_capacity,
        root_regression_self_check=root_regression_self_check,
    )
    run_self_checks(api)
    print("dispatcher/root-regression self-check: ok")
    print("fake sovereign vectors: non-qualifying; sovereign readiness: not established")
    return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument("--self-check", action="store_true")
    parser.add_argument("--preflight-prerequisites", action="store_true")
    parser.add_argument("--trust-bundle")
    parser.add_argument("--execution-mode", choices=EXECUTION_MODES)
    parser.add_argument("--start-session", action="store_true")
    parser.add_argument("--session-id")
    parser.add_argument("--begin-action", action="store_true")
    parser.add_argument("--complete-action", action="store_true")
    parser.add_argument("--task-id")
    parser.add_argument("--action")
    parser.add_argument("--target-kind")
    parser.add_argument("--target-identifier")
    parser.add_argument("--intent-event-id")
    parser.add_argument("--outcome", default="succeeded")
    parser.add_argument("--authorize-transition", action="store_true")
    parser.add_argument("--accept-transition", action="store_true")
    parser.add_argument("--transition-id")
    parser.add_argument("--path")
    parser.add_argument("--expected-before-sha")
    parser.add_argument("--expected-after-sha")
    parser.add_argument("--env", action="append", default=[])
    parser.add_argument("--finalize-session", action="store_true")
    parser.add_argument("--_custodian", type=Path, help=argparse.SUPPRESS)
    return parser


def _required(arguments: argparse.Namespace, *names: str) -> None:
    missing = [name for name in names if getattr(arguments, name) in (None, False)]
    if missing:
        raise ValueError(f"missing required options: {', '.join(missing)}")


def main(argv: Sequence[str] | None = None) -> int:
    values = list(sys.argv[1:] if argv is None else argv)
    if "--" in values:
        separator = values.index("--")
        option_values, child = values[:separator], values[separator + 1 :]
    else:
        option_values, child = values, []
    arguments = _parser().parse_args(option_values)
    if arguments._custodian:
        return _custodian(arguments._custodian)
    if arguments.self_check:
        return _self_check()
    if arguments.preflight_prerequisites:
        _required(arguments, "execution_mode", "trust_bundle")
        if arguments.execution_mode != "sovereign":
            raise RuntimeError("signed prerequisite preflight is sovereign-only")
        raise RuntimeError("real sovereign prerequisite preflight is pending external execution")
    if arguments.start_session:
        _required(arguments, "execution_mode")
        return _start_session(arguments.execution_mode)
    if arguments.begin_action:
        _required(arguments, "session_id", "task_id", "action", "target_kind", "target_identifier")
        return _begin_action(arguments)
    if arguments.complete_action:
        _required(
            arguments,
            "session_id",
            "task_id",
            "action",
            "target_kind",
            "target_identifier",
            "intent_event_id",
        )
        return _complete_action(arguments)
    if arguments.authorize_transition:
        _required(arguments, "session_id", "transition_id", "path", "expected_before_sha")
        return _authorize_transition(arguments)
    if arguments.accept_transition:
        _required(arguments, "session_id", "transition_id", "path", "expected_after_sha")
        return _accept_transition(arguments)
    if arguments.finalize_session:
        _required(arguments, "session_id")
        return _finalize_session(arguments.session_id)
    if child:
        _required(arguments, "session_id")
        return _run_child(arguments, child)
    raise ValueError("one dispatcher operation is required")


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, ValueError, PermissionError) as error:
        print(f"dispatcher: blocked: {type(error).__name__}", file=sys.stderr)
        raise SystemExit(1) from None