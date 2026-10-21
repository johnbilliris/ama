from __future__ import annotations

import argparse
import os
import re
import subprocess
import tempfile
import tomllib
from pathlib import Path

PROJECTS: tuple[tuple[Path, tuple[str, ...]], ...] = (
    (Path("pyproject.toml"), ("dev", "load")),
    (Path("apps/api/pyproject.toml"), ()),
    (Path("apps/agents/pyproject.toml"), ()),
    (Path("apps/ingestion/pyproject.toml"), ()),
    (Path("apps/eval-runner/pyproject.toml"), ()),
    (Path("apps/ingest-runner/pyproject.toml"), ("dev",)),
    (Path("packages/eval-core/pyproject.toml"), ()),
    (Path("packages/eval-dataset/pyproject.toml"), ()),
    (Path("tools/routing_mcp_server/pyproject.toml"), ()),
)

EDITABLE_PROJECTS: tuple[Path, ...] = (
    Path("apps/api"),
    Path("apps/agents"),
    Path("apps/ingestion"),
    Path("apps/eval-runner"),
    Path("apps/ingest-runner"),
    Path("packages/eval-core"),
    Path("packages/eval-dataset"),
    Path("tools/routing_mcp_server"),
)

ADDITIONAL_DEV_DEPENDENCIES: tuple[str, ...] = ("hypothesis>=6.0",)
PROXY_INDEX_URL = "https://packagefeedproxy.microsoft.io/pypi/simple"


def normalise_name(requirement: str) -> str:
    match = re.match(r"\s*([A-Za-z0-9][A-Za-z0-9._-]*)", requirement)
    if match is None:
        raise ValueError(f"Unable to parse dependency name from {requirement!r}")
    return match.group(1).lower().replace("_", "-").replace(".", "-")


def read_project(path: Path) -> dict[str, object]:
    with path.open("rb") as pyproject:
        return tomllib.load(pyproject)["project"]


def collect_dependencies() -> list[str]:
    project_data = [(path, extras, read_project(path)) for path, extras in PROJECTS]
    local_names = {normalise_name(str(project["name"])) for _, _, project in project_data}
    dependencies: list[str] = []

    for _, extras, project in project_data:
        dependencies.extend(
            str(dependency)
            for dependency in project.get("dependencies", [])
            if normalise_name(str(dependency)) not in local_names
        )
        optional_dependencies = project.get("optional-dependencies", {})
        if not isinstance(optional_dependencies, dict):
            raise TypeError("project.optional-dependencies must be a table")
        for extra in extras:
            dependencies.extend(
                str(dependency)
                for dependency in optional_dependencies.get(extra, [])
                if normalise_name(str(dependency)) not in local_names
            )

    return list(dict.fromkeys([*dependencies, *ADDITIONAL_DEV_DEPENDENCIES]))


def collect_uv_overrides() -> tuple[str, ...]:
    with Path("pyproject.toml").open("rb") as pyproject:
        config = tomllib.load(pyproject)
    tool_config = config.get("tool", {})
    if not isinstance(tool_config, dict):
        raise TypeError("tool must be a table")
    uv_config = tool_config.get("uv", {})
    if not isinstance(uv_config, dict):
        raise TypeError("tool.uv must be a table")
    raw_overrides = uv_config.get("override-dependencies", [])
    if not isinstance(raw_overrides, list):
        raise TypeError("tool.uv.override-dependencies must be a list")
    overrides: list[str] = []
    for override in raw_overrides:
        if not isinstance(override, str):
            raise TypeError("tool.uv.override-dependencies entries must be strings")
        overrides.append(override)
    return tuple(overrides)


def package_source_environment() -> dict[str, str]:
    environment = os.environ.copy()
    environment.update(
        {
            "PIP_CONFIG_FILE": os.devnull,
            "PIP_INDEX_URL": PROXY_INDEX_URL,
            "PIP_EXTRA_INDEX_URL": "",
            "PIP_FIND_LINKS": "",
            "UV_DEFAULT_INDEX": PROXY_INDEX_URL,
            "UV_INDEX": "",
            "UV_EXTRA_INDEX_URL": "",
            "UV_FIND_LINKS": "",
            "UV_NO_CONFIG": "1",
        }
    )
    return environment


def run_uv(python: Path, *arguments: str, overrides: tuple[str, ...] = ()) -> None:
    command = [
        "uv",
        "--no-config",
        "pip",
        "install",
        "--default-index",
        PROXY_INDEX_URL,
    ]
    override_path: Path | None = None
    if overrides:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", suffix=".txt", delete=False) as override_file:
            override_file.write("\n".join(overrides))
            override_file.write("\n")
        override_path = Path(override_file.name)
        command.extend(("--overrides", str(override_path)))
    command.extend(("--python", str(python), *arguments))
    try:
        subprocess.run(
            command,
            check=True,
            env=package_source_environment(),
        )
    finally:
        if override_path is not None:
            override_path.unlink(missing_ok=True)


def install_dependencies(python: Path) -> None:
    run_uv(python, *collect_dependencies(), overrides=collect_uv_overrides())
    run_uv(
        python,
        "--no-deps",
        "--upgrade",
        "mem0ai>=2.0.0b2",
    )


def install_editable_projects(python: Path) -> None:
    editable_arguments = [argument for project in EDITABLE_PROJECTS for argument in ("--editable", str(project))]
    run_uv(python, "--no-deps", *editable_arguments)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--python", type=Path, required=True)
    parser.add_argument(
        "--mode",
        choices=("all", "dependencies", "editables"),
        default="all",
    )
    args = parser.parse_args()

    if args.mode in {"all", "dependencies"}:
        install_dependencies(args.python)
    if args.mode in {"all", "editables"}:
        install_editable_projects(args.python)


if __name__ == "__main__":
    main()
