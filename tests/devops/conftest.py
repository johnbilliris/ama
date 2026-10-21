"""Shared pytest fixtures for CD pipeline / DevOps tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

# ── Repository root (tests/devops/conftest.py → repo root is two levels up) ──
ROOT = Path(__file__).resolve().parents[2]


# ── YAML / JSON loaders ─────────────────────────────────────────────────────


@pytest.fixture(scope="session")
def repo_root() -> Path:
    """Return the absolute path to the repository root."""
    return ROOT


@pytest.fixture(scope="session")
def cd_workflow_path(repo_root: Path) -> Path:
    """Return the path to the CD workflow file."""
    return repo_root / ".github" / "workflows" / "cd.yml"


@pytest.fixture(scope="session")
def eval_pr_gate_workflow_path(repo_root: Path) -> Path:
    """Return the path to the eval PR gate workflow file."""
    return repo_root / ".github" / "workflows" / "eval-pr-gate.yml"


@pytest.fixture(scope="session")
def drift_workflow_path(repo_root: Path) -> Path:
    """Return the path to the drift-detection workflow file."""
    return repo_root / ".github" / "workflows" / "drift-detection.yml"


@pytest.fixture(scope="session")
def ci_workflow_path(repo_root: Path) -> Path:
    """Return the path to the CI workflow file (read-only reference)."""
    return repo_root / ".github" / "workflows" / "ci.yml"


@pytest.fixture(scope="session")
def rollback_script_path(repo_root: Path) -> Path:
    """Return the path to the rollback script."""
    return repo_root / "scripts" / "rollback.sh"


@pytest.fixture(scope="session")
def staging_params_path(repo_root: Path) -> Path:
    """Return the path to the staging parameter file."""
    return repo_root / "infra" / "main.parameters.staging.json"


@pytest.fixture(scope="session")
def production_params_path(repo_root: Path) -> Path:
    """Return the path to the production parameter file."""
    return repo_root / "infra" / "main.parameters.production.json"


@pytest.fixture(scope="session")
def base_params_path(repo_root: Path) -> Path:
    """Return the path to the base (dev) parameter file."""
    return repo_root / "infra" / "main.parameters.json"


# ── Parsed content fixtures ─────────────────────────────────────────────────


def _normalize_yaml_keys(data: dict) -> dict:
    """Normalize YAML keys — yaml.safe_load parses bare `on` as boolean True."""
    if not isinstance(data, dict):
        return data
    normalized = {}
    for k, v in data.items():
        key = "on" if k is True else k
        normalized[key] = v
    return normalized


@pytest.fixture(scope="session")
def cd_workflow(cd_workflow_path: Path) -> dict:
    """Parse and return the CD workflow YAML as a dict."""
    raw = yaml.safe_load(cd_workflow_path.read_text(encoding="utf-8"))
    return _normalize_yaml_keys(raw)


@pytest.fixture(scope="session")
def eval_pr_gate_workflow(eval_pr_gate_workflow_path: Path) -> dict:
    """Parse and return the eval PR gate workflow YAML as a dict."""
    raw = yaml.safe_load(eval_pr_gate_workflow_path.read_text(encoding="utf-8"))
    return _normalize_yaml_keys(raw)


@pytest.fixture(scope="session")
def drift_workflow(drift_workflow_path: Path) -> dict:
    """Parse and return the drift-detection workflow YAML as a dict."""
    raw = yaml.safe_load(drift_workflow_path.read_text(encoding="utf-8"))
    return _normalize_yaml_keys(raw)


@pytest.fixture(scope="session")
def ci_workflow(ci_workflow_path: Path) -> dict:
    """Parse and return the CI workflow YAML as a dict."""
    raw = yaml.safe_load(ci_workflow_path.read_text(encoding="utf-8"))
    return _normalize_yaml_keys(raw)


@pytest.fixture(scope="session")
def staging_params(staging_params_path: Path) -> dict:
    """Parse and return the staging parameter file."""
    return json.loads(staging_params_path.read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def production_params(production_params_path: Path) -> dict:
    """Parse and return the production parameter file."""
    return json.loads(production_params_path.read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def base_params(base_params_path: Path) -> dict:
    """Parse and return the base (dev) parameter file."""
    return json.loads(base_params_path.read_text(encoding="utf-8"))


# ── Service metadata ────────────────────────────────────────────────────────

SERVICES = {
    "api": {"host": "containerapp", "health_endpoint": "/api/health"},
    "agents": {"host": "containerapp", "health_endpoint": "/health"},
    "ingestion": {"host": "containerapp", "health_endpoint": "/health"},
    "web": {"host": "appservice", "health_endpoint": "/"},
}

ALLOWED_REGIONS = {"australiaeast", "australiasoutheast"}


@pytest.fixture(scope="session")
def services() -> dict:
    """Return the service metadata dict."""
    return SERVICES


@pytest.fixture(scope="session")
def allowed_regions() -> set[str]:
    """Return set of allowed Azure regions (FR-009)."""
    return ALLOWED_REGIONS
