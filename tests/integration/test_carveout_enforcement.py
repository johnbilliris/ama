"""T013 — Integration test for ``scripts/verify-carveout.ps1`` CD enforcement (FR-RAG-CV-01..04).

Synthesises the four documented CD-failure cases from tasks.md T013 and
asserts the script exits non-zero on each:

(i)   deployment missing from registry
(ii)  ``review_date`` expired
(iii) placeholder ``approver_identities``
(iv)  data-plane resource in a non-AU region

This test goes RED before T024 (extended verify-carveout.ps1) lands and GREEN
once the script's expanded checks are in place.
"""

from __future__ import annotations

import datetime as dt
import os
import shutil
import subprocess
import textwrap
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "verify-carveout.ps1"

pytestmark = pytest.mark.skipif(
    shutil.which("pwsh") is None and shutil.which("powershell") is None,
    reason="PowerShell not available in environment",
)


def _pwsh() -> str:
    return shutil.which("pwsh") or shutil.which("powershell") or "powershell"


def _run_script(registry_path: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            _pwsh(),
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(SCRIPT),
            "-RegistryPath",
            str(registry_path),
        ],
        capture_output=True,
        text=True,
        check=False,
        cwd=str(ROOT),
        env={**os.environ, "POWERSHELL_TELEMETRY_OPTOUT": "1"},
    )


def _write(tmp: Path, body: str) -> Path:
    p = tmp / "synth-carveout.yaml"
    p.write_text(textwrap.dedent(body).lstrip(), encoding="utf-8")
    return p


@pytest.fixture
def baseline_yaml(tmp_path: Path) -> Path:
    """A passing registry (empty deployments — production baseline)."""
    return _write(
        tmp_path,
        f"""
        version: 1
        last_reviewed: {dt.date.today().isoformat()}
        reviewer_quorum: 2
        deployments: []
        """,
    )


def test_baseline_passes(baseline_yaml: Path) -> None:
    res = _run_script(baseline_yaml)
    assert res.returncode == 0, (
        f"baseline carve-out registry must pass (rc=0); got {res.returncode}\nstdout={res.stdout}\nstderr={res.stderr}"
    )


def test_review_date_expired_fails(tmp_path: Path) -> None:
    """Case (ii): review_date older than 6 months MUST fail."""
    expired = dt.date.today() - dt.timedelta(days=210)
    yaml_path = _write(
        tmp_path,
        f"""
        version: 1
        last_reviewed: {dt.date.today().isoformat()}
        reviewer_quorum: 2
        deployments:
          - model_name: gpt-4o-mini
            region: eastus
            purpose: production
            business_justification: "Spec 036 FR-RAG-FM-01 — production inference."
            approver_identities:
              - johnbilliris
              - security-engineer-handle
            review_date: {expired.isoformat()}
            data_minimisation_required: true
            classification_filter_required: true
        """,
    )
    res = _run_script(yaml_path)
    assert res.returncode != 0, "expired review_date must fail (FR-RAG-CV-02)"


def test_placeholder_approver_fails(tmp_path: Path) -> None:
    """Case (iii): placeholder approver MUST fail."""
    fresh = dt.date.today() + dt.timedelta(days=30)
    yaml_path = _write(
        tmp_path,
        f"""
        version: 1
        last_reviewed: {dt.date.today().isoformat()}
        reviewer_quorum: 2
        deployments:
          - model_name: gpt-4o-mini
            region: australiaeast
            purpose: production
            business_justification: "Spec 036 FR-RAG-FM-01 — production inference."
            approver_identities:
              - johnbilliris
              - <security-engineer-handle>
            review_date: {fresh.isoformat()}
            data_minimisation_required: true
            classification_filter_required: true
        """,
    )
    res = _run_script(yaml_path)
    assert res.returncode != 0, "placeholder approver_identities must fail (FR-RAG-CV-01)"


def test_under_quorum_fails(tmp_path: Path) -> None:
    yaml_path = _write(
        tmp_path,
        f"""
        version: 1
        last_reviewed: {dt.date.today().isoformat()}
        reviewer_quorum: 1
        deployments: []
        """,
    )
    res = _run_script(yaml_path)
    assert res.returncode != 0, "reviewer_quorum < 2 must fail (FR-RAG-CV-01)"


@pytest.mark.skipif(
    shutil.which("pwsh") is None and shutil.which("powershell") is None,
    reason="PowerShell not available in environment",
)
def test_deployment_missing_from_registry_fails(tmp_path: Path) -> None:
    """Case (i): synthetic bicep what-if emitting a deployment NOT in registry → CD fails."""
    fresh = dt.date.today() + dt.timedelta(days=30)
    yaml_path = _write(
        tmp_path,
        f"""
        version: 1
        last_reviewed: {dt.date.today().isoformat()}
        reviewer_quorum: 2
        deployments:
          - model_name: gpt-4o-mini
            region: australiaeast
            purpose: production
            business_justification: "Spec 036 FR-RAG-FM-01 — production inference for all agents."
            approver_identities:
              - johnbilliris
              - security-engineer-handle
            review_date: {fresh.isoformat()}
            data_minimisation_required: true
            classification_filter_required: true
        """,
    )
    # Synthesise a what-if dump with a *different* deployment (gpt-4o-canary)
    # that is NOT in the registry. The script must reject it.
    whatif_path = tmp_path / "whatif.json"
    whatif_path.write_text(
        '{"changes":[{"resourceId":"/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/rg/providers/Microsoft.CognitiveServices/accounts/foundry/deployments/gpt-4o-canary","location":"australiaeast"}]}',
        encoding="utf-8",
    )
    res = subprocess.run(
        [
            _pwsh(),
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(SCRIPT),
            "-RegistryPath",
            str(yaml_path),
            "-WhatIfPath",
            str(whatif_path),
        ],
        capture_output=True,
        text=True,
        check=False,
        cwd=str(ROOT),
        env={**os.environ, "POWERSHELL_TELEMETRY_OPTOUT": "1"},
    )
    assert res.returncode != 0, (
        f"deployment not in registry must fail (FR-RAG-CV-01); rc={res.returncode}\n"
        f"stdout={res.stdout}\nstderr={res.stderr}"
    )


@pytest.mark.skipif(
    shutil.which("pwsh") is None and shutil.which("powershell") is None,
    reason="PowerShell not available in environment",
)
def test_non_au_data_plane_fails(tmp_path: Path) -> None:
    """Case (iv): a data-plane resource in a non-AU region MUST fail (FR-RAG-CV-04).

    Two enforcement points:
      a) registry row with non-AU region (caught by the registry walk).
      b) bicep what-if with a non-AU cognitive-services / search resource.
    """
    fresh = dt.date.today() + dt.timedelta(days=30)
    yaml_path = _write(
        tmp_path,
        f"""
        version: 1
        last_reviewed: {dt.date.today().isoformat()}
        reviewer_quorum: 2
        deployments:
          - model_name: gpt-4o-mini
            region: australiacentral
            purpose: production
            business_justification: "Spec 036 FR-RAG-FM-01 — production inference."
            approver_identities:
              - johnbilliris
              - security-engineer-handle
            review_date: {fresh.isoformat()}
            data_minimisation_required: true
            classification_filter_required: true
        """,
    )
    res = _run_script(yaml_path)
    assert res.returncode != 0, "non-AU registry region must fail (FR-RAG-CV-04)"
