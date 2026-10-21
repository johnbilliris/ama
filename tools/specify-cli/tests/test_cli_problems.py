from __future__ import annotations

import builtins
import importlib.util
import json
import os
import pydoc
import stat
from pathlib import Path
from types import ModuleType
from typing import Protocol

import pytest
from typer.testing import CliRunner

# isort: split
from specify_cli.cli import app
from specify_cli.daemon_protocol import AuditReceipt, ClientResponse
from specify_cli.extensions.models import ExtensionListEntry

ANSI_ESCAPE = "\x1b["


def _load_cases() -> ModuleType:
    fixture_path = Path(__file__).resolve().parent / "fixtures" / "problem_cases.py"
    spec = importlib.util.spec_from_file_location("spec001_cli_problem_cases", fixture_path)
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


def _entries(case: _ProblemFixture) -> tuple[ExtensionListEntry, ...]:
    from specify_cli.extensions.inventory import load_installed_entries

    return tuple(
        load_installed_entries(
            case.discovery_start,
            session_temp=case.session_temp,
            source_digest=case.source_digest,
            synthetic_mode=True,
        )
    )


def _render(case: _ProblemFixture, *, width: int = 80) -> str:
    from specify_cli.extensions.rendering import render_entries

    return render_entries(
        _entries(case),
        view="installed",
        output_json=False,
        width=width,
        color_system=None,
        force_terminal=False,
    )


def _response(stdout: str) -> ClientResponse:
    return ClientResponse(
        stdout=stdout,
        stderr="",
        exit_code=0,
        audit=AuditReceipt(intent_event_id="intent-1", result_event_id="result-1", outcome="succeeded"),
    )


def _deny_interaction(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail(*_: object, **__: object) -> None:
        pytest.fail("problem output must not invoke a pager or input prompt")

    monkeypatch.setattr(pydoc, "pager", fail)
    monkeypatch.setattr(builtins, "input", fail)


def test_problem_output_oracle_exact_conflict_text_survives_cli_redirection(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import specify_cli.daemon_client as daemon_client

    case = CASES.build_duplicate_id_case(_session_temp(tmp_path))
    _deny_interaction(monkeypatch)
    try:
        rendered = _render(case)
    finally:
        case.cleanup()

    expected = (
        "Duplicate First\n"
        "ID: duplicate-extension\n"
        "Version: 1.0.0\n"
        "Installed: yes\n"
        "Activation: inactive\n"
        "Health: invalid\n"
        "Conflict: duplicate-installed-id\n"
        "Metadata diagnostic [duplicate-installed-id]: Stable ID is installed from \n"
        "multiple physical sources.\n"
        "Commands: 0\n"
        "Hooks: 0\n"
    )
    assert rendered == expected
    monkeypatch.setattr(daemon_client, "request_extension_list", lambda **_: _response(rendered))

    result = CliRunner().invoke(
        app,
        ["extension", "list"],
        catch_exceptions=False,
        env={"NO_COLOR": "1", "COLUMNS": "80", "LINES": "24", "PAGER": ""},
    )

    assert result.exit_code == 0
    assert result.stdout == expected
    assert result.stderr == ""
    assert ANSI_ESCAPE not in result.stdout


def test_problem_output_oracle_activation_failure_is_separate_from_healthy_metadata(tmp_path: Path) -> None:
    case = CASES.build_activation_states_case(_session_temp(tmp_path))
    try:
        output = _render(case)
    finally:
        case.cleanup()

    failed_start = output.index("Failed Extension")
    failed_end = output.find("\n\n", failed_start)
    failed_row = output[failed_start:] if failed_end < 0 else output[failed_start:failed_end]
    assert "Activation: activation-failed" in failed_row
    assert "Health: healthy" in failed_row
    assert "Activation diagnostic: Synthetic activation failed." in failed_row
    assert "Metadata diagnostic" not in failed_row

    for literal_state in ("disabled", "inactive", "active", "activation-failed"):
        assert f"Activation: {literal_state}" in output


def test_problem_output_oracle_fallback_and_metadata_diagnostic_are_literal(tmp_path: Path) -> None:
    case = CASES.build_missing_id_case(_session_temp(tmp_path))
    try:
        output = _render(case)
    finally:
        case.cleanup()

    assert "Source: .specify/extensions/missing-id" in output
    assert "Activation: inactive" in output
    assert "Health: invalid" in output
    compacted = " ".join(output.split())
    assert "Metadata diagnostic [missing-stable-id]: Extension manifest is missing a stable identifier." in compacted
    assert "Activation diagnostic:" not in output


@pytest.mark.parametrize(("width", "height"), [(80, 24), (40, 12)])
def test_problem_output_oracle_constrained_terminal_is_complete_escaped_and_noninteractive(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    width: int,
    height: int,
) -> None:
    case = CASES.build_unknown_activation_case(_session_temp(tmp_path))
    manifest_path = case.project_root / ".specify" / "extensions" / "unknown" / "extension.yml"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["name"] = "[bold] Literal Problem Extension"
    manifest["description"] = "[link=https://invalid.example]diagnostic markup[/link] remains literal."
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    _deny_interaction(monkeypatch)
    try:
        output = _render(case, width=width)
    finally:
        case.cleanup()

    compacted = "".join(output.split())
    assert ANSI_ESCAPE not in output
    assert output.endswith("\n")
    assert len(output.splitlines()) >= 11
    assert "[bold]LiteralProblemExtension" in compacted
    assert "[link=https://invalid.example]diagnosticmarkup[/link]remainsliteral." in compacted
    for literal in (
        "Activation: inactive",
        "Health: invalid",
        "Metadata diagnostic [invalid-activation-state]: Registry activation state is invalid.",
        "Commands: 0",
        "Hooks: 0",
    ):
        assert literal in output or "".join(literal.split()) in compacted
    assert height > 0
