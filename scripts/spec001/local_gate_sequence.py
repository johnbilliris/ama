from __future__ import annotations

from dataclasses import dataclass
import math
import os
from pathlib import Path
from types import MappingProxyType
from typing import Callable, Mapping
import xml.etree.ElementTree as ElementTree


EXECUTION_MODES = {"local-synthetic", "sovereign"}
REPOSITORY_MUTATION_GUARDS = (
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
)
ROOT_SELECTION = (
    "uv",
    "run",
    "--no-sync",
    "pytest",
    "tests/unit",
    "tests/contract",
    "tests/integration",
    "tests/simulation",
    "-m",
    "not azure_staging and not azure_foundry_staging and not azure_cosmos_staging and not azure_speech_staging "
    "and not azure_blob_worm_staging and not measurement_staging and not e2e and not load and not locust",
    "--cov=apps",
    "--cov=packages",
    "--cov-report=xml",
    "--cov-report=term",
)


@dataclass(frozen=True)
class PackageCommand:
    name: str
    argv: tuple[str, ...]
    environment: Mapping[str, str]
    execution_mode: str
    network_policy: str
    audit_phases: tuple[str, str] = ("intent", "result")
    route_via_mode_bound_daemon: bool = True
    repository_mutation_guards: tuple[str, ...] = REPOSITORY_MUTATION_GUARDS


def _package_run(*arguments: str, offline: bool) -> tuple[str, ...]:
    options = ("--offline",) if offline else ()
    return ("uv", "run", *options, "--project", "tools/specify-cli", "--extra", "dev", *arguments)


def assemble_package_commands(
    repository_root: Path, external_temp: Path, execution_mode: str
) -> tuple[PackageCommand, ...]:
    if execution_mode not in EXECUTION_MODES:
        raise ValueError("unknown execution mode")
    resolved_root = repository_root.resolve(strict=True)
    resolved_temp = external_temp.resolve(strict=True)
    if resolved_temp.is_relative_to(resolved_root):
        raise ValueError("package quality temporary directory must be external")

    sovereign = execution_mode == "sovereign"
    offline_options = ("--offline",) if sovereign else ()
    quality_environment = {
        "SPECIFY_CLI_NETWORK_DISABLED": "1",
        "UV_FROZEN": "1",
        **({"UV_OFFLINE": "1"} if sovereign else {}),
    }
    coverage_environment = {
        **quality_environment,
        "COVERAGE_FILE": str(resolved_temp / ".coverage"),
        "COVERAGE_RCFILE": str(resolved_temp / ".coveragerc"),
        "PYTEST_ADDOPTS": "-pno:cacheprovider",
    }
    root_environment = {
        **coverage_environment,
        "MYPY_CACHE_DIR": str(resolved_temp / "mypy-cache"),
    }
    sync_environment = {"UV_OFFLINE": "1"} if sovereign else {}
    network_policy = "deny-production-and-unapproved"
    clean_environment = resolved_temp / "clean-venv"
    installed_python = clean_environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    installed_console = clean_environment / ("Scripts/ama-specify.exe" if os.name == "nt" else "bin/ama-specify")
    wheel_pattern = resolved_root / "tools" / "specify-cli" / "dist" / "*.whl"
    coverage_xml = resolved_temp / "package-coverage.xml"

    def command(
        name: str,
        argv: tuple[str, ...],
        environment: Mapping[str, str],
        policy: str = network_policy,
    ) -> PackageCommand:
        return PackageCommand(
            name=name,
            argv=argv,
            environment=MappingProxyType(dict(environment)),
            execution_mode=execution_mode,
            network_policy=policy,
        )

    return (
        command(
            "locked-sync",
            ("uv", "sync", "--project", "tools/specify-cli", "--extra", "dev", "--locked", *offline_options),
            sync_environment,
            "authorized-au-mirror-cache" if sovereign else "configured-https-proxy-or-cache",
        ),
        command(
            "ruff-check",
            _package_run("ruff", "check", "tools/specify-cli/src", "tools/specify-cli/tests", offline=sovereign),
            quality_environment,
        ),
        command(
            "ruff-format",
            _package_run(
                "ruff", "format", "--check", "tools/specify-cli/src", "tools/specify-cli/tests", offline=sovereign
            ),
            quality_environment,
        ),
        command(
            "strict-mypy",
            _package_run(
                "mypy", "--strict", "tools/specify-cli/src", offline=sovereign
            ),
            {**quality_environment, "MYPY_CACHE_DIR": str(resolved_temp / "mypy-cache")},
        ),
        command(
            "package-pytest",
            _package_run(
                "pytest",
                "-c",
                "tools/specify-cli/pyproject.toml",
                "tools/specify-cli/tests",
                "-q",
                "--cov=specify_cli",
                "--cov-branch",
                "--cov-fail-under=90",
                f"--cov-report=xml:{coverage_xml}",
                offline=sovereign,
            ),
            coverage_environment,
        ),
        command(
            "wheel-build",
            ("uv", "build", "--project", "tools/specify-cli", "--wheel", *offline_options),
            sync_environment,
            "authorized-au-mirror-cache" if sovereign else "configured-https-proxy-or-cache",
        ),
        command(
            "clean-install",
            (
                "uv",
                "pip",
                "install",
                *offline_options,
                "--no-deps",
                "--python",
                str(installed_python),
                str(wheel_pattern),
            ),
            sync_environment,
            "authorized-au-mirror-cache" if sovereign else "configured-https-proxy-or-cache",
        ),
        command("console-smoke", (str(installed_console), "extension", "list", "--json"), quality_environment),
        command(
            "module-smoke",
            (str(installed_python), "-m", "specify_cli", "extension", "list", "--json"),
            quality_environment,
        ),
        command("root-selection", ROOT_SELECTION, root_environment),
    )


def parse_package_coverage(report_path: Path) -> float:
    try:
        root = ElementTree.parse(report_path).getroot()
    except (ElementTree.ParseError, OSError) as error:
        raise ValueError("package coverage XML is unreadable") from error
    raw_line_rate = root.get("line-rate")
    if raw_line_rate is None:
        raise ValueError("package coverage XML requires line-rate")
    try:
        line_rate = float(raw_line_rate)
    except ValueError as error:
        raise ValueError("package coverage line-rate must be numeric") from error
    if not math.isfinite(line_rate) or not 0 <= line_rate <= 1:
        raise ValueError("package coverage line-rate must be between zero and one")
    percentage = line_rate * 100
    if percentage < 90.00:
        raise ValueError("package line coverage must be at least 90.00 percent")
    return percentage


def run_local_gate_sequence(
    repository_root: Path,
    external_temp: Path,
    execution_mode: str,
    guarded_executor: Callable[[PackageCommand], None],
) -> float:
    coverage_percentage: float | None = None
    for command in assemble_package_commands(repository_root, external_temp, execution_mode):
        guarded_executor(command)
        if command.name == "package-pytest":
            coverage_percentage = parse_package_coverage(external_temp.resolve(strict=True) / "package-coverage.xml")
    if coverage_percentage is None:
        raise RuntimeError("package coverage command is absent")
    return coverage_percentage