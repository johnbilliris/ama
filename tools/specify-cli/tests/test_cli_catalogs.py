from __future__ import annotations

import importlib.util
import json
import os
import stat
from pathlib import Path
from types import ModuleType
from typing import Protocol, cast

import pytest
from typer.testing import CliRunner

# isort: split
from specify_cli.cli import app
from specify_cli.daemon_protocol import ClientResponse, ListRequest


def _load_cases() -> ModuleType:
    fixture_path = Path(__file__).resolve().parent / "fixtures" / "catalog_local_cases.py"
    spec = importlib.util.spec_from_file_location("spec001_cli_catalog_cases", fixture_path)
    if spec is None or spec.loader is None:
        raise ImportError("cannot load catalog fixture builder")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


CASES = _load_cases()


class _CatalogCase(Protocol):
    discovery_start: Path
    extensions_root: Path
    session_temp: Path
    source_digest: str

    def cleanup(self) -> None: ...


def _session_temp(tmp_path: Path) -> Path:
    session_temp = tmp_path / "session"
    session_temp.mkdir(mode=0o700)
    session_temp.chmod(0o700)
    if os.name != "nt":
        assert stat.S_IMODE(session_temp.stat().st_mode) == 0o700
    return session_temp


def _materialize_combined_case(tmp_path: Path) -> _CatalogCase:
    case = CASES.build_catalog_conflict_case(_session_temp(tmp_path))
    manifests = {
        "shared": {
            "id": "shared-extension",
            "name": "Installed Shared",
            "version": "2.0.0",
            "commands": ["shared.run"],
        },
        "local-only": {
            "id": "local-only",
            "name": "Local Only",
            "version": "1.0.0",
            "commands": [],
        },
    }
    for directory, manifest in manifests.items():
        target = case.extensions_root / directory / "extension.yml"
        target.parent.mkdir(parents=True)
        target.write_text(json.dumps(manifest), encoding="utf-8")
    return cast(_CatalogCase, case)


def _response(case: _CatalogCase, view: str, *, output_json: bool = True) -> ClientResponse:
    from specify_cli.daemon import handle_extension_request
    from specify_cli.extensions.catalogs import collect_catalog_records
    from specify_cli.extensions.inventory import load_installed_entries

    return handle_extension_request(
        ListRequest(view=view, output_json=output_json, discovery_start=case.discovery_start),
        session_id="catalog-cli-session",
        execution_mode="local-synthetic",
        installed_loader=lambda start: load_installed_entries(
            start,
            session_temp=case.session_temp,
            source_digest=case.source_digest,
            synthetic_mode=True,
        ),
        catalog_loader=lambda start: collect_catalog_records(
            start,
            session_temp=case.session_temp,
            source_digest=case.source_digest,
            synthetic_mode=True,
        ),
    )


def test_catalog_cli_available_and_all_views_are_complete_and_deterministic(tmp_path: Path) -> None:
    case = _materialize_combined_case(tmp_path)
    try:
        available = _response(case, "available")
        all_extensions = _response(case, "all")
    finally:
        case.cleanup()

    available_rows = json.loads(available.stdout)
    all_rows = json.loads(all_extensions.stdout)
    assert available.exit_code == 0
    assert available.stderr == ""
    assert [row["id"] for row in available_rows] == ["shared-extension"]
    assert available_rows[0]["source"]["kind"] == "combined"
    assert available_rows[0]["installed"] is True
    assert [row["id"] for row in all_rows] == ["shared-extension", "local-only"]


def test_catalog_cli_any_source_failure_discards_every_catalog_row_and_warns_once(tmp_path: Path) -> None:
    case = _materialize_combined_case(tmp_path)
    failed_source = case.extensions_root / "catalogs" / "bravo.json"
    failed_source.write_text('{"schema_version":"1.0","extensions":[', encoding="utf-8")
    try:
        response = _response(case, "all")
    finally:
        case.cleanup()

    rows = json.loads(response.stdout)
    assert response.exit_code == 0
    assert [row["id"] for row in rows] == ["shared-extension", "local-only"]
    assert all(row["source"]["kind"] == "local" for row in rows)
    assert response.stderr == "Catalog unavailable: source is invalid.\n"


def test_catalog_cli_available_failure_has_scope_empty_state_and_one_warning(tmp_path: Path) -> None:
    case = _materialize_combined_case(tmp_path)
    failed_source = case.extensions_root / "catalogs" / "alpha.json"
    failed_source.write_text("not json", encoding="utf-8")
    try:
        response = _response(case, "available", output_json=False)
    finally:
        case.cleanup()

    assert response.exit_code == 0
    assert response.stdout == "No catalog extensions available.\n"
    assert response.stderr == "Catalog unavailable: source is invalid.\n"


def test_catalog_cli_client_preserves_success_streams(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    import specify_cli.daemon_client as daemon_client

    case = _materialize_combined_case(tmp_path)
    try:
        response = _response(case, "all", output_json=False)
    finally:
        case.cleanup()
    monkeypatch.setattr(daemon_client, "request_extension_list", lambda **_: response)

    result = CliRunner().invoke(app, ["extension", "list", "--all"], catch_exceptions=False)

    assert result.exit_code == 0
    assert result.stdout == response.stdout
    assert result.stderr == response.stderr
