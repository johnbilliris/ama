from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import tempfile

from protected_state import (
    BOOTSTRAP_PATHS,
    PROTECTED_PATHS,
    ProtectedStateMismatch,
    capture_protected_state,
    compare_protected_state,
    ensure_owner_only_directory,
    session_manifest_digest,
)


EXPECTED_PROTECTED_PATHS = (
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

EXPECTED_BOOTSTRAP_PATHS = (
    "scripts/spec001/protected_state_selfcheck.py",
    "scripts/spec001/dispatcher_selfcheck_cases.py",
    "scripts/spec001/protected_state.py",
    "scripts/spec001/root_regression.py",
    "scripts/spec001/run_local_gates.py",
)


def _git(root: Path, *arguments: str) -> bytes:
    return subprocess.run(
        ["git", *arguments],
        cwd=root,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ).stdout


def _write(root: Path, relative_path: str, value: bytes) -> None:
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(value)


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _exercise_exact_manifests() -> None:
    _require(PROTECTED_PATHS == EXPECTED_PROTECTED_PATHS, "protected manifest drift")
    _require(BOOTSTRAP_PATHS == EXPECTED_BOOTSTRAP_PATHS, "bootstrap manifest drift")


def _exercise_canonical_digest() -> None:
    manifest = {
        "protected": [
            {"path": "alpha", "state": "file", "sha256": "a" * 64},
            {"path": "omega", "state": "absent", "sha256": None},
        ],
        "bootstrap": [],
    }
    expected = hashlib.sha256(
        json.dumps(manifest, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")
    ).hexdigest()
    _require(session_manifest_digest(manifest) == expected, "manifest digest is not canonical")
    reordered = {"bootstrap": [], "protected": manifest["protected"]}
    _require(session_manifest_digest(reordered) == expected, "object key order changed the digest")


def _exercise_owner_only_state() -> None:
    with tempfile.TemporaryDirectory(prefix="spec001-protected-") as temporary:
        state_root = Path(temporary) / "state"
        ensure_owner_only_directory(state_root)
        _require(state_root.is_dir(), "owner-only state directory was not created")
        _require(not state_root.is_symlink(), "owner-only state directory followed a symlink")
        if os.name != "nt":
            mode = stat.S_IMODE(state_root.stat().st_mode)
            _require(mode == 0o700, f"owner-only state mode is {mode:o}")


def _exercise_capture_and_dirty_preservation() -> None:
    with tempfile.TemporaryDirectory(prefix="spec001-repository-") as temporary:
        root = Path(temporary)
        _git(root, "init", "--quiet")
        _git(root, "config", "user.email", "synthetic@example.invalid")
        _git(root, "config", "user.name", "Synthetic")
        _write(root, "pyproject.toml", b"initial\n")
        _write(root, "package.json", b"{}\n")
        _git(root, "add", "pyproject.toml", "package.json")
        _git(root, "commit", "--quiet", "-m", "synthetic baseline")

        _write(root, "pyproject.toml", b"staged\n")
        _git(root, "add", "pyproject.toml")
        _write(root, "package.json", b'{"dirty":true}\n')

        before = capture_protected_state(root, ("pyproject.toml", "package.json", "uv.lock"))
        _require(before.existing_pathspecs == ("pyproject.toml", "package.json"), "existing pathspecs were not frozen")
        states = {item.path: item for item in before.paths}
        _require(states["uv.lock"].state == "absent", "absent state was not captured")
        _require(states["uv.lock"].sha256 is None, "absent state has a digest")
        _require(states["pyproject.toml"].sha256 == hashlib.sha256(b"staged\n").hexdigest(), "file digest mismatch")
        _require(before.staged_diff, "staged binary diff was not captured")
        _require(before.unstaged_diff, "unstaged binary diff was not captured")

        after = capture_protected_state(root, ("pyproject.toml", "package.json", "uv.lock"), before.existing_pathspecs)
        compare_protected_state(before, after)
        _require(_git(root, "diff", "--cached", "--binary", "--no-ext-diff") != b"", "staged dirty state was remediated")
        _require(_git(root, "diff", "--binary", "--no-ext-diff") != b"", "unstaged dirty state was remediated")

        _write(root, "package.json", b'{"dirty":false}\n')
        changed = capture_protected_state(root, ("pyproject.toml", "package.json", "uv.lock"), before.existing_pathspecs)
        try:
            compare_protected_state(before, changed)
        except ProtectedStateMismatch as error:
            _require("package.json" in error.changed_paths, "dirty mismatch omitted the changed path")
        else:
            raise AssertionError("dirty-state mismatch was not detected")


def main() -> int:
    _exercise_exact_manifests()
    _exercise_canonical_digest()
    _exercise_owner_only_state()
    _exercise_capture_and_dirty_preservation()
    print("protected-state self-check: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())