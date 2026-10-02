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
    fixture_path = Path(__file__).resolve().parent / "fixtures" / "problem_cases.py"
    spec = importlib.util.spec_from_file_location("spec001_problem_cases", fixture_path)
    if spec is None or spec.loader is None:
        raise ImportError("cannot load problem fixture builder")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


CASES = _load_cases()


class _ProblemFixture(Protocol):
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


def _load(case: _ProblemFixture) -> tuple[ExtensionListEntry, ...]:
    from specify_cli.extensions.inventory import load_installed_entries

    return tuple(
        load_installed_entries(
            case.discovery_start,
            session_temp=case.session_temp,
            source_digest=case.source_digest,
            synthetic_mode=True,
        )
    )


def _codes(entry: ExtensionListEntry) -> list[str]:
    return [diagnostic.code for diagnostic in entry.health.diagnostics]


def test_problem_projection_activation_precedence_and_diagnostic_nullability(tmp_path: Path) -> None:
    case = CASES.build_activation_states_case(_session_temp(tmp_path))
    try:
        entries = {entry.id: entry for entry in _load(case)}
    finally:
        case.cleanup()

    assert {identifier: entry.activation_state for identifier, entry in entries.items()} == {
        "active-extension": "active",
        "disabled-extension": "disabled",
        "failed-extension": "activation-failed",
        "inactive-extension": "inactive",
        "legacy-active": "active",
    }
    assert entries["failed-extension"].activation_diagnostic == "Synthetic activation failed."
    assert all(
        entry.activation_diagnostic is None for identifier, entry in entries.items() if identifier != "failed-extension"
    )
    assert all(entry.health.state == "healthy" for entry in entries.values())


def test_problem_projection_unknown_activation_is_invalid_metadata_but_inactive(tmp_path: Path) -> None:
    case = CASES.build_unknown_activation_case(_session_temp(tmp_path))
    try:
        (entry,) = _load(case)
    finally:
        case.cleanup()

    assert entry.activation_state == "inactive"
    assert entry.activation_diagnostic is None
    assert entry.health.state == "invalid"
    assert _codes(entry) == ["invalid-activation-state"]


@pytest.mark.parametrize(
    ("builder", "expected_code"),
    [
        ("build_malformed_case", "manifest-invalid"),
        ("build_unreadable_case", "manifest-unreadable"),
    ],
)
def test_problem_projection_malformed_observation_is_retained_without_hiding_healthy_rows(
    tmp_path: Path,
    builder: str,
    expected_code: str,
) -> None:
    case = getattr(CASES, builder)(_session_temp(tmp_path))
    try:
        entries = _load(case)
    finally:
        case.cleanup()

    invalid = [entry for entry in entries if entry.health.state == "invalid"]
    assert len(invalid) == 1
    assert invalid[0].id is None
    assert invalid[0].fallback_identity == invalid[0].source_locations[0]
    assert _codes(invalid[0]) == [expected_code]
    if builder == "build_malformed_case":
        healthy = [entry for entry in entries if entry.health.state == "healthy"]
        assert [entry.id for entry in healthy] == ["healthy-extension"]


def test_problem_projection_missing_id_uses_canonical_source_fallback(tmp_path: Path) -> None:
    case = CASES.build_missing_id_case(_session_temp(tmp_path))
    try:
        (entry,) = _load(case)
    finally:
        case.cleanup()

    assert entry.id is None
    assert entry.fallback_identity == ".specify/extensions/missing-id"
    assert entry.source_locations == (entry.fallback_identity,)
    assert entry.name == "Missing Identity"
    assert entry.health.state == "invalid"
    assert _codes(entry) == ["missing-stable-id"]
    assert entry.catalog_sources == ()
    assert entry.available_versions == ()


def test_problem_projection_source_aliases_coalesce_before_stable_id_grouping(tmp_path: Path) -> None:
    case = CASES.build_source_alias_case(_session_temp(tmp_path))
    try:
        (entry,) = _load(case)
    finally:
        case.cleanup()

    assert entry.id == "alias-extension"
    assert entry.source_locations == (".specify/extensions/alias",)
    assert len(entry.evidence) == 3
    assert entry.conflict is False
    assert entry.health.state == "healthy"


def test_problem_projection_resolvable_symlink_alias_coalesces_when_supported(tmp_path: Path) -> None:
    case = CASES.build_symlink_alias_case(_session_temp(tmp_path))
    if not case.symlink_supported:
        case.cleanup()
        pytest.skip("directory symlink creation is unavailable")
    try:
        (entry,) = _load(case)
    finally:
        case.cleanup()

    assert entry.id == "symlink-extension"
    assert entry.source_locations == (".specify/extensions/real",)
    assert len(entry.evidence) == 3


@pytest.mark.skipif(os.name != "nt", reason="case aliases coalesce only on case-insensitive platforms")
def test_problem_projection_case_variant_alias_coalesces_on_windows(tmp_path: Path) -> None:
    case = CASES.build_case_variant_case(_session_temp(tmp_path))
    try:
        (entry,) = _load(case)
    finally:
        case.cleanup()

    assert entry.id == "case-extension"
    assert entry.source_locations == (".specify/extensions/CaseSource",)
    assert len(entry.evidence) == 3


def test_problem_projection_distinct_sources_with_duplicate_id_form_one_conflict(tmp_path: Path) -> None:
    case = CASES.build_duplicate_id_case(_session_temp(tmp_path))
    try:
        (entry,) = _load(case)
    finally:
        case.cleanup()

    assert entry.id == "duplicate-extension"
    assert entry.source_locations == (".specify/extensions/first", ".specify/extensions/second")
    assert entry.conflict is True
    assert entry.conflict_reasons == ("duplicate-installed-id",)
    assert entry.health.state == "invalid"
    assert _codes(entry) == ["duplicate-installed-id"]
    assert len(entry.evidence) == 2


def test_problem_projection_same_source_identity_conflict_has_no_authoritative_id(tmp_path: Path) -> None:
    case = CASES.build_same_source_identity_conflict_case(_session_temp(tmp_path))
    try:
        (entry,) = _load(case)
    finally:
        case.cleanup()

    assert entry.id is None
    assert entry.fallback_identity == ".specify/extensions/conflict"
    assert entry.conflict is True
    assert entry.conflict_reasons == ("local-identity-conflict",)
    assert entry.health.state == "invalid"
    assert _codes(entry) == ["local-identity-conflict"]
    assert len(entry.evidence) == 2


def test_problem_projection_equal_names_at_distinct_sources_never_merge(tmp_path: Path) -> None:
    case = CASES.build_same_name_case(_session_temp(tmp_path))
    try:
        entries = _load(case)
    finally:
        case.cleanup()

    assert len(entries) == 2
    assert [entry.name for entry in entries] == ["Same Name", "Same Name"]
    assert [entry.fallback_identity for entry in entries] == [
        ".specify/extensions/first",
        ".specify/extensions/second",
    ]
    assert all(_codes(entry) == ["missing-stable-id"] for entry in entries)


def test_problem_projection_diagnostics_are_deterministic_by_code_then_source(tmp_path: Path) -> None:
    case = CASES.build_unknown_activation_case(_session_temp(tmp_path))
    manifest_path = case.project_root / ".specify" / "extensions" / "unknown" / "extension.yml"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["commands"] = ["valid.command", 42, ""]
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    try:
        (entry,) = _load(case)
    finally:
        case.cleanup()

    diagnostics = [(item.code, item.source) for item in entry.health.diagnostics]
    assert diagnostics == sorted(diagnostics, key=lambda item: (item[0], item[1] or ""))
    assert [code for code, _ in diagnostics] == ["invalid-activation-state", "manifest-invalid"]


def test_problem_projection_marker_mismatch_and_live_root_reject_before_access(tmp_path: Path) -> None:
    from specify_cli.extensions.inventory import load_installed_entries

    case = CASES.build_missing_id_case(_session_temp(tmp_path))
    marker_path = case.project_root / ".spec001-synthetic-fixture.json"
    marker = json.loads(marker_path.read_text(encoding="utf-8"))
    marker["feature"] = "wrong-feature"
    marker_path.write_text(json.dumps(marker), encoding="utf-8")
    try:
        with pytest.raises(ValueError, match="marker binding mismatch"):
            _load(case)
    finally:
        case.cleanup()

    live_root_temp = tmp_path / "live-root"
    live_root_temp.mkdir()
    with pytest.raises(PermissionError, match="beneath the session temporary root"):
        tuple(
            load_installed_entries(
                REPOSITORY_ROOT,
                session_temp=_session_temp(live_root_temp),
                source_digest=CASES.fixture_source_digest(),
                synthetic_mode=True,
            )
        )
