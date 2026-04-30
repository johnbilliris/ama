"""Test the verify-carveout.ps1 script (spec-032 T018, FR-AI03a).

Spawns the PowerShell script with crafted YAML inputs and asserts the exit code
behaviour required by ADR-033's deploy-time gate.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "verify-carveout.ps1"

pwsh = shutil.which("pwsh") or shutil.which("powershell")
pytestmark = pytest.mark.skipif(pwsh is None, reason="pwsh not on PATH")


def _run(yaml_text: str) -> subprocess.CompletedProcess:
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False, encoding="utf-8") as f:
        f.write(yaml_text)
        path = f.name
    try:
        return subprocess.run(  # noqa: S603
            [pwsh, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(SCRIPT), "-RegistryPath", path],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
    finally:
        os.unlink(path)


def test_empty_registry_passes():
    """Empty deployments list should pass — no non-AU models to enforce against."""
    yaml_text = "version: 1\nlast_reviewed: 2026-04-30\nreviewer_quorum: 2\ndeployments: []\n"
    result = _run(yaml_text)
    assert result.returncode == 0, f"stderr: {result.stderr}\nstdout: {result.stdout}"


def test_quorum_below_two_fails():
    yaml_text = "version: 1\nlast_reviewed: 2026-04-30\nreviewer_quorum: 1\ndeployments: []\n"
    result = _run(yaml_text)
    assert result.returncode == 3


def test_missing_required_flags_fails():
    """Deployment without data_minimisation_required + classification_filter_required must fail."""
    yaml_text = (
        "version: 1\n"
        "last_reviewed: 2026-04-30\n"
        "reviewer_quorum: 2\n"
        "deployments:\n"
        "  - model_name: phi-3.5-mini\n"
        "    region: eastus\n"
        "    purpose: shadow\n"
        "    business_justification: 'Cost/quality shadow path; complies with ADR-033 NN-2 carve-out.'\n"
        "    approver_identities: [johnbilliris, secengineer, complianceauditor]\n"
        "    review_date: 2026-10-30\n"
        "    data_minimisation_required: false\n"
        "    classification_filter_required: true\n"
    )
    result = _run(yaml_text)
    assert result.returncode == 4
    assert "data_minimisation_required" in result.stderr or "classification_filter_required" in result.stderr


def test_fewer_than_two_approvers_fails():
    yaml_text = (
        "version: 1\n"
        "last_reviewed: 2026-04-30\n"
        "reviewer_quorum: 2\n"
        "deployments:\n"
        "  - model_name: phi-3.5-mini\n"
        "    region: eastus\n"
        "    purpose: shadow\n"
        "    business_justification: 'Cost/quality shadow path; complies with ADR-033 NN-2 carve-out.'\n"
        "    approver_identities: [solo-approver]\n"
        "    review_date: 2026-10-30\n"
        "    data_minimisation_required: true\n"
        "    classification_filter_required: true\n"
    )
    result = _run(yaml_text)
    assert result.returncode == 4
    assert "approver_identities" in result.stderr


def test_stale_review_date_fails():
    yaml_text = (
        "version: 1\n"
        "last_reviewed: 2024-01-01\n"
        "reviewer_quorum: 2\n"
        "deployments:\n"
        "  - model_name: phi-3.5-mini\n"
        "    region: eastus\n"
        "    purpose: shadow\n"
        "    business_justification: 'Cost/quality shadow path; complies with ADR-033 NN-2 carve-out.'\n"
        "    approver_identities: [a, b, c]\n"
        "    review_date: 2024-01-01\n"
        "    data_minimisation_required: true\n"
        "    classification_filter_required: true\n"
    )
    result = _run(yaml_text)
    assert result.returncode == 4
    assert "older than 6 months" in result.stderr


def test_valid_deployment_passes():
    """A fully-conforming deployment should pass."""
    yaml_text = (
        "version: 1\n"
        "last_reviewed: 2030-01-01\n"
        "reviewer_quorum: 2\n"
        "deployments:\n"
        "  - model_name: phi-3.5-mini\n"
        "    region: eastus\n"
        "    purpose: shadow\n"
        "    business_justification: 'Cost/quality shadow path under ADR-033 NN-2 carve-out.'\n"
        "    approver_identities: [project-lead, security-eng, compliance-auditor]\n"
        "    review_date: 2030-06-30\n"
        "    data_minimisation_required: true\n"
        "    classification_filter_required: true\n"
    )
    result = _run(yaml_text)
    assert result.returncode == 0, f"stderr: {result.stderr}\nstdout: {result.stdout}"


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q", "-v"]))
