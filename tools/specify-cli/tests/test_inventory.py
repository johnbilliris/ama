from __future__ import annotations

# ruff: noqa: I001

import importlib.util
import json
import os
import stat
from pathlib import Path
from types import ModuleType
from typing import Protocol

import pytest

from specify_cli.extensions.models import ExtensionListEntry

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]


def _load_cases() -> ModuleType:
    fixture_path = Path(__file__).resolve().parent / "fixtures" / "installed_cases.py"
    spec = importlib.util.spec_from_file_location("spec001_installed_cases", fixture_path)
    if spec is None or spec.loader is None:
        raise ImportError("cannot load installed fixture builder")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


CASES = _load_cases()


class _InstalledFixture(Protocol):
    discovery_start: Path
    session_temp: Path
    source_digest: str


def _session_temp(tmp_path: Path) -> Path:
    session_temp = tmp_path / "session"
    session_temp.mkdir(mode=0o700)
    session_temp.chmod(0o700)
    if os.name != "nt":
        assert stat.S_IMODE(session_temp.stat().st_mode) == 0o700
    return session_temp


def _snapshot(root: Path) -> dict[str, bytes]:
    return {path.relative_to(root).as_posix(): path.read_bytes() for path in sorted(root.rglob("*")) if path.is_file()}


def _load(case: _InstalledFixture) -> tuple[ExtensionListEntry, ...]:
    from specify_cli.extensions.inventory import load_installed_entries

    return tuple(
        load_installed_entries(
            case.discovery_start,
            session_temp=case.session_temp,
            source_digest=case.source_digest,
            synthetic_mode=True,
        )
    )


def test_installed_inventory_registry_manifest_union_counts_evidence_and_read_only(tmp_path: Path) -> None:
    case = CASES.build_registry_case(_session_temp(tmp_path))
    before = _snapshot(case.project_root)
    try:
        entries = _load(case)
        after = _snapshot(case.project_root)
    finally:
        case.cleanup()

    assert before == after
    assert len(entries) == 1
    entry = entries[0]
    assert entry.id == "alpha-tools"
    assert entry.name == "Alpha Tools"
    assert entry.installed_version == "2.1.0"
    assert entry.version == "2.1.0"
    assert entry.description == "Registry and manifest union fixture."
    assert entry.priority == 4
    assert entry.enabled is True
    assert entry.activation_state == "active"
    assert entry.health.state == "healthy"
    assert entry.provides.commands == 2
    assert entry.provides.hooks == 1
    assert entry.source_locations == (".specify/extensions/alpha-tools",)
    assert [item.kind for item in entry.evidence] == ["local", "local"]
    assert [item.source_ordinal for item in entry.evidence] == [0, 1]


def test_installed_inventory_physical_manifests_filter_catalog_and_sort_deterministically(tmp_path: Path) -> None:
    case = CASES.build_manifest_case(_session_temp(tmp_path))
    try:
        entries = _load(case)
    finally:
        case.cleanup()

    assert [entry.id for entry in entries] == ["bravo-extension", "charlie-extension"]
    assert [entry.name for entry in entries] == ["Bravo Extension", "Charlie Extension"]
    assert all(entry.source.kind == "local" for entry in entries)
    assert all(entry.catalog_sources == () for entry in entries)
    assert all(entry.available_versions == () for entry in entries)
    assert [entry.provides.commands for entry in entries] == [1, 1]
    assert [entry.provides.hooks for entry in entries] == [2, 0]


def test_installed_inventory_ancestor_discovery_from_nested_directory(tmp_path: Path) -> None:
    from specify_cli.extensions.inventory import discover_project

    case = CASES.build_nested_directory_case(_session_temp(tmp_path))
    try:
        context = discover_project(case.discovery_start)
        entries = _load(case)
    finally:
        case.cleanup()

    assert context.project_root == case.project_root
    assert [entry.id for entry in entries] == ["nested-extension"]


def test_installed_inventory_missing_optional_metadata_remains_healthy(tmp_path: Path) -> None:
    case = CASES.build_optional_metadata_case(_session_temp(tmp_path))
    try:
        entries = _load(case)
    finally:
        case.cleanup()

    assert len(entries) == 1
    entry = entries[0]
    assert entry.id == "minimal-extension"
    assert entry.version == "unknown"
    assert entry.installed_version is None
    assert entry.description is None
    assert entry.health.state == "healthy"
    assert entry.provides.commands == 0
    assert entry.provides.hooks == 0


def test_installed_inventory_empty_fixture_returns_no_rows(tmp_path: Path) -> None:
    case = CASES.build_empty_case(_session_temp(tmp_path))
    try:
        assert _load(case) == ()
    finally:
        case.cleanup()


def test_installed_inventory_no_root_is_null_without_marker_or_inventory_access(tmp_path: Path) -> None:
    from specify_cli.extensions.inventory import discover_project, load_installed_entries

    no_root = CASES.build_no_project_root()
    try:
        assert not (no_root.discovery_start / ".spec001-synthetic-fixture.json").exists()
        assert discover_project(no_root.discovery_start).project_root is None
        assert (
            tuple(
                load_installed_entries(
                    no_root.discovery_start,
                    session_temp=_session_temp(tmp_path),
                    source_digest=CASES.fixture_source_digest(),
                    synthetic_mode=True,
                )
            )
            == ()
        )
    finally:
        no_root.cleanup()


def test_installed_inventory_rejects_marker_mismatch_before_source_read(tmp_path: Path) -> None:
    from specify_cli.extensions.inventory import load_installed_entries

    case = CASES.build_registry_case(_session_temp(tmp_path))
    marker_path = case.project_root / ".spec001-synthetic-fixture.json"
    marker = json.loads(marker_path.read_text(encoding="utf-8"))
    marker["source_digest"] = "0" * 64
    marker_path.write_text(json.dumps(marker), encoding="utf-8")
    registry_path = case.project_root / ".specify" / "extensions" / ".registry"
    registry_before = registry_path.read_bytes()
    try:
        with pytest.raises(PermissionError, match="source digest mismatch"):
            tuple(
                load_installed_entries(
                    case.discovery_start,
                    session_temp=case.session_temp,
                    source_digest=case.source_digest,
                    synthetic_mode=True,
                )
            )
        assert registry_path.read_bytes() == registry_before
    finally:
        case.cleanup()


def test_installed_inventory_rejects_repository_live_root_before_inventory_access(tmp_path: Path) -> None:
    from specify_cli.extensions.inventory import load_installed_entries

    with pytest.raises(PermissionError, match="beneath the session temporary root"):
        tuple(
            load_installed_entries(
                REPOSITORY_ROOT,
                session_temp=_session_temp(tmp_path),
                source_digest=CASES.fixture_source_digest(),
                synthetic_mode=True,
            )
        )
