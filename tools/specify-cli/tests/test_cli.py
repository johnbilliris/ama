from __future__ import annotations

import ast
import builtins
import importlib.util
import os
import pydoc
import runpy
import shutil
import stat
import tempfile
from pathlib import Path
from types import ModuleType
from typing import Protocol

import pytest
from typer.testing import CliRunner

# isort: split
from specify_cli.cli import app
from specify_cli.daemon_protocol import AuditReceipt, ClientResponse
from specify_cli.extensions.models import ExtensionListEntry

EMPTY_TEXT = {
    "installed": "No extensions installed.\n",
    "available": "No catalog extensions available.\n",
    "all": "No installed or catalog extensions found.\n",
}
ANSI_ESCAPE = "\x1b["


def _load_installed_output_cases() -> ModuleType:
    fixture_path = Path(__file__).resolve().parent / "fixtures" / "installed_cases.py"
    spec = importlib.util.spec_from_file_location("spec001_installed_output_cases", fixture_path)
    if spec is None or spec.loader is None:
        raise ImportError("cannot load installed output fixture builder")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


CASES = _load_installed_output_cases()


class _InstalledFixture(Protocol):
    discovery_start: Path
    session_temp: Path
    source_digest: str


def _external_no_root() -> Path:
    directory = Path(tempfile.mkdtemp(prefix="spec001-no-root-"))
    directory.chmod(0o700)
    if os.name != "nt":
        assert stat.S_IMODE(directory.stat().st_mode) == 0o700
    assert not any((ancestor / ".specify" / "extensions").exists() for ancestor in (directory, *directory.parents))
    return directory


def _response(stdout: str) -> ClientResponse:
    return ClientResponse(
        stdout=stdout,
        stderr="",
        exit_code=0,
        audit=AuditReceipt(intent_event_id="intent-1", result_event_id="result-1", outcome="succeeded"),
    )


@pytest.mark.parametrize(
    ("arguments", "view", "expected"),
    [
        (["extension", "list"], "installed", EMPTY_TEXT["installed"]),
        (["extension", "list", "--available"], "available", EMPTY_TEXT["available"]),
        (["extension", "list", "--all"], "all", EMPTY_TEXT["all"]),
        (["extension", "list", "--json"], "installed", "[]\n"),
        (["extension", "list", "--available", "--json"], "available", "[]\n"),
        (["extension", "list", "--all", "--json"], "all", "[]\n"),
    ],
)
def test_no_project_root_all_scopes_are_ipc_only(
    monkeypatch: pytest.MonkeyPatch,
    arguments: list[str],
    view: str,
    expected: str,
) -> None:
    import specify_cli.daemon_client as daemon_client

    external_root = _external_no_root()
    calls: list[tuple[str, bool, Path]] = []

    def fake_request(*, view: str, output_json: bool) -> ClientResponse:
        calls.append((view, output_json, Path.cwd()))
        return _response("[]\n" if output_json else EMPTY_TEXT[view])

    monkeypatch.setattr(daemon_client, "request_extension_list", fake_request)
    original_cwd = Path.cwd()
    monkeypatch.chdir(external_root)
    try:
        result = CliRunner().invoke(app, arguments, catch_exceptions=False, env={"NO_COLOR": "1"})
    finally:
        monkeypatch.chdir(original_cwd)
        shutil.rmtree(external_root)

    assert result.exit_code == 0
    assert result.stdout == expected
    assert result.stderr == ""
    assert calls == [(view, "--json" in arguments, external_root)]


def test_no_project_root_cli_has_no_inventory_or_catalog_fallback() -> None:
    cli_path = Path(__file__).resolve().parents[1] / "src" / "specify_cli" / "cli.py"
    tree = ast.parse(cli_path.read_text(encoding="utf-8"), filename=str(cli_path))
    imported = {alias.name for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names} | {
        node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) and node.module is not None
    }

    assert "specify_cli.extensions.inventory" not in imported
    assert "specify_cli.extensions.catalogs" not in imported
    assert "specify_cli.daemon_client" in imported


def test_no_project_root_runtime_response_requires_linked_audit() -> None:
    from specify_cli.daemon_protocol import ProtocolError, validate_client_response

    with pytest.raises(ProtocolError, match="audit receipt"):
        validate_client_response(ClientResponse(stdout="[]\n", stderr="", exit_code=0, audit=None))


def test_no_project_root_module_entry_point_delegates_to_shared_app(monkeypatch: pytest.MonkeyPatch) -> None:
    import specify_cli.cli as cli

    calls: list[str] = []
    monkeypatch.setattr(cli, "app", lambda: calls.append("called"))

    runpy.run_module("specify_cli", run_name="__main__")

    assert calls == ["called"]


def _installed_entries(case: _InstalledFixture) -> tuple[ExtensionListEntry, ...]:
    from specify_cli.extensions.inventory import load_installed_entries

    return tuple(
        load_installed_entries(
            case.discovery_start,
            session_temp=case.session_temp,
            source_digest=case.source_digest,
            synthetic_mode=True,
        )
    )


def _deny_interaction(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail(*_: object, **__: object) -> None:
        pytest.fail("installed output must not invoke a pager or input prompt")

    monkeypatch.setattr(pydoc, "pager", fail)
    monkeypatch.setattr(builtins, "input", fail)


@pytest.mark.parametrize(("width", "height"), [(80, 24), (40, 12)])
def test_installed_output_oracle_terminal_sizes_are_complete_plain_and_noninteractive(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    width: int,
    height: int,
) -> None:
    from specify_cli.extensions.rendering import render_entries

    session_temp = tmp_path / "session"
    session_temp.mkdir(mode=0o700)
    session_temp.chmod(0o700)
    case = CASES.build_long_output_case(session_temp)
    _deny_interaction(monkeypatch)
    try:
        entries = _installed_entries(case)
        output = render_entries(
            entries,
            view="installed",
            output_json=False,
            width=width,
            color_system=None,
            force_terminal=False,
        )
    finally:
        case.cleanup()

    assert len(output.splitlines()) > height
    assert ANSI_ESCAPE not in output
    assert output.endswith("\n")
    for entry in entries:
        assert output.count(entry.name) == 1
        assert entry.id is not None
        assert output.count(entry.id) == 1
    for label in ("Installed", "Activation", "Health", "Commands", "Hooks"):
        assert output.count(f"{label}:") == len(entries)
    first_row = output.index(entries[0].name)
    assert first_row < output.index("Installed:", first_row)
    assert output.index("Installed:", first_row) < output.index("Activation:", first_row)
    assert output.index("Activation:", first_row) < output.index("Health:", first_row)
    assert output.index("Health:", first_row) < output.index("Commands:", first_row)
    assert output.index("Commands:", first_row) < output.index("Hooks:", first_row)


def test_installed_output_oracle_redirected_stream_is_exact_and_stderr_is_empty(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import specify_cli.daemon_client as daemon_client
    from specify_cli.extensions.rendering import render_entries

    session_temp = tmp_path / "session"
    session_temp.mkdir(mode=0o700)
    session_temp.chmod(0o700)
    case = CASES.build_manifest_case(session_temp)
    _deny_interaction(monkeypatch)
    try:
        entries = _installed_entries(case)
        rendered = render_entries(
            entries,
            view="installed",
            output_json=False,
            width=80,
            color_system=None,
            force_terminal=False,
        )
    finally:
        case.cleanup()

    monkeypatch.setattr(daemon_client, "request_extension_list", lambda **_: _response(rendered))
    result = CliRunner().invoke(
        app,
        ["extension", "list"],
        catch_exceptions=False,
        env={"NO_COLOR": "1", "COLUMNS": "80", "LINES": "24", "PAGER": ""},
    )

    assert result.exit_code == 0
    assert result.stdout == rendered
    assert result.stderr == ""
    assert ANSI_ESCAPE not in result.stdout


def test_installed_output_oracle_narrow_markup_is_escaped_and_text_complete(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from specify_cli.extensions.rendering import render_entries

    session_temp = tmp_path / "session"
    session_temp.mkdir(mode=0o700)
    session_temp.chmod(0o700)
    case = CASES.build_narrow_terminal_case(session_temp)
    _deny_interaction(monkeypatch)
    try:
        output = render_entries(
            _installed_entries(case),
            view="installed",
            output_json=False,
            width=40,
            color_system=None,
            force_terminal=False,
        )
    finally:
        case.cleanup()

    compacted = "".join(output.split())
    assert ANSI_ESCAPE not in output
    assert "[bold]LiteralMarkupExtension" in compacted
    assert "[link=https://invalid.example]text[/link]" in compacted
    assert "Installed: yes" in output
    assert "Activation: inactive" in output
    assert "Health: healthy" in output
    assert "Commands: 1" in output
    assert "Hooks: 1" in output
