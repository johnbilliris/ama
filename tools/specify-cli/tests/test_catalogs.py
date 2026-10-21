from __future__ import annotations

import importlib.util
import json
import os
import stat
from copy import deepcopy
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]


def _load_fixture(name: str) -> ModuleType:
    fixture_path = Path(__file__).resolve().parent / "fixtures" / name
    spec = importlib.util.spec_from_file_location(f"spec001_{fixture_path.stem}", fixture_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load fixture builder: {name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


LOCAL_CASES = _load_fixture("catalog_local_cases.py")
REMOTE_CASES = _load_fixture("catalog_remote_cases.py")


def _session_temp(tmp_path: Path) -> Path:
    session_temp = tmp_path / "session"
    session_temp.mkdir(mode=0o700)
    session_temp.chmod(0o700)
    if os.name != "nt":
        assert stat.S_IMODE(session_temp.stat().st_mode) == 0o700
    return session_temp


def _collect(case: Any) -> Any:
    from specify_cli.extensions.catalogs import collect_catalog_records

    return collect_catalog_records(
        case.discovery_start,
        session_temp=case.session_temp,
        source_digest=case.source_digest,
        synthetic_mode=True,
    )


def test_catalog_contract_local_boundary_is_schema_validated_before_records_exist(tmp_path: Path) -> None:
    case = LOCAL_CASES.build_local_catalog_boundary_case(_session_temp(tmp_path))
    try:
        result = _collect(case)
    finally:
        case.cleanup()

    assert result.warning is None
    assert len(result.records) == 1_000
    assert result.records[0].available_version is None
    assert result.records[-1].stable_id == "catalog-extension-0999"
    assert all(record.catalog_name == "boundary" for record in result.records)


def test_catalog_contract_duplicate_configuration_name_rejects_before_source_access(tmp_path: Path) -> None:
    case = LOCAL_CASES.build_catalog_conflict_case(_session_temp(tmp_path))
    config = json.loads(case.catalog_config.read_text(encoding="utf-8"))
    config["catalogs"][1]["name"] = "alpha"
    config["catalogs"][0]["path"] = "catalogs/does-not-exist.json"
    config["catalogs"][1]["path"] = "catalogs/also-does-not-exist.json"
    case.catalog_config.write_text(json.dumps(config), encoding="utf-8")
    try:
        result = _collect(case)
    finally:
        case.cleanup()

    assert result.records == ()
    assert result.warning == "Catalog unavailable: duplicate catalog name."


@pytest.mark.parametrize(
    "entry",
    [
        {"name": "http", "priority": 1, "url": "http://127.0.0.1/catalog.json"},
        {"name": "public", "priority": 1, "url": "https://example.test/catalog.json"},
        {
            "name": "missing-scope",
            "priority": 1,
            "url": "https://spec001catalog.blob.core.windows.net/extensions/catalog.json",
            "storage_account_resource_id": REMOTE_CASES.ACCOUNT_SCOPE,
        },
    ],
)
def test_catalog_contract_rejects_non_private_azure_blob_remote_shapes_atomically(
    tmp_path: Path,
    entry: dict[str, object],
) -> None:
    case = LOCAL_CASES.materialize_catalog_fixture(
        _session_temp(tmp_path),
        "invalid-remote",
        catalogs=[entry],
        sources={},
    )
    try:
        result = _collect(case)
    finally:
        case.cleanup()

    assert result.records == ()
    assert result.warning == "Catalog unavailable: configuration is invalid."


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("location", "eastus", "Australian region"),
        ("public_network_access", "Enabled", "public access"),
        ("default_action", "Allow", "default Deny"),
        ("approved_private_endpoint", False, "private endpoint"),
        ("blob_host", "wrong.blob.core.windows.net", "host"),
        ("private_addresses", ["20.1.2.3"], "private DNS"),
    ],
)
def test_catalog_contract_remote_preconditions_fail_closed_before_transport(
    field: str,
    value: object,
    message: str,
) -> None:
    from specify_cli.extensions.catalogs import validate_remote_catalog_access

    entry = REMOTE_CASES.remote_catalog_entry()
    preconditions = REMOTE_CASES.private_au_storage_preconditions()
    preconditions[field] = value
    with pytest.raises(PermissionError, match=message):
        validate_remote_catalog_access(entry, preconditions, reader_authorized=True)


def test_catalog_contract_remote_requires_successful_shared_reader_decision() -> None:
    from specify_cli.extensions.catalogs import validate_remote_catalog_access

    with pytest.raises(PermissionError, match="Reader authorization"):
        validate_remote_catalog_access(
            REMOTE_CASES.remote_catalog_entry(),
            REMOTE_CASES.private_au_storage_preconditions(),
            reader_authorized=False,
        )


def test_catalog_contract_remote_accepts_complete_private_au_preconditions() -> None:
    from specify_cli.extensions.catalogs import validate_remote_catalog_access

    validate_remote_catalog_access(
        REMOTE_CASES.remote_catalog_entry(),
        REMOTE_CASES.private_au_storage_preconditions(),
        reader_authorized=True,
    )


def test_catalog_contract_marker_mismatch_symlink_escape_and_live_root_reject_before_access(tmp_path: Path) -> None:
    from specify_cli.extensions.catalogs import collect_catalog_records

    session_temp = _session_temp(tmp_path)
    case = LOCAL_CASES.build_catalog_conflict_case(session_temp)
    marker_path = case.project_root / LOCAL_CASES.MARKER_NAME
    marker = json.loads(marker_path.read_text(encoding="utf-8"))
    marker["source_digest"] = "0" * 64
    marker_path.write_text(json.dumps(marker), encoding="utf-8")
    try:
        with pytest.raises(PermissionError, match="source digest mismatch"):
            _collect(case)
    finally:
        case.cleanup()

    with pytest.raises(PermissionError, match="beneath the session temporary root"):
        collect_catalog_records(
            REPOSITORY_ROOT,
            session_temp=session_temp,
            source_digest=LOCAL_CASES.catalog_fixture_source_digest(),
            synthetic_mode=True,
        )


def test_catalog_contract_remote_rejects_mismatched_resource_scope_and_malformed_private_dns() -> None:
    from specify_cli.extensions.catalogs import validate_remote_catalog_access

    entry = REMOTE_CASES.remote_catalog_entry()
    preconditions = REMOTE_CASES.private_au_storage_preconditions()

    invalid_entry = deepcopy(entry)
    invalid_entry["url"] = "http://spec001catalog.blob.core.windows.net/extensions/catalog.json"
    with pytest.raises(PermissionError, match="host"):
        validate_remote_catalog_access(invalid_entry, preconditions, reader_authorized=True)

    invalid_entry = deepcopy(entry)
    invalid_entry["container_scope"] = f"{REMOTE_CASES.ACCOUNT_SCOPE}/blobServices/default/other"
    with pytest.raises(PermissionError, match="container scope"):
        validate_remote_catalog_access(invalid_entry, preconditions, reader_authorized=True)

    invalid_preconditions = deepcopy(preconditions)
    invalid_preconditions["account_resource_id"] = (
        "/subscriptions/other/resourceGroups/rg/providers/Microsoft.Storage/storageAccounts/other"
    )
    with pytest.raises(PermissionError, match="resource mismatch"):
        validate_remote_catalog_access(entry, invalid_preconditions, reader_authorized=True)

    for addresses, message in (("10.0.0.4", "required"), ([], "required"), (["not-an-ip"], "invalid")):
        invalid_preconditions = deepcopy(preconditions)
        invalid_preconditions["private_addresses"] = addresses
        with pytest.raises(PermissionError, match=message):
            validate_remote_catalog_access(entry, invalid_preconditions, reader_authorized=True)


def test_catalog_contract_no_root_or_configuration_returns_no_records(tmp_path: Path) -> None:
    from specify_cli.extensions.catalogs import collect_catalog_records

    session_temp = _session_temp(tmp_path)
    no_root = session_temp / "no-project"
    no_root.mkdir()
    result = collect_catalog_records(
        no_root,
        session_temp=session_temp,
        source_digest=LOCAL_CASES.catalog_fixture_source_digest(),
        synthetic_mode=True,
    )
    assert result.records == ()
    assert result.warning is None

    case = LOCAL_CASES.build_catalog_conflict_case(session_temp)
    case.catalog_config.unlink()
    try:
        result = _collect(case)
    finally:
        case.cleanup()
    assert result.records == ()
    assert result.warning is None


def test_catalog_contract_unavailable_or_invalid_local_source_is_atomic(tmp_path: Path) -> None:
    session_temp = _session_temp(tmp_path)
    case = LOCAL_CASES.materialize_catalog_fixture(
        session_temp,
        "missing-source",
        catalogs=[{"name": "missing", "priority": 1, "path": "catalogs/missing.json"}],
        sources={},
    )
    try:
        result = _collect(case)
    finally:
        case.cleanup()
    assert result.records == ()
    assert result.warning == "Catalog unavailable: source is invalid."

    case = LOCAL_CASES.materialize_catalog_fixture(
        session_temp,
        "invalid-utf8",
        catalogs=[{"name": "invalid", "priority": 1, "path": "catalogs/invalid.json"}],
        sources={
            ".specify/extensions/catalogs/invalid.json": {
                "schema_version": "1.0",
                "extensions": [],
            }
        },
    )
    source_path = case.extensions_root / "catalogs" / "invalid.json"
    source_path.write_bytes(b"\xff")
    try:
        result = _collect(case)
    finally:
        case.cleanup()
    assert result.records == ()
    assert result.warning == "Catalog unavailable: source is invalid."
