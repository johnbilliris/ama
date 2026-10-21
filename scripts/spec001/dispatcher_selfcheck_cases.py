from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import platform
import tempfile
from typing import Callable, Mapping, Sequence
import uuid


EXPECTED_OPTIONS = (
    "--self-check",
    "--preflight-prerequisites",
    "--trust-bundle",
    "--execution-mode",
    "--start-session",
    "--session-id",
    "--begin-action",
    "--complete-action",
    "--task-id",
    "--action",
    "--target-kind",
    "--target-identifier",
    "--intent-event-id",
    "--outcome",
    "--authorize-transition",
    "--accept-transition",
    "--transition-id",
    "--path",
    "--expected-before-sha",
    "--expected-after-sha",
    "--env",
    "--finalize-session",
    "--",
)

ROOT_PROVISION_COMMAND = ("uv", "sync", "--locked", "--extra", "dev", "--no-install-project")
ROOT_PYTEST_PREFIX = ("uv", "run", "--no-sync", "pytest")
PARTITION_PREFIX = "spec001-extension-list"
MAX_RECORDS = 49_000
LAST_ORDINARY_SEQUENCE = 48_998
FINALIZATION_SEQUENCES = (48_999, 49_000)


@dataclass(frozen=True)
class SelfCheckApi:
    parser_options: Sequence[str]
    canonical_json: Callable[[object], bytes]
    validate_toolchain: Callable[[], Mapping[str, str]]
    validate_guarded_child: Callable[[Sequence[str], Mapping[str, str]], None]
    validate_fixture_access: Callable[[Path | None, Path, Mapping[str, str]], None]
    linux_endpoint: Callable[[Mapping[str, str], int], Path]
    windows_pipe_name: Callable[[str], str]
    sanitize: Callable[[bytes, bytes, int], Mapping[str, object]]
    validate_execution_mode: Callable[[str], None]
    validate_sovereign_environment: Callable[[Mapping[str, str]], None]
    validate_partition_capacity: Callable[[int, bool], None]
    root_regression_self_check: Callable[[], None]


def _expect_error(action: Callable[[], object], message: str) -> None:
    try:
        action()
    except (RuntimeError, ValueError, PermissionError):
        return
    raise AssertionError(message)


def _exercise_parser(api: SelfCheckApi) -> None:
    if tuple(api.parser_options) != EXPECTED_OPTIONS:
        raise AssertionError("frozen parser surface drift")


def _exercise_toolchain(api: SelfCheckApi) -> None:
    binding = api.validate_toolchain()
    required = {"python_executable", "python_version", "uv_version", "os", "architecture"}
    if set(binding) != required or any(not value for value in binding.values()):
        raise AssertionError("toolchain binding is incomplete")
    major, minor, *_ = (int(part) for part in platform.python_version_tuple())
    if (major, minor) < (3, 12):
        raise AssertionError("Python 3.12 or later is required")


def _exercise_canonical_json(api: SelfCheckApi) -> None:
    if api.canonical_json({"z": 1, "a": [True, None]}) != b'{"a":[true,null],"z":1}':
        raise AssertionError("canonical JSON encoding drift")


def _exercise_modes_and_environment(api: SelfCheckApi) -> None:
    api.validate_execution_mode("local-synthetic")
    api.validate_execution_mode("sovereign")
    _expect_error(lambda: api.validate_execution_mode("local"), "unknown execution mode accepted")
    api.validate_sovereign_environment({})
    for name in ("SPEC001_TEST_MODE", "SPEC001_EXTERNAL_TRANSPORT", "SPEC001_UNKNOWN", "SPECIFY_CLI_UNKNOWN"):
        _expect_error(
            lambda name=name: api.validate_sovereign_environment({name: "synthetic"}),
            f"sovereign environment accepted {name}",
        )


def _exercise_guarded_children(api: SelfCheckApi) -> None:
    pytest_environment = {"UV_FROZEN": "1", "PYTEST_ADDOPTS": "-pno:cacheprovider"}
    api.validate_guarded_child((*ROOT_PYTEST_PREFIX, "tests/unit"), pytest_environment)
    api.validate_guarded_child(
        ("uv", "run", "--project", "tools/specify-cli", "--extra", "dev", "pytest", "tests"),
        pytest_environment,
    )
    api.validate_guarded_child(
        ("uv", "run", "--project", "tools/specify-cli", "--extra", "dev", "mypy", "src"),
        {"UV_FROZEN": "1", "MYPY_CACHE_DIR": str(Path(tempfile.gettempdir()) / "spec001-mypy")},
    )
    _expect_error(
        lambda: api.validate_guarded_child(("uv", "run", "pytest"), pytest_environment),
        "root pytest sync was accepted",
    )
    _expect_error(
        lambda: api.validate_guarded_child(ROOT_PYTEST_PREFIX, {"PYTEST_ADDOPTS": "-pno:cacheprovider"}),
        "uv child without UV_FROZEN was accepted",
    )
    _expect_error(
        lambda: api.validate_guarded_child(ROOT_PYTEST_PREFIX, {"UV_FROZEN": "1"}),
        "pytest child without cache-provider denial was accepted",
    )
    _expect_error(
        lambda: api.validate_guarded_child(
            ("uv", "run", "--project", "tools/specify-cli", "pytest"), pytest_environment
        ),
        "package pytest without dev extra was accepted",
    )


def _exercise_fixture_policy(api: SelfCheckApi) -> None:
    with tempfile.TemporaryDirectory(prefix="spec001-session-") as temporary:
        session_root = Path(temporary)
        api.validate_fixture_access(None, session_root, {})
        fixture = session_root / "fixture"
        fixture.mkdir()
        marker = fixture / ".spec001-synthetic-fixture.json"
        marker.write_text(
            '{"feature":"001-extension-list","fixture_id":"synthetic-1","schema_version":"1.0",'
            '"source_digest":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"}',
            encoding="utf-8",
        )
        api.validate_fixture_access(fixture, session_root, {"SPEC001_TEST_MODE": "synthetic"})
        _expect_error(
            lambda: api.validate_fixture_access(fixture, session_root, {}),
            "data-bearing fixture without synthetic mode was accepted",
        )
        _expect_error(
            lambda: api.validate_fixture_access(Path.cwd(), session_root, {"SPEC001_TEST_MODE": "synthetic"}),
            "repository-resident fixture was accepted",
        )


def _exercise_endpoints(api: SelfCheckApi) -> None:
    fallback = api.linux_endpoint({}, 1000)
    if fallback.as_posix().split("/")[-2:] != ["ama-specify-1000", "daemon.sock"]:
        raise AssertionError("Linux fallback endpoint drift")
    with tempfile.TemporaryDirectory(prefix="spec001-xdg-") as temporary:
        runtime_root = Path(temporary)
        if os.name != "nt":
            os.chmod(runtime_root, 0o700)
            endpoint = api.linux_endpoint({"XDG_RUNTIME_DIR": str(runtime_root)}, os.getuid())
            if endpoint != runtime_root / "ama-specify" / "daemon.sock":
                raise AssertionError("Linux XDG endpoint drift")
    pipe = api.windows_pipe_name("S-1-5-21-synthetic")
    if not pipe.startswith("\\\\.\\pipe\\ama-specify-"):
        raise AssertionError("Windows named-pipe endpoint drift")


def _exercise_partition(api: SelfCheckApi) -> None:
    api.validate_partition_capacity(LAST_ORDINARY_SEQUENCE - 1, False)
    api.validate_partition_capacity(LAST_ORDINARY_SEQUENCE, True)
    _expect_error(
        lambda: api.validate_partition_capacity(LAST_ORDINARY_SEQUENCE, False),
        "ordinary action consumed the reserved finalization pair",
    )
    _expect_error(lambda: api.validate_partition_capacity(MAX_RECORDS, True), "partition rollover was accepted")
    first = f"{PARTITION_PREFIX}/{uuid.uuid4()}"
    second = f"{PARTITION_PREFIX}/{uuid.uuid4()}"
    if first == second:
        raise AssertionError("new sessions claimed continuity")


def _exercise_sanitizer(api: SelfCheckApi) -> None:
    result = api.sanitize(b"one\n", b"secret=/private/path\n", 1)
    required = {"exit_code", "stdout", "stderr"}
    if set(result) != required:
        raise AssertionError("sanitizer result is not closed")
    for stream in (result["stdout"], result["stderr"]):
        if not isinstance(stream, dict) or set(stream) != {"bytes", "lines", "sha256", "summary"}:
            raise AssertionError("sanitizer stream metadata is not closed")
    if "secret" in str(result).lower() or "private" in str(result).lower():
        raise AssertionError("sanitizer exposed forbidden values")


def run_self_checks(api: SelfCheckApi) -> None:
    _exercise_parser(api)
    _exercise_toolchain(api)
    _exercise_canonical_json(api)
    _exercise_modes_and_environment(api)
    _exercise_guarded_children(api)
    _exercise_fixture_policy(api)
    _exercise_endpoints(api)
    _exercise_partition(api)
    _exercise_sanitizer(api)
    api.root_regression_self_check()
