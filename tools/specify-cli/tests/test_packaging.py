from __future__ import annotations

import ast
import json
import os
import subprocess
import sys
import tempfile
import tomllib
import zipfile
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_METADATA = PACKAGE_ROOT / "pyproject.toml"
PACKAGE_README = PACKAGE_ROOT / "README.md"
PACKAGE_SOURCE = PACKAGE_ROOT / "src" / "specify_cli"

RUNTIME_DEPENDENCIES = {
    "typer>=0.12,<1",
    "rich>=13,<15",
    "pyyaml>=6,<7",
    "requests>=2.32,<3",
    "jsonschema>=4.23,<5",
    "rfc8785>=0.1.4,<1",
    "cryptography>=44,<47",
    "azure-identity>=1.19,<2",
    "azure-storage-blob>=12.24,<13",
    "azure-mgmt-resource>=23.1,<24",
    "azure-mgmt-authorization>=4,<5",
    "azure-keyvault-keys>=4.10,<5",
}
DEV_DEPENDENCIES = {
    "hatchling>=1.27,<2",
    "pytest>=8,<9",
    "ruff>=0.8,<1",
    "mypy>=1.14,<2",
    "pytest-cov>=6,<8",
    "types-pyyaml>=6.0.12,<7",
    "types-requests>=2.32,<3",
}
FORBIDDEN_IPC_DEPENDENCY_PREFIXES = (
    "pywin32",
    "pywin32-ctypes",
    "posix-ipc",
    "sysv-ipc",
    "python-daemon",
)
FORBIDDEN_COLD_CLIENT_IMPORTS = ("azure", "cryptography", "jsonschema", "requests")
COLD_CLIENT_MODULES = (
    "__init__.py",
    "__main__.py",
    "cli.py",
    "daemon_client.py",
    "daemon_protocol.py",
)
CURRENT_WHEEL_MODULES = {
    "specify_cli/__init__.py",
    "specify_cli/__main__.py",
    "specify_cli/azure_authorization.py",
    "specify_cli/cli.py",
    "specify_cli/daemon.py",
    "specify_cli/daemon_client.py",
    "specify_cli/daemon_protocol.py",
    "specify_cli/evidence.py",
    "specify_cli/trusted_attestation_keys.json",
    "specify_cli/extensions/__init__.py",
    "specify_cli/extensions/catalogs.py",
    "specify_cli/extensions/inventory.py",
    "specify_cli/extensions/models.py",
    "specify_cli/extensions/rendering.py",
}


def _metadata() -> dict[str, object]:
    assert PACKAGE_METADATA.is_file(), "package metadata is absent"
    return tomllib.loads(PACKAGE_METADATA.read_text(encoding="utf-8"))


def _normalized_requirements(requirements: object) -> set[str]:
    assert isinstance(requirements, list)
    return {str(requirement).replace(" ", "").lower() for requirement in requirements}


def _table(parent: object, key: str) -> dict[str, object]:
    assert isinstance(parent, dict)
    value = parent[key]
    assert isinstance(value, dict)
    return value


def _top_level_imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    imports: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".", 1)[0])
    return imports


def test_packaging_metadata_declares_exact_runtime_and_development_contract() -> None:
    metadata = _metadata()
    project = _table(metadata, "project")
    assert project["requires-python"] == ">=3.12"
    assert project["readme"] == "README.md"
    assert _normalized_requirements(project["dependencies"]) == RUNTIME_DEPENDENCIES

    optional_dependencies = _table(project, "optional-dependencies")
    development = _normalized_requirements(optional_dependencies["dev"])
    assert development == DEV_DEPENDENCIES
    assert not any(
        requirement.startswith(FORBIDDEN_IPC_DEPENDENCY_PREFIXES) for requirement in RUNTIME_DEPENDENCIES | development
    )

    build_system = _table(metadata, "build-system")
    assert _normalized_requirements(build_system["requires"]) == {"hatchling>=1.27,<2"}
    assert build_system["build-backend"] == "hatchling.build"


def test_packaging_metadata_owns_readme_script_index_and_wheel_layout() -> None:
    metadata = _metadata()
    project = _table(metadata, "project")
    assert PACKAGE_README.is_file(), "package README is absent"
    assert _table(project, "scripts") == {"ama-specify": "specify_cli.cli:app"}

    tool = _table(metadata, "tool")
    indexes = _table(tool, "uv")["index"]
    assert indexes == [
        {
            "name": "microsoft-package-feed-proxy",
            "url": "https://packagefeedproxy.microsoft.io/pypi/simple",
            "default": True,
        }
    ]

    hatch = _table(tool, "hatch")
    build = _table(hatch, "build")
    wheel = _table(_table(build, "targets"), "wheel")
    assert wheel["packages"] == ["src/specify_cli"]
    assert build["artifacts"] == ["src/specify_cli/trusted_attestation_keys.json"]
    assert "force-include" not in wheel


def test_packaging_metadata_configures_package_quality_without_repository_outputs() -> None:
    tool = _table(_metadata(), "tool")

    pytest_options = _table(tool, "pytest")["ini_options"]
    assert isinstance(pytest_options, dict)
    assert pytest_options["testpaths"] == ["tests"]
    assert pytest_options["addopts"] == [
        "--import-mode=importlib",
        "--strict-config",
        "--strict-markers",
    ]

    ruff = _table(tool, "ruff")
    assert ruff["target-version"] == "py312"
    assert ruff["line-length"] == 120
    assert _table(ruff, "lint")["select"] == ["E", "F", "I", "UP"]

    mypy = _table(tool, "mypy")
    assert mypy["python_version"] == "3.12"
    assert mypy["strict"] is True

    coverage = _table(tool, "coverage")
    coverage_run = _table(coverage, "run")
    assert coverage_run["branch"] is True
    assert coverage_run["source"] == ["specify_cli"]
    assert coverage_run["relative_files"] is True
    assert "data_file" not in coverage_run
    assert "xml" not in coverage
    assert _table(coverage, "report")["fail_under"] == 90


def test_packaging_cold_client_keeps_heavy_runtime_imports_daemon_side() -> None:
    for module_name in COLD_CLIENT_MODULES:
        module_path = PACKAGE_SOURCE / module_name
        if module_path.is_file():
            assert _top_level_imports(module_path).isdisjoint(FORBIDDEN_COLD_CLIENT_IMPORTS)


def test_clean_wheel_installs_externally_owns_both_entry_points_without_shadowing_specify() -> None:
    with tempfile.TemporaryDirectory(prefix="spec001-clean-wheel-") as raw_directory:
        external_root = Path(raw_directory)
        external_root.chmod(0o700)
        wheel_directory = external_root / "wheel"
        environment_directory = external_root / "venv"
        wheel_directory.mkdir()
        build_environment = os.environ.copy()
        build_environment["VIRTUAL_ENV"] = sys.prefix

        subprocess.run(
            [
                "uv",
                "build",
                "--wheel",
                "--no-build-isolation",
                "--out-dir",
                str(wheel_directory),
                str(PACKAGE_ROOT),
            ],
            cwd=external_root,
            env=build_environment,
            check=True,
            capture_output=True,
            text=True,
        )
        wheels = list(wheel_directory.glob("*.whl"))
        assert len(wheels) == 1
        wheel = wheels[0]
        with zipfile.ZipFile(wheel) as archive:
            package_resources = {
                name for name in archive.namelist() if name.startswith("specify_cli/") and not name.endswith("/")
            }
        assert package_resources == CURRENT_WHEEL_MODULES

        sync_environment = os.environ.copy()
        sync_environment["UV_PROJECT_ENVIRONMENT"] = str(environment_directory)
        sync_environment.pop("UV_FROZEN", None)
        subprocess.run(
            ["uv", "sync", "--project", str(PACKAGE_ROOT), "--locked", "--offline"],
            cwd=external_root,
            env=sync_environment,
            check=True,
            capture_output=True,
            text=True,
        )
        installed_python = environment_directory / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        installed_console = environment_directory / (
            "Scripts/ama-specify.exe" if os.name == "nt" else "bin/ama-specify"
        )
        shadow_console = environment_directory / ("Scripts/specify.exe" if os.name == "nt" else "bin/specify")
        subprocess.run(
            ["uv", "pip", "install", "--offline", "--no-deps", "--python", str(installed_python), str(wheel)],
            cwd=external_root,
            check=True,
            capture_output=True,
            text=True,
        )

        for command in ([str(installed_console), "--help"], [str(installed_python), "-m", "specify_cli", "--help"]):
            completed = subprocess.run(
                command,
                cwd=external_root,
                check=True,
                capture_output=True,
                text=True,
            )
            assert "extension" in completed.stdout
            assert completed.stderr == ""

        assert not shadow_console.exists()
        probe = subprocess.run(
            [
                str(installed_python),
                "-c",
                "import importlib.util,json; print(json.dumps(importlib.util.find_spec('specify') is None))",
            ],
            cwd=external_root,
            check=True,
            capture_output=True,
            text=True,
        )
        assert json.loads(probe.stdout) is True

        trust_probe = subprocess.run(
            [
                str(installed_python),
                "-c",
                (
                    "import importlib.resources,json; "
                    "p=importlib.resources.files('specify_cli').joinpath('trusted_attestation_keys.json'); "
                    "print(json.loads(p.read_text(encoding='utf-8'))['schema_version'])"
                ),
            ],
            cwd=external_root,
            check=True,
            capture_output=True,
            text=True,
        )
        assert trust_probe.stdout.strip() == "1.0"
