from __future__ import annotations

import argparse
import re
import sys
import tomllib
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

PROXY_INDEX_URL = "https://packagefeedproxy.microsoft.io/pypi/simple"
PROXY_INDEX_NAME = "microsoft-package-feed-proxy"
MICROSOFT_ARTIFACT_HOST_SUFFIX = ".pkgs.visualstudio.com"
EXCLUDED_DIRECTORIES = {
    ".git",
    ".mypy_cache",
    ".pnpm-store",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    ".venv",
    "node_modules",
}
DEPENDENCY_GROUPS = ("dependencies",)
ONLINE_INSTALL_PATTERN = re.compile(
    r"(?:python\s+-m\s+pip|pip3?|uv\s+pip)\s+install|uv\s+(?:sync|lock)",
    re.IGNORECASE,
)
DIRECT_EXTERNAL_REQUIREMENT_PATTERN = re.compile(
    r"(?:^|\s@\s)(?:https?|git\+https?|hg\+https?|svn\+https?|bzr\+https?)://",
    re.IGNORECASE,
)
CONFIG_FILE_PATTERNS = (
    ".github/workflows/*.yml",
    ".github/workflows/*.yaml",
    ".pre-commit-config.yaml",
    "**/Dockerfile",
    ".devcontainer/Dockerfile",
    "compose.yaml",
    "azure.yaml",
)


@dataclass(frozen=True)
class Violation:
    path: Path
    message: str

    def render(self, root: Path) -> str:
        try:
            display_path = self.path.relative_to(root)
        except ValueError:
            display_path = self.path
        return f"{display_path}: {self.message}"


def _is_excluded(path: Path, root: Path) -> bool:
    relative_parts = path.relative_to(root).parts
    return any(part in EXCLUDED_DIRECTORIES for part in relative_parts)


def _discover(root: Path, name: str) -> list[Path]:
    return sorted(path for path in root.rglob(name) if not _is_excluded(path, root))


def _dependency_strings(project: dict[str, Any]) -> Iterable[str]:
    for dependency in project.get("dependencies", []):
        yield str(dependency)
    for dependencies in project.get("optional-dependencies", {}).values():
        for dependency in dependencies:
            yield str(dependency)


def validate_pyproject(path: Path) -> list[Violation]:
    with path.open("rb") as stream:
        document = tomllib.load(stream)

    violations: list[Violation] = []
    indexes = document.get("tool", {}).get("uv", {}).get("index", [])
    expected_index = {"name": PROXY_INDEX_NAME, "url": PROXY_INDEX_URL, "default": True}
    if indexes != [expected_index]:
        violations.append(Violation(path, f"tool.uv.index must contain only the default {PROXY_INDEX_URL} index"))

    project = document.get("project", {})
    build_system = document.get("build-system", {})
    requirements = [*_dependency_strings(project), *(str(item) for item in build_system.get("requires", []))]
    for requirement in requirements:
        if DIRECT_EXTERNAL_REQUIREMENT_PATTERN.search(requirement):
            violations.append(Violation(path, f"direct external requirement is forbidden: {requirement}"))

    sources = document.get("tool", {}).get("uv", {}).get("sources", {})
    for manager in ("poetry", "pdm"):
        manager_sources = document.get("tool", {}).get(manager, {}).get("source", [])
        if manager_sources:
            violations.append(Violation(path, f"tool.{manager}.source is forbidden; uv proxy policy is authoritative"))

    for package_name, source in sources.items():
        if not isinstance(source, dict):
            violations.append(Violation(path, f"tool.uv.sources.{package_name} must be a table"))
            continue
        external_keys = {"git", "url"}.intersection(source)
        if external_keys:
            violations.append(
                Violation(
                    path, f"tool.uv.sources.{package_name} uses forbidden external source keys: {sorted(external_keys)}"
                )
            )
        if "index" in source and source["index"] != PROXY_INDEX_NAME:
            violations.append(Violation(path, f"tool.uv.sources.{package_name} references a non-proxy index"))

    return violations


def _validate_artifact_url(path: Path, package_name: str, artifact_url: str) -> list[Violation]:
    parsed = urlparse(artifact_url)
    allowed_host = parsed.hostname == "packagefeedproxy.microsoft.io" or (
        parsed.hostname is not None and parsed.hostname.endswith(MICROSOFT_ARTIFACT_HOST_SUFFIX)
    )
    if parsed.scheme != "https" or not allowed_host:
        return [Violation(path, f"package {package_name} has forbidden artifact URL: {artifact_url}")]
    return []


def validate_lockfile(path: Path) -> list[Violation]:
    with path.open("rb") as stream:
        document = tomllib.load(stream)

    violations: list[Violation] = []
    for package in document.get("package", []):
        package_name = str(package.get("name", "<unknown>"))
        source = package.get("source", {})
        if "registry" in source and source["registry"] != PROXY_INDEX_URL:
            violations.append(Violation(path, f"package {package_name} uses forbidden registry {source['registry']}"))
        if any(key in source for key in ("git", "url")):
            violations.append(Violation(path, f"package {package_name} uses a direct external source"))

        sdist = package.get("sdist")
        if isinstance(sdist, dict) and "url" in sdist:
            violations.extend(_validate_artifact_url(path, package_name, str(sdist["url"])))
        for wheel in package.get("wheels", []):
            if isinstance(wheel, dict) and "url" in wheel:
                violations.extend(_validate_artifact_url(path, package_name, str(wheel["url"])))

    return violations


def _config_files(root: Path) -> list[Path]:
    paths: set[Path] = set()
    for pattern in CONFIG_FILE_PATTERNS:
        paths.update(path for path in root.glob(pattern) if path.is_file() and not _is_excluded(path, root))
    return sorted(paths)


def validate_install_surface(path: Path) -> list[Violation]:
    text = path.read_text(encoding="utf-8")
    violations: list[Violation] = []

    if path.name == ".pre-commit-config.yaml":
        remote_repositories = re.findall(r"(?im)^\s*-\s+repo:\s+(https?://\S+)", text)
        allowed_non_python_repositories = {"https://github.com/gitleaks/gitleaks"}
        for repository in remote_repositories:
            if repository not in allowed_non_python_repositories:
                violations.append(Violation(path, f"remote pre-commit package source is forbidden: {repository}"))

    if re.search(r"(?im)^\s*ARG\s+(?:PIP_INDEX_URL|UV_DEFAULT_INDEX)(?:\s*=|\s*$)", text):
        violations.append(Violation(path, "package index must not be caller-overridable through a Docker ARG"))

    forbidden_index_options = re.findall(
        r"--(?:extra-index-url|index-url|default-index|index)\s+(?!https://packagefeedproxy\.microsoft\.io/pypi/simple(?:\s|$))\S+",
        text,
        re.IGNORECASE,
    )
    for option in forbidden_index_options:
        violations.append(Violation(path, f"forbidden package index option: {option}"))

    for variable in (
        "PIP_EXTRA_INDEX_URL",
        "PIP_FIND_LINKS",
        "UV_EXTRA_INDEX_URL",
        "UV_FIND_LINKS",
        "UV_INDEX",
    ):
        assignments = re.findall(rf"(?im)(?:^|\s){variable}\s*[:=]\s*([^\s#]*)", text)
        if any(value.strip("\"'\\") for value in assignments):
            violations.append(Violation(path, f"{variable} must be empty when configured"))

    logical_text = re.sub(r"\\\r?\n\s*", " ", text)
    install_commands = [line for line in logical_text.splitlines() if ONLINE_INSTALL_PATTERN.search(line)]
    for command in install_commands:
        command_without_proxy = command.replace(PROXY_INDEX_URL, "")
        if re.search(
            r"(?:^|\s)(?:https?|git\+https?|hg\+https?|svn\+https?|bzr\+https?)://",
            command_without_proxy,
            re.IGNORECASE,
        ):
            violations.append(Violation(path, f"direct external install URL is forbidden: {command.strip()}"))

    has_online_install = any("--offline" not in command for command in install_commands)
    if has_online_install:
        if PROXY_INDEX_URL not in text:
            violations.append(Violation(path, "online Python install surface does not declare the canonical proxy"))
        if "PIP_CONFIG_FILE" not in text:
            violations.append(
                Violation(path, "online Python install surface does not disable ambient pip configuration")
            )
        if "windows-latest" in text and not re.search(r"(?im)^\s*PIP_CONFIG_FILE:\s*NUL\s*$", text):
            violations.append(Violation(path, "Windows Python install job must use PIP_CONFIG_FILE: NUL"))

    return violations


def check_repository(root: Path) -> list[Violation]:
    root = root.resolve()
    violations: list[Violation] = []
    pyprojects = _discover(root, "pyproject.toml")
    lockfiles = _discover(root, "uv.lock")

    if not pyprojects:
        violations.append(Violation(root, "no pyproject.toml files discovered"))
    for path in pyprojects:
        violations.extend(validate_pyproject(path))
    for path in lockfiles:
        violations.extend(validate_lockfile(path))
    for path in _config_files(root):
        violations.extend(validate_install_surface(path))

    return violations


def main() -> int:
    parser = argparse.ArgumentParser(description="Enforce the repository's Microsoft Python package proxy policy.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()

    violations = check_repository(args.root)
    if violations:
        for violation in violations:
            print(violation.render(args.root), file=sys.stderr)
        return 1

    print(f"Python package source policy passed: {PROXY_INDEX_URL}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
