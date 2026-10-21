from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

SCRIPT_PATH = Path(__file__).resolve().parents[2] / ".devcontainer" / "install-python-dependencies.py"
SPEC = importlib.util.spec_from_file_location("install_python_dependencies", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
installer = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = installer
SPEC.loader.exec_module(installer)


def test_run_uv_uses_only_the_microsoft_proxy(monkeypatch) -> None:
    monkeypatch.setenv("PIP_EXTRA_INDEX_URL", "https://pypi.org/simple/")
    monkeypatch.setenv("PIP_FIND_LINKS", "https://example.com/wheels/")
    monkeypatch.setenv("UV_INDEX", "https://example.com/simple/")
    monkeypatch.setenv("UV_EXTRA_INDEX_URL", "https://pypi.org/simple/")

    with patch.object(installer.subprocess, "run") as run:
        installer.run_uv(Path("python"), "requests>=2")

    command = run.call_args.args[0]
    environment = run.call_args.kwargs["env"]
    assert command[:6] == [
        "uv",
        "--no-config",
        "pip",
        "install",
        "--default-index",
        installer.PROXY_INDEX_URL,
    ]
    assert environment["PIP_CONFIG_FILE"]
    assert environment["PIP_INDEX_URL"] == installer.PROXY_INDEX_URL
    assert environment["UV_DEFAULT_INDEX"] == installer.PROXY_INDEX_URL
    assert environment["PIP_EXTRA_INDEX_URL"] == ""
    assert environment["PIP_FIND_LINKS"] == ""
    assert environment["UV_INDEX"] == ""
    assert environment["UV_EXTRA_INDEX_URL"] == ""
    assert environment["UV_FIND_LINKS"] == ""
    assert environment["UV_NO_CONFIG"] == "1"


def test_install_dependencies_applies_workspace_overrides(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        '[tool.uv]\noverride-dependencies = ["PyJWT>=2.14.0,<3"]\n',
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(installer, "collect_dependencies", lambda: ["redis-entraid==1.2.1"])
    commands: list[list[str]] = []
    override_contents: list[str] = []
    override_paths: list[Path] = []

    def capture_run(command: list[str], **_kwargs: object) -> None:
        commands.append(command)
        if "--overrides" in command:
            override_path = Path(command[command.index("--overrides") + 1])
            override_contents.append(override_path.read_text(encoding="utf-8"))
            override_paths.append(override_path)

    with patch.object(installer.subprocess, "run", side_effect=capture_run):
        installer.install_dependencies(Path("python"))

    assert override_contents == ["PyJWT>=2.14.0,<3\n"]
    assert len(override_paths) == 1
    assert not override_paths[0].exists()
    assert "--overrides" not in commands[1]
