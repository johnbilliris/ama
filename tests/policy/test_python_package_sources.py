from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

SCRIPT_PATH = Path(__file__).resolve().parents[2] / "scripts" / "verify_python_package_sources.py"
SPEC = importlib.util.spec_from_file_location("verify_python_package_sources", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
policy = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = policy
SPEC.loader.exec_module(policy)


def write_valid_pyproject(root: Path, relative_path: str = "pyproject.toml") -> Path:
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        """\
[project]
name = "policy-fixture"
version = "0.1.0"
dependencies = ["requests>=2"]

[[tool.uv.index]]
name = "microsoft-package-feed-proxy"
url = "https://packagefeedproxy.microsoft.io/pypi/simple"
default = true
""",
        encoding="utf-8",
    )
    return path


def write_valid_lockfile(root: Path) -> Path:
    path = root / "uv.lock"
    path.write_text(
        """\
version = 1

[[package]]
name = "requests"
version = "2.0.0"
source = { registry = "https://packagefeedproxy.microsoft.io/pypi/simple" }
wheels = [
  { url = "https://ms-feed-25.pkgs.visualstudio.com/feed/pypi/download/requests.whl", hash = "sha256:abc" },
]
""",
        encoding="utf-8",
    )
    return path


def test_accepts_proxy_registry_microsoft_artifacts_and_local_sources(tmp_path: Path) -> None:
    pyproject = write_valid_pyproject(tmp_path)
    text = pyproject.read_text(encoding="utf-8")
    pyproject.write_text(
        text
        + """\
[tool.uv.sources]
local-package = { path = "packages/local-package", editable = true }
""",
        encoding="utf-8",
    )
    write_valid_lockfile(tmp_path)

    assert policy.check_repository(tmp_path) == []


@pytest.mark.parametrize(
    "replacement",
    [
        "https://packagefeedproxy.microsoft.io/pypi/simple/",
        "https://pypi.org/simple/",
        "https://example.com/simple/",
    ],
)
def test_rejects_alternate_project_indexes(tmp_path: Path, replacement: str) -> None:
    pyproject = write_valid_pyproject(tmp_path)
    pyproject.write_text(
        pyproject.read_text(encoding="utf-8").replace(policy.PROXY_INDEX_URL, replacement),
        encoding="utf-8",
    )

    violations = policy.check_repository(tmp_path)

    assert any("tool.uv.index" in violation.message for violation in violations)


def test_rejects_direct_url_and_vcs_requirements(tmp_path: Path) -> None:
    pyproject = write_valid_pyproject(tmp_path)
    pyproject.write_text(
        pyproject.read_text(encoding="utf-8").replace(
            '"requests>=2"',
            '"archive @ https://example.com/archive.whl", "project @ git+https://example.com/project.git"',
        ),
        encoding="utf-8",
    )

    violations = policy.check_repository(tmp_path)

    assert sum("direct external requirement" in violation.message for violation in violations) == 2


def test_rejects_non_proxy_lock_registry_and_artifact(tmp_path: Path) -> None:
    write_valid_pyproject(tmp_path)
    lockfile = write_valid_lockfile(tmp_path)
    lockfile.write_text(
        lockfile.read_text(encoding="utf-8")
        .replace(policy.PROXY_INDEX_URL, "https://pypi.org/simple/")
        .replace("https://ms-feed-25.pkgs.visualstudio.com/feed", "https://files.pythonhosted.org/packages"),
        encoding="utf-8",
    )

    violations = policy.check_repository(tmp_path)

    assert any("forbidden registry" in violation.message for violation in violations)
    assert any("forbidden artifact URL" in violation.message for violation in violations)


def test_rejects_extra_index_and_docker_build_arg(tmp_path: Path) -> None:
    write_valid_pyproject(tmp_path)
    dockerfile = tmp_path / "apps" / "api" / "Dockerfile"
    dockerfile.parent.mkdir(parents=True)
    dockerfile.write_text(
        """\
FROM python:3.12-slim
ARG PIP_INDEX_URL=https://packagefeedproxy.microsoft.io/pypi/simple
ENV PIP_EXTRA_INDEX_URL=https://pypi.org/simple/
ENV PIP_FIND_LINKS=https://example.com/wheels/
RUN pip install requests
""",
        encoding="utf-8",
    )

    violations = policy.check_repository(tmp_path)

    assert any("Docker ARG" in violation.message for violation in violations)
    assert any("PIP_EXTRA_INDEX_URL" in violation.message for violation in violations)
    assert any("PIP_FIND_LINKS" in violation.message for violation in violations)


def test_discovers_new_nested_project_without_proxy(tmp_path: Path) -> None:
    write_valid_pyproject(tmp_path)
    nested = tmp_path / "future" / "service" / "pyproject.toml"
    nested.parent.mkdir(parents=True)
    nested.write_text(
        '[project]\nname = "future-service"\nversion = "0.1.0"\n',
        encoding="utf-8",
    )

    violations = policy.check_repository(tmp_path)

    assert any(violation.path == nested and "tool.uv.index" in violation.message for violation in violations)


def test_rejects_direct_url_in_install_command(tmp_path: Path) -> None:
    write_valid_pyproject(tmp_path)
    workflow = tmp_path / ".github" / "workflows" / "direct-url.yml"
    workflow.parent.mkdir(parents=True)
    workflow.write_text(
        """\
env:
  PIP_CONFIG_FILE: /dev/null
  PIP_INDEX_URL: https://packagefeedproxy.microsoft.io/pypi/simple
  PIP_EXTRA_INDEX_URL: ""
  UV_DEFAULT_INDEX: https://packagefeedproxy.microsoft.io/pypi/simple
jobs:
  install:
    runs-on: ubuntu-latest
    steps:
      - run: pip install https://example.com/archive.whl
""",
        encoding="utf-8",
    )

    violations = policy.check_repository(tmp_path)

    assert any("direct external install URL" in violation.message for violation in violations)


def test_rejects_remote_python_pre_commit_package_source(tmp_path: Path) -> None:
    write_valid_pyproject(tmp_path)
    config = tmp_path / ".pre-commit-config.yaml"
    config.write_text(
        """\
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.8.4
    hooks:
      - id: ruff
""",
        encoding="utf-8",
    )

    violations = policy.check_repository(tmp_path)

    assert any("remote pre-commit package source" in violation.message for violation in violations)
