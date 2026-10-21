from __future__ import annotations

import hashlib
import json
import os
import shutil
import stat
import tempfile
import uuid
from collections.abc import Mapping
from pathlib import Path

import rfc8785

_BUILDER_REPOSITORY_PATH = "tools/specify-cli/tests/fixtures/problem_cases.py"
_MARKER_NAME = ".spec001-synthetic-fixture.json"


class ProblemFixture:
    def __init__(
        self,
        session_temp: Path,
        project_root: Path,
        discovery_start: Path,
        source_digest: str,
        *,
        symlink_supported: bool = True,
    ) -> None:
        self.session_temp = session_temp
        self.project_root = project_root
        self.discovery_start = discovery_start
        self.source_digest = source_digest
        self.symlink_supported = symlink_supported

    def cleanup(self) -> None:
        shutil.rmtree(self.project_root)


def fixture_source_digest() -> str:
    builder = Path(__file__).resolve(strict=True)
    sources = [{"path": _BUILDER_REPOSITORY_PATH, "sha256": hashlib.sha256(builder.read_bytes()).hexdigest()}]
    return hashlib.sha256(rfc8785.dumps(sources)).hexdigest()


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


def _target(project_root: Path, relative_path: str) -> Path:
    relative = Path(relative_path)
    if relative.is_absolute() or ".." in relative.parts:
        raise PermissionError("fixture path escapes the project root")
    resolved_root = project_root.resolve(strict=True)
    target = project_root / relative
    existing = target.parent
    while not existing.exists():
        existing = existing.parent
    if existing.is_symlink() or not existing.resolve(strict=True).is_relative_to(resolved_root):
        raise PermissionError("fixture path escapes the project root")
    return target


def _write_bytes(project_root: Path, relative_path: str, content: bytes) -> None:
    target = _target(project_root, relative_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(content)


def _write_json(project_root: Path, relative_path: str, value: object) -> None:
    _write_bytes(project_root, relative_path, (json.dumps(value, ensure_ascii=True, indent=2) + "\n").encode())


def _manifest(identifier: object, name: object, **extra: object) -> dict[str, object]:
    value = {"id": identifier, "name": name, "version": "1.0.0", "commands": [], "hooks": {}}
    value.update(extra)
    return value


def _materialize(
    session_temp: Path,
    fixture_name: str,
    *,
    manifests: Mapping[str, Mapping[str, object] | bytes],
    registry: Mapping[str, Mapping[str, object]] | None = None,
) -> ProblemFixture:
    resolved_session = _owner_only_directory(session_temp, "session temporary root")
    project_root = Path(tempfile.mkdtemp(prefix=f"spec001-problem-{fixture_name}-", dir=resolved_session))
    project_root.chmod(0o700)
    _owner_only_directory(project_root, "fixture project root")
    source_digest = fixture_source_digest()
    _write_json(
        project_root,
        _MARKER_NAME,
        {
            "schema_version": "1.0",
            "feature": "001-extension-list",
            "fixture_id": f"problem-{fixture_name}-{uuid.uuid4()}",
            "source_digest": source_digest,
        },
    )
    (project_root / ".specify" / "extensions").mkdir(parents=True)
    if registry is not None:
        _write_json(project_root, ".specify/extensions/.registry", registry)
    for directory, manifest in manifests.items():
        content = manifest if isinstance(manifest, bytes) else (json.dumps(manifest, indent=2) + "\n").encode()
        _write_bytes(project_root, f".specify/extensions/{directory}/extension.yml", content)
    return ProblemFixture(resolved_session, project_root, project_root, source_digest)


def build_malformed_case(session_temp: Path) -> ProblemFixture:
    return _materialize(
        session_temp,
        "malformed",
        manifests={
            "healthy": _manifest("healthy-extension", "Healthy Extension"),
            "malformed": b"id: [unterminated\n",
        },
    )


def build_unreadable_case(session_temp: Path) -> ProblemFixture:
    return _materialize(session_temp, "unreadable", manifests={"unreadable": b"\xff\xfe\x00\x00"})


def build_missing_id_case(session_temp: Path) -> ProblemFixture:
    return _materialize(
        session_temp,
        "missing-id",
        manifests={"missing-id": {"name": "Missing Identity", "version": "1.0.0"}},
    )


def build_duplicate_id_case(session_temp: Path) -> ProblemFixture:
    return _materialize(
        session_temp,
        "duplicate-id",
        manifests={
            "first": _manifest("duplicate-extension", "Duplicate First"),
            "second": _manifest("duplicate-extension", "Duplicate Second", version="2.0.0"),
        },
    )


def build_unknown_activation_case(session_temp: Path) -> ProblemFixture:
    return _materialize(
        session_temp,
        "unknown-activation",
        manifests={"unknown": _manifest("unknown-activation", "Unknown Activation")},
        registry={
            "unknown": {
                "path": "unknown",
                "enabled": True,
                "activation": {"state": "waiting-for-magic", "diagnostic": "must not leak as activation failure"},
            }
        },
    )


def build_activation_states_case(session_temp: Path) -> ProblemFixture:
    manifests = {
        "disabled": _manifest("disabled-extension", "Disabled Extension"),
        "inactive": _manifest("inactive-extension", "Inactive Extension"),
        "active": _manifest("active-extension", "Active Extension"),
        "failed": _manifest("failed-extension", "Failed Extension"),
        "legacy": _manifest("legacy-active", "Legacy Active"),
    }
    registry = {
        "disabled": {"path": "disabled", "enabled": False, "activation": {"state": "active"}},
        "inactive": {"path": "inactive", "enabled": True, "activation": {"state": "inactive"}},
        "active": {"path": "active", "enabled": True, "activation": {"state": "active"}},
        "failed": {
            "path": "failed",
            "enabled": True,
            "activation": {"state": "activation-failed", "diagnostic": "Synthetic activation failed."},
        },
        "legacy": {"path": "legacy", "enabled": True, "registered_skills": ["legacy-skill"]},
    }
    return _materialize(session_temp, "activation-states", manifests=manifests, registry=registry)


def build_source_alias_case(session_temp: Path) -> ProblemFixture:
    return _materialize(
        session_temp,
        "source-alias",
        manifests={"alias": _manifest("alias-extension", "Alias Extension")},
        registry={
            "plain": {"path": "alias", "version": "1.0.0"},
            "dotted": {"path": "nested/../alias", "version": "1.0.0"},
        },
    )


def build_symlink_alias_case(session_temp: Path) -> ProblemFixture:
    case = _materialize(
        session_temp,
        "symlink-alias",
        manifests={"real": _manifest("symlink-extension", "Symlink Extension")},
        registry={
            "real": {"path": "real", "version": "1.0.0"},
            "alias": {"path": "alias", "version": "1.0.0"},
        },
    )
    alias = case.project_root / ".specify" / "extensions" / "alias"
    try:
        alias.symlink_to("real", target_is_directory=True)
    except OSError:
        case.symlink_supported = False
    return case


def build_case_variant_case(session_temp: Path) -> ProblemFixture:
    return _materialize(
        session_temp,
        "case-variant",
        manifests={"CaseSource": _manifest("case-extension", "Case Extension")},
        registry={
            "original": {"path": "CaseSource", "version": "1.0.0"},
            "variant": {"path": "casesource", "version": "1.0.0"},
        },
    )


def build_same_name_case(session_temp: Path) -> ProblemFixture:
    return _materialize(
        session_temp,
        "same-name",
        manifests={
            "first": _manifest(None, "Same Name"),
            "second": _manifest(None, "Same Name"),
        },
    )


def build_same_source_identity_conflict_case(session_temp: Path) -> ProblemFixture:
    return _materialize(
        session_temp,
        "identity-conflict",
        manifests={"conflict": _manifest("manifest-identity", "Identity Conflict")},
        registry={"registry-identity": {"path": "conflict", "id": "registry-identity", "version": "1.0.0"}},
    )
