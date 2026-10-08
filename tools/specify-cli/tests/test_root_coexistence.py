from __future__ import annotations

import importlib.util
import sys
import tomllib
from collections.abc import Mapping
from pathlib import Path
from types import ModuleType
from typing import Protocol, cast

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
SEQUENCE_PATH = REPOSITORY_ROOT / "scripts" / "spec001" / "local_gate_sequence.py"
ROOT_REGRESSION_PATH = REPOSITORY_ROOT / "scripts" / "spec001" / "root_regression.py"


class _Command(Protocol):
    name: str
    argv: tuple[str, ...]
    environment: Mapping[str, str]
    repository_mutation_guards: tuple[str, ...]


class _SequenceModule(Protocol):
    ROOT_SELECTION: tuple[str, ...]

    def assemble_package_commands(
        self, repository_root: Path, external_temp: Path, execution_mode: str
    ) -> tuple[_Command, ...]: ...


class _RootRegressionModule(Protocol):
    ROOT_REGRESSION_COMMAND: tuple[str, ...]

    def capture_repository_cache_state(self, repository_root: Path) -> dict[str, str]: ...

    def compare_repository_cache_state(self, before: dict[str, str], after: dict[str, str]) -> None: ...


def _load_module(path: Path, name: str) -> ModuleType:
    specification = importlib.util.spec_from_file_location(name, path)
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    sys.modules[name] = module
    specification.loader.exec_module(module)
    return module


def _package_commands(tmp_path: Path) -> tuple[_Command, ...]:
    external_temp = tmp_path / "quality"
    external_temp.mkdir(mode=0o700)
    external_temp.chmod(0o700)
    sequence = cast(_SequenceModule, _load_module(SEQUENCE_PATH, "spec001_root_coexistence_sequence"))
    return sequence.assemble_package_commands(REPOSITORY_ROOT, external_temp, "local-synthetic")


def _command(commands: tuple[_Command, ...], name: str) -> _Command:
    return next(command for command in commands if command.name == name)


def test_root_coexistence_assigns_ruff_to_workflow_repository_and_package_owners(tmp_path: Path) -> None:
    workflow = (REPOSITORY_ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    root_ruff = (REPOSITORY_ROOT / "ruff.toml").read_text(encoding="utf-8")
    package = tomllib.loads((REPOSITORY_ROOT / "tools" / "specify-cli" / "pyproject.toml").read_text(encoding="utf-8"))

    assert "ruff check apps tests packages" in workflow
    assert "ruff format --check apps tests packages" in workflow
    assert '"tools/**/*.py"' in root_ruff
    assert package["tool"]["ruff"] == {
        "target-version": "py312",
        "line-length": 120,
        "lint": {"select": ["E", "F", "I", "UP"]},
    }

    commands = _package_commands(tmp_path)
    for name, operation in (("ruff-check", "check"), ("ruff-format", "format")):
        argv = _command(commands, name).argv
        assert argv[:2] == ("uv", "run")
        assert argv[argv.index("--project") + 1] == "tools/specify-cli"
        assert argv[argv.index("--extra") + 1] == "dev"
        assert operation in argv
        assert "tools/specify-cli/src" in argv
        assert "tools/specify-cli/tests" in argv


def test_root_coexistence_excludes_tool_from_root_mypy_coverage_and_import_linter() -> None:
    root = tomllib.loads((REPOSITORY_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert root["tool"]["mypy"]["files"] == ["apps", "packages"]
    assert root["tool"]["coverage"]["run"]["source"] == ["apps", "packages"]
    assert root["tool"]["importlinter"]["root_packages"] == ["apps", "packages"]


def test_root_coexistence_uses_exact_root_selection(tmp_path: Path) -> None:
    sequence = cast(_SequenceModule, _load_module(SEQUENCE_PATH, "spec001_root_coexistence_exact_sequence"))
    root_regression = cast(
        _RootRegressionModule,
        _load_module(ROOT_REGRESSION_PATH, "spec001_root_coexistence_root_regression"),
    )
    root_command = _command(_package_commands(tmp_path), "root-selection")
    assert sequence.ROOT_SELECTION == root_regression.ROOT_REGRESSION_COMMAND
    assert root_command.argv == root_regression.ROOT_REGRESSION_COMMAND


def test_root_coexistence_routes_coverage_and_mypy_externally_and_denies_pytest_cache(tmp_path: Path) -> None:
    commands = _package_commands(tmp_path)
    package_pytest = _command(commands, "package-pytest")
    strict_mypy = _command(commands, "strict-mypy")
    root_selection = _command(commands, "root-selection")

    for definition in (package_pytest, root_selection):
        assert definition.environment["PYTEST_ADDOPTS"] == "-pno:cacheprovider"
        assert Path(definition.environment["COVERAGE_FILE"]).is_relative_to(tmp_path)
        assert Path(definition.environment["COVERAGE_RCFILE"]).is_relative_to(tmp_path)
        assert not Path(definition.environment["COVERAGE_FILE"]).is_relative_to(REPOSITORY_ROOT)
        assert not Path(definition.environment["COVERAGE_RCFILE"]).is_relative_to(REPOSITORY_ROOT)

    mypy_cache = Path(strict_mypy.environment["MYPY_CACHE_DIR"])
    assert mypy_cache.is_relative_to(tmp_path)
    assert not mypy_cache.is_relative_to(REPOSITORY_ROOT)


def test_root_coexistence_guards_repository_coverage_and_recursive_cache_mutation(tmp_path: Path) -> None:
    commands = _package_commands(tmp_path)
    expected_guards = {
        ".coverage",
        ".coverage.*",
        "coverage.xml",
        "package-coverage.xml",
        ".mypy_cache",
        ".pytest_cache",
        "tools/specify-cli/.coverage",
        "tools/specify-cli/.coverage.*",
        "tools/specify-cli/coverage.xml",
        "tools/specify-cli/package-coverage.xml",
        "tools/specify-cli/.mypy_cache",
        "tools/specify-cli/.pytest_cache",
    }
    assert all(set(command.repository_mutation_guards) == expected_guards for command in commands)

    root_regression = cast(
        _RootRegressionModule,
        _load_module(ROOT_REGRESSION_PATH, "spec001_root_coexistence_cache_guard"),
    )
    before = root_regression.capture_repository_cache_state(tmp_path)
    nested_cache = tmp_path / ".mypy_cache" / "nested" / "state.json"
    nested_cache.parent.mkdir(parents=True)
    nested_cache.write_text("changed", encoding="utf-8")
    after = root_regression.capture_repository_cache_state(tmp_path)
    with pytest.raises(RuntimeError, match="coverage or cache state changed"):
        root_regression.compare_repository_cache_state(
            before,
            after,
        )
