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

MARKER_NAME = ".spec001-synthetic-fixture.json"
BUILDER_REPOSITORY_PATHS = (
    "tools/specify-cli/tests/fixtures/catalog_local_cases.py",
    "tools/specify-cli/tests/fixtures/catalog_remote_cases.py",
)


class CatalogFixture:
    def __init__(
        self,
        session_temp: Path,
        project_root: Path,
        discovery_start: Path,
        source_digest: str,
    ) -> None:
        self.session_temp = session_temp
        self.project_root = project_root
        self.discovery_start = discovery_start
        self.source_digest = source_digest
        self.extensions_root = project_root / ".specify" / "extensions"
        self.catalog_config = self.extensions_root / "catalogs.json"

    def cleanup(self) -> None:
        shutil.rmtree(self.project_root)


def catalog_fixture_source_digest() -> str:
    repository_root = Path(__file__).resolve(strict=True).parents[4]
    source_manifest: list[dict[str, str]] = []
    for relative_path in BUILDER_REPOSITORY_PATHS:
        source_path = repository_root / relative_path
        if not source_path.is_file() or source_path.is_symlink():
            raise PermissionError("catalog fixture builders must be regular files")
        source_manifest.append(
            {
                "path": relative_path,
                "sha256": hashlib.sha256(source_path.read_bytes()).hexdigest(),
            }
        )
    source_manifest.sort(key=lambda item: item["path"])
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
    relative = Path(relative_path)
    if relative.is_absolute():
        raise PermissionError("fixture path must be relative")
    resolved_root = project_root.resolve(strict=True)
    target = project_root / relative
    existing = target.parent
    while not existing.exists():
        existing = existing.parent
    if existing.is_symlink() or not existing.resolve(strict=True).is_relative_to(resolved_root):
        raise PermissionError("fixture path escapes the project root")
    return target


def _write_json(project_root: Path, relative_path: str, value: object) -> Path:
    target = _contained_target(project_root, relative_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(value, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    return target


def catalog_record(
    identifier: str,
    name: str,
    *,
    version: str | None = "1.0.0",
    description: str | None = "Synthetic catalog extension.",
    author: str | None = "Synthetic Author",
    install_allowed: bool = True,
    commands: int = 0,
    templates: int = 0,
    scripts: int = 0,
    hooks: int = 0,
) -> dict[str, object]:
    return {
        "id": identifier,
        "name": name,
        "version": version,
        "description": description,
        "author": author,
        "install_allowed": install_allowed,
        "provides": {
            "commands": commands,
            "templates": templates,
            "scripts": scripts,
            "hooks": hooks,
        },
    }


def materialize_catalog_fixture(
    session_temp: Path,
    fixture_name: str,
    *,
    catalogs: Sequence[Mapping[str, object]],
    sources: Mapping[str, Mapping[str, object]],
    nested_start: bool = False,
) -> CatalogFixture:
    resolved_session = _owner_only_directory(session_temp, "session temporary root")
    project_root = Path(tempfile.mkdtemp(prefix=f"spec001-{fixture_name}-", dir=resolved_session))
    project_root.chmod(0o700)
    _owner_only_directory(project_root, "fixture project root")

    source_digest = catalog_fixture_source_digest()
    _write_json(
        project_root,
        MARKER_NAME,
        {
            "schema_version": "1.0",
            "feature": "001-extension-list",
            "fixture_id": f"{fixture_name}-{uuid.uuid4()}",
            "source_digest": source_digest,
        },
    )
    _write_json(
        project_root,
        ".specify/extensions/catalogs.json",
        {"schema_version": "1.0", "catalogs": list(catalogs)},
    )
    for relative_path, source in sources.items():
        _write_json(project_root, relative_path, source)

    discovery_start = project_root
    if nested_start:
        discovery_start = project_root / "workspace" / "nested"
        discovery_start.mkdir(parents=True)
    return CatalogFixture(resolved_session, project_root, discovery_start, source_digest)


def build_local_catalog_boundary_case(session_temp: Path) -> CatalogFixture:
    records = [
        catalog_record(
            "catalog-extension-0000",
            "Boundary Extension 0000",
            version=None,
        ),
        *[
            catalog_record(
                f"catalog-extension-{index:04d}",
                f"Boundary Extension {index:04d}",
                version=f"1.{index}.0",
                commands=index % 3,
                hooks=index % 2,
            )
            for index in range(1, 1_000)
        ],
    ]
    return materialize_catalog_fixture(
        session_temp,
        "catalog-boundary",
        catalogs=[{"name": "boundary", "priority": 1, "path": "catalogs/boundary.json"}],
        sources={
            ".specify/extensions/catalogs/boundary.json": {
                "schema_version": "1.0",
                "extensions": records,
            }
        },
        nested_start=True,
    )


def build_catalog_conflict_case(session_temp: Path) -> CatalogFixture:
    return materialize_catalog_fixture(
        session_temp,
        "catalog-conflict",
        catalogs=[
            {"name": "alpha", "priority": 1, "path": "catalogs/alpha.json"},
            {"name": "bravo", "priority": 1, "path": "catalogs/bravo.json"},
        ],
        sources={
            ".specify/extensions/catalogs/alpha.json": {
                "schema_version": "1.0",
                "extensions": [
                    catalog_record(
                        "shared-extension",
                        "Alpha Preferred",
                        version="2.0.0",
                        description="Synthetic alpha description.",
                        install_allowed=True,
                        commands=2,
                    )
                ],
            },
            ".specify/extensions/catalogs/bravo.json": {
                "schema_version": "1.0",
                "extensions": [
                    catalog_record(
                        "shared-extension",
                        "Bravo Alternate",
                        version="3.0.0",
                        description="Synthetic bravo description.",
                        install_allowed=False,
                        hooks=3,
                    )
                ],
            },
        },
    )
