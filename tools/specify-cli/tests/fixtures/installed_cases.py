from __future__ import annotations

import hashlib
import json
import os
import shutil
import stat
import tempfile
import uuid
from collections.abc import Mapping, Sequence
from pathlib import Path

import rfc8785

_MARKER_NAME = ".spec001-synthetic-fixture.json"
_BUILDER_REPOSITORY_PATH = "tools/specify-cli/tests/fixtures/installed_cases.py"


class InstalledFixture:
    def __init__(
        self,
        session_temp: Path,
        project_root: Path,
        discovery_start: Path,
        source_digest: str,
        expected_ids: tuple[str, ...],
    ) -> None:
        self.session_temp = session_temp
        self.project_root = project_root
        self.discovery_start = discovery_start
        self.source_digest = source_digest
        self.expected_ids = expected_ids

    def cleanup(self) -> None:
        shutil.rmtree(self.project_root)


class NoProjectRoot:
    def __init__(self, discovery_start: Path) -> None:
        self.discovery_start = discovery_start

    def cleanup(self) -> None:
        shutil.rmtree(self.discovery_start)


def fixture_source_digest() -> str:
    builder = Path(__file__).resolve(strict=True)
    source_manifest = [
        {
            "path": _BUILDER_REPOSITORY_PATH,
            "sha256": hashlib.sha256(builder.read_bytes()).hexdigest(),
        }
    ]
    return hashlib.sha256(rfc8785.dumps(source_manifest)).hexdigest()


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


def _contained_target(project_root: Path, relative_path: str) -> Path:
    if Path(relative_path).is_absolute():
        raise PermissionError("fixture path must be relative")
    resolved_root = project_root.resolve(strict=True)
    target = project_root / relative_path
    existing = target.parent
    while not existing.exists():
        existing = existing.parent
    if existing.is_symlink() or not existing.resolve(strict=True).is_relative_to(resolved_root):
        raise PermissionError("fixture path escapes the project root")
    return target


def _write_json(project_root: Path, relative_path: str, value: object) -> None:
    target = _contained_target(project_root, relative_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(value, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def _manifest(
    identifier: str,
    name: str,
    *,
    version: str | None = "1.0.0",
    description: str | None = "Synthetic installed extension.",
    commands: Sequence[str] = (),
    hooks: Sequence[str] = (),
    priority: int = 10,
) -> dict[str, object]:
    manifest: dict[str, object] = {
        "id": identifier,
        "name": name,
        "priority": priority,
        "commands": list(commands),
        "hooks": {hook: f"hooks/{hook}.py" for hook in hooks},
    }
    if version is not None:
        manifest["version"] = version
    if description is not None:
        manifest["description"] = description
    return manifest


def _materialize(
    session_temp: Path,
    fixture_name: str,
    *,
    manifests: Mapping[str, Mapping[str, object]],
    registry: Mapping[str, Mapping[str, object]] | None = None,
    nested_start: bool = False,
) -> InstalledFixture:
    resolved_session = _owner_only_directory(session_temp, "session temporary root")
    project_root = Path(tempfile.mkdtemp(prefix=f"spec001-{fixture_name}-", dir=resolved_session))
    project_root.chmod(0o700)
    _owner_only_directory(project_root, "fixture project root")

    source_digest = fixture_source_digest()
    _write_json(
        project_root,
        _MARKER_NAME,
        {
            "schema_version": "1.0",
            "feature": "001-extension-list",
            "fixture_id": f"{fixture_name}-{uuid.uuid4()}",
            "source_digest": source_digest,
        },
    )
    extensions_root = project_root / ".specify" / "extensions"
    extensions_root.mkdir(parents=True)
    if registry is not None:
        _write_json(project_root, ".specify/extensions/.registry", registry)
    for relative_directory, manifest in manifests.items():
        _write_json(project_root, f".specify/extensions/{relative_directory}/extension.yml", manifest)

    discovery_start = project_root
    if nested_start:
        discovery_start = project_root / "workspace" / "nested" / "deep"
        discovery_start.mkdir(parents=True)
    expected_ids = tuple(sorted(str(manifest["id"]) for manifest in manifests.values()))
    return InstalledFixture(resolved_session, project_root, discovery_start, source_digest, expected_ids)


def build_registry_case(session_temp: Path) -> InstalledFixture:
    manifest = _manifest(
        "alpha-tools",
        "Alpha Tools",
        version="2.1.0",
        description="Registry and manifest union fixture.",
        commands=("alpha.run", "alpha.check"),
        hooks=("before-task",),
        priority=4,
    )
    registry = {
        "alpha-tools": {
            "path": "alpha-tools",
            "version": "2.1.0",
            "enabled": True,
            "priority": 4,
            "activation": {"state": "active"},
            "registered_commands": {"copilot": ["alpha.run", "alpha.check"]},
            "registered_skills": ["alpha-skill"],
        }
    }
    return _materialize(session_temp, "registry", manifests={"alpha-tools": manifest}, registry=registry)


def build_manifest_case(session_temp: Path) -> InstalledFixture:
    manifests = {
        "bravo": _manifest(
            "bravo-extension",
            "Bravo Extension",
            version="1.4.0",
            description="Manifest-only extension.",
            commands=("bravo.start",),
            hooks=("after-task", "on-error"),
        ),
        "charlie": _manifest(
            "charlie-extension",
            "Charlie Extension",
            version="3.0.0",
            description="Second manifest-only extension.",
            commands=("charlie.run",),
        ),
    }
    return _materialize(session_temp, "manifest", manifests=manifests)


def build_optional_metadata_case(session_temp: Path) -> InstalledFixture:
    return _materialize(
        session_temp,
        "optional",
        manifests={
            "minimal": _manifest(
                "minimal-extension",
                "Minimal Extension",
                version=None,
                description=None,
            )
        },
    )


def build_nested_directory_case(session_temp: Path) -> InstalledFixture:
    return _materialize(
        session_temp,
        "nested",
        manifests={"nested-extension": _manifest("nested-extension", "Nested Extension")},
        nested_start=True,
    )


def build_empty_case(session_temp: Path) -> InstalledFixture:
    return _materialize(session_temp, "empty", manifests={}, registry={})


def build_long_output_case(session_temp: Path, count: int = 30) -> InstalledFixture:
    manifests = {
        f"extension-{index:03d}": _manifest(
            f"extension-{index:03d}",
            f"Synthetic Extension {index:03d}",
            version=f"1.{index}.0",
            description=(
                f"Long synthetic description {index:03d} with enough text to exercise ordinary terminal scrolling "
                "without invoking a pager or requesting input."
            ),
            commands=(f"extension-{index:03d}.run",),
            hooks=("before-task",),
        )
        for index in range(count)
    }
    return _materialize(session_temp, "long", manifests=manifests)


def build_narrow_terminal_case(session_temp: Path) -> InstalledFixture:
    return _materialize(
        session_temp,
        "narrow",
        manifests={
            "markup-safe": _manifest(
                "markup-safe",
                "[bold] Literal Markup Extension",
                version="7.8.9",
                description="Escaped [link=https://invalid.example]text[/link] remains visible when wrapped.",
                commands=("markup-safe.execute-a-long-command-name",),
                hooks=("before-a-long-running-task",),
            )
        },
    )


def build_no_project_root() -> NoProjectRoot:
    discovery_start = Path(tempfile.mkdtemp(prefix="spec001-no-root-"))
    discovery_start.chmod(0o700)
    _owner_only_directory(discovery_start, "no-project-root directory")
    if any((ancestor / ".specify" / "extensions").exists() for ancestor in (discovery_start, *discovery_start.parents)):
        shutil.rmtree(discovery_start)
        raise RuntimeError("no-project-root directory has an extension ancestor")
    if (discovery_start / _MARKER_NAME).exists():
        shutil.rmtree(discovery_start)
        raise RuntimeError("no-project-root directory must not contain a marker")
    return NoProjectRoot(discovery_start)
