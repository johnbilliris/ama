from __future__ import annotations

import ast
import importlib.util
import sys
from pathlib import Path
from typing import Any, cast

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
SEQUENCE_PATH = REPOSITORY_ROOT / "scripts" / "spec001" / "local_gate_sequence.py"
DISPATCHER_PATH = REPOSITORY_ROOT / "scripts" / "spec001" / "run_local_gates.py"


def _load_module(path: Path, name: str) -> Any:
    specification = importlib.util.spec_from_file_location(name, path)
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    sys.modules[name] = module
    sys.path.insert(0, str(path.parent))
    try:
        specification.loader.exec_module(module)
    finally:
        sys.path.remove(str(path.parent))
    return module


def _sequence() -> Any:
    return _load_module(SEQUENCE_PATH, "spec001_local_gate_sequence")


def _definitions(tmp_path: Path, execution_mode: str) -> tuple[Any, ...]:
    external_temp = tmp_path / execution_mode
    external_temp.mkdir(mode=0o700)
    external_temp.chmod(0o700)
    module = _sequence()
    return cast(tuple[Any, ...], module.assemble_package_commands(REPOSITORY_ROOT, external_temp, execution_mode))


def _definition(definitions: tuple[Any, ...], name: str) -> Any:
    return next(definition for definition in definitions if definition.name == name)


@pytest.mark.parametrize("execution_mode", ["local-synthetic", "sovereign"])
def test_gate_sequence_defines_complete_mode_bound_two_phase_package_gate(tmp_path: Path, execution_mode: str) -> None:
    definitions = _definitions(tmp_path, execution_mode)
    names = tuple(definition.name for definition in definitions)
    assert names == (
        "locked-sync",
        "ruff-check",
        "ruff-format",
        "strict-mypy",
        "package-pytest",
        "wheel-build",
        "clean-install",
        "console-smoke",
        "module-smoke",
        "root-selection",
    )
    assert all(definition.execution_mode == execution_mode for definition in definitions)
    assert all(definition.audit_phases == ("intent", "result") for definition in definitions)
    assert all(definition.route_via_mode_bound_daemon for definition in definitions)


def test_gate_sequence_local_bootstrap_allows_only_proxy_or_cache_and_denies_test_network(tmp_path: Path) -> None:
    definitions = _definitions(tmp_path, "local-synthetic")
    locked_sync = _definition(definitions, "locked-sync")
    assert locked_sync.environment.get("UV_OFFLINE") is None
    assert locked_sync.network_policy == "configured-https-proxy-or-cache"

    for name in ("ruff-check", "ruff-format", "strict-mypy", "package-pytest", "root-selection"):
        definition = _definition(definitions, name)
        assert definition.environment["SPECIFY_CLI_NETWORK_DISABLED"] == "1"
        assert definition.network_policy == "deny-production-and-unapproved"


def test_gate_sequence_sovereign_uv_children_are_offline_and_frozen(tmp_path: Path) -> None:
    definitions = _definitions(tmp_path, "sovereign")
    for definition in definitions:
        if definition.argv[:2] == ("uv", "run"):
            assert definition.environment["UV_FROZEN"] == "1"
            assert definition.environment["UV_OFFLINE"] == "1"
        if (
            definition.argv
            and definition.argv[0] == "uv"
            and definition.name
            in {
                "locked-sync",
                "wheel-build",
                "clean-install",
            }
        ):
            assert definition.environment["UV_OFFLINE"] == "1"
            assert "--offline" in definition.argv


def test_gate_sequence_sovereign_environment_rejects_all_feature_controls() -> None:
    dispatcher = _load_module(DISPATCHER_PATH, "spec001_dispatcher_for_sequence")
    dispatcher.validate_sovereign_environment({})
    for name in ("SPEC001_TEST_MODE", "SPEC001_EXTERNAL_TRANSPORT", "SPEC001_UNKNOWN", "SPECIFY_CLI_UNKNOWN"):
        with pytest.raises(ValueError, match="sovereign mode rejects"):
            dispatcher.validate_sovereign_environment({name: "synthetic"})


def test_gate_sequence_quality_children_select_dev_extra_and_external_caches(tmp_path: Path) -> None:
    definitions = _definitions(tmp_path, "sovereign")
    for name in ("ruff-check", "ruff-format", "strict-mypy", "package-pytest"):
        argv = _definition(definitions, name).argv
        assert argv[:2] == ("uv", "run")
        assert argv[argv.index("--project") + 1] == "tools/specify-cli"
        assert argv[argv.index("--extra") + 1] == "dev"

    mypy = _definition(definitions, "strict-mypy")
    assert Path(mypy.environment["MYPY_CACHE_DIR"]).is_relative_to(tmp_path)
    assert not Path(mypy.environment["MYPY_CACHE_DIR"]).is_relative_to(REPOSITORY_ROOT)

    pytest_definition = _definition(definitions, "package-pytest")
    assert pytest_definition.environment["PYTEST_ADDOPTS"] == "-pno:cacheprovider"
    assert Path(pytest_definition.environment["COVERAGE_FILE"]).is_relative_to(tmp_path)
    assert Path(pytest_definition.environment["COVERAGE_RCFILE"]).is_relative_to(tmp_path)
    assert any(argument.startswith("--cov-report=xml:") for argument in pytest_definition.argv)
    assert "--cov-branch" in pytest_definition.argv
    assert "--cov-fail-under=90" in pytest_definition.argv

    root = _definition(definitions, "root-selection")
    assert root.argv[:4] == ("uv", "run", "--no-sync", "pytest")
    assert root.environment["PYTEST_ADDOPTS"] == "-pno:cacheprovider"


def test_gate_sequence_guards_all_repository_quality_outputs(tmp_path: Path) -> None:
    definitions = _definitions(tmp_path, "local-synthetic")
    expected = {
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
    assert all(set(definition.repository_mutation_guards) == expected for definition in definitions)


def test_gate_sequence_coverage_parser_requires_independent_numeric_line_threshold(tmp_path: Path) -> None:
    module = _sequence()
    report = tmp_path / "package-coverage.xml"
    report.write_text('<coverage line-rate="0.9001" branch-rate="0.5"/>', encoding="utf-8")
    assert module.parse_package_coverage(report) == pytest.approx(90.01)

    report.write_text('<coverage line-rate="0.8999" branch-rate="1.0"/>', encoding="utf-8")
    with pytest.raises(ValueError, match="90.00"):
        module.parse_package_coverage(report)
    report.write_text('<coverage branch-rate="1.0"/>', encoding="utf-8")
    with pytest.raises(ValueError, match="line-rate"):
        module.parse_package_coverage(report)


def test_gate_sequence_boundaries_are_pure_and_do_not_own_root_regression() -> None:
    source = SEQUENCE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(SEQUENCE_PATH))
    functions = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}
    assert {"assemble_package_commands", "parse_package_coverage", "run_local_gate_sequence"} <= functions.keys()
    assembly_calls = {
        node.func.id
        for node in ast.walk(functions["run_local_gate_sequence"])
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    assert {"assemble_package_commands", "parse_package_coverage"} <= assembly_calls
    assert "root_regression" not in source
    assert "subprocess" not in source
    assert ".run(" not in source
