from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat
import subprocess
from typing import Iterable, Mapping, Sequence


PROTECTED_PATHS = (
    "pyproject.toml",
    "uv.lock",
    "package.json",
    "pnpm-workspace.yaml",
    "azure.yaml",
    "ruff.toml",
    ".pre-commit-config.yaml",
    ".github/workflows/ci.yml",
    "apps/api/Dockerfile",
    "apps/api/app/main.py",
    "apps/agents/Dockerfile",
    "apps/agents/dispatcher/__main__.py",
    "apps/agents/communication/__main__.py",
    "apps/agents/evacuation/__main__.py",
    "apps/agents/maf_runtime/workflow/builder.py",
    "apps/ingestion/Dockerfile",
    "apps/ingestion/worker.py",
    "apps/web/package.json",
)

BOOTSTRAP_PATHS = (
    "scripts/spec001/protected_state_selfcheck.py",
    "scripts/spec001/dispatcher_selfcheck_cases.py",
    "scripts/spec001/protected_state.py",
    "scripts/spec001/root_regression.py",
    "scripts/spec001/run_local_gates.py",
)


@dataclass(frozen=True)
class PathState:
    path: str
    state: str
    sha256: str | None


@dataclass(frozen=True)
class ProtectedState:
    paths: tuple[PathState, ...]
    existing_pathspecs: tuple[str, ...]
    staged_diff: bytes
    unstaged_diff: bytes


class ProtectedStateMismatch(RuntimeError):
    def __init__(self, changed_paths: Sequence[str], staged_diff_changed: bool, unstaged_diff_changed: bool) -> None:
        self.changed_paths = tuple(changed_paths)
        self.staged_diff_changed = staged_diff_changed
        self.unstaged_diff_changed = unstaged_diff_changed
        super().__init__("protected state changed")


def _canonical_json_bytes(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")


def session_manifest_digest(manifest: Mapping[str, object]) -> str:
    return hashlib.sha256(_canonical_json_bytes(manifest)).hexdigest()


def ensure_owner_only_directory(path: Path) -> Path:
    if path.exists() and path.is_symlink():
        raise ValueError("owner-only state path must not be a symlink")
    path.mkdir(mode=0o700, parents=True, exist_ok=True)
    if os.name != "nt":
        os.chmod(path, 0o700)
        metadata = path.stat(follow_symlinks=False)
        if metadata.st_uid != os.getuid() or stat.S_IMODE(metadata.st_mode) != 0o700:
            raise PermissionError("owner-only state directory ownership or mode is invalid")
    return path


def _normalize_relative_path(relative_path: str) -> str:
    normalized = PurePosixPath(relative_path)
    if normalized.is_absolute() or ".." in normalized.parts or str(normalized) in {"", "."}:
        raise ValueError("protected path must be repository-relative")
    return normalized.as_posix()


def _capture_path(root: Path, relative_path: str) -> PathState:
    normalized = _normalize_relative_path(relative_path)
    path = root.joinpath(*PurePosixPath(normalized).parts)
    if path.is_symlink():
        raise ValueError(f"protected path is a symlink: {normalized}")
    if not path.exists():
        return PathState(path=normalized, state="absent", sha256=None)
    if not path.is_file():
        raise ValueError(f"protected path is not a regular file: {normalized}")
    return PathState(path=normalized, state="file", sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def capture_path_states(root: Path, paths: Iterable[str]) -> tuple[PathState, ...]:
    return tuple(_capture_path(root, relative_path) for relative_path in paths)


def protected_bootstrap_manifest(root: Path) -> dict[str, list[dict[str, str | None]]]:
    def serialize(paths: Sequence[str]) -> list[dict[str, str | None]]:
        return [
            {"path": item.path, "state": item.state, "sha256": item.sha256}
            for item in capture_path_states(root, paths)
        ]

    return {"protected": serialize(PROTECTED_PATHS), "bootstrap": serialize(BOOTSTRAP_PATHS)}


def _git_diff(root: Path, pathspecs: Sequence[str], *, cached: bool) -> bytes:
    if not pathspecs:
        return b""
    arguments = ["git", "diff"]
    if cached:
        arguments.append("--cached")
    arguments.extend(("--binary", "--no-ext-diff", "--", *pathspecs))
    return subprocess.run(
        arguments,
        cwd=root,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ).stdout


def capture_protected_state(
    root: Path,
    paths: Sequence[str] = PROTECTED_PATHS,
    existing_pathspecs: Sequence[str] | None = None,
) -> ProtectedState:
    resolved_root = root.resolve(strict=True)
    path_states = capture_path_states(resolved_root, paths)
    if existing_pathspecs is None:
        frozen_pathspecs = tuple(item.path for item in path_states if item.state == "file")
    else:
        frozen_pathspecs = tuple(_normalize_relative_path(path) for path in existing_pathspecs)
    return ProtectedState(
        paths=path_states,
        existing_pathspecs=frozen_pathspecs,
        staged_diff=_git_diff(resolved_root, frozen_pathspecs, cached=True),
        unstaged_diff=_git_diff(resolved_root, frozen_pathspecs, cached=False),
    )


def compare_protected_state(before: ProtectedState, after: ProtectedState) -> None:
    before_paths = {item.path: item for item in before.paths}
    after_paths = {item.path: item for item in after.paths}
    changed_paths = sorted(
        path
        for path in before_paths.keys() | after_paths.keys()
        if before_paths.get(path) != after_paths.get(path)
    )
    staged_changed = before.staged_diff != after.staged_diff
    unstaged_changed = before.unstaged_diff != after.unstaged_diff
    if before.existing_pathspecs != after.existing_pathspecs:
        changed_paths.append("<existing-pathspecs>")
    if changed_paths or staged_changed or unstaged_changed:
        raise ProtectedStateMismatch(changed_paths, staged_changed, unstaged_changed)