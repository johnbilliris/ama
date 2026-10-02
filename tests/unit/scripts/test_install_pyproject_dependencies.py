from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path
from unittest.mock import Mock

import pytest

SCRIPT_PATH = Path(__file__).resolve().parents[3] / "scripts" / "install_pyproject_dependencies.py"
SPEC = importlib.util.spec_from_file_location("install_pyproject_dependencies", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
installer = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = installer
SPEC.loader.exec_module(installer)


def test_install_dependencies_passes_each_requirement_to_pip(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        """\
[project]
name = "container-fixture"
version = "0.1.0"
dependencies = ["fastapi>=0.115.0", "PyJWT[crypto]>=2.10.1"]
""",
        encoding="utf-8",
    )
    run = Mock()
    monkeypatch.setattr(subprocess, "run", run)

    installer.install_dependencies(pyproject)

    run.assert_called_once_with(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--no-cache-dir",
            "fastapi>=0.115.0",
            "PyJWT[crypto]>=2.10.1",
        ],
        check=True,
    )


@pytest.mark.parametrize(
    "dependencies",
    [
        "dependencies = []",
        'dependencies = [""]',
    ],
)
def test_load_dependencies_rejects_invalid_manifests(tmp_path: Path, dependencies: str) -> None:
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        f"""\
[project]
name = "container-fixture"
version = "0.1.0"
{dependencies}
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="project"):
        installer.load_dependencies(pyproject)
