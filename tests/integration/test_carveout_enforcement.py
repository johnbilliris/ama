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
import json
import os
import shutil
import subprocess
import textwrap
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "verify-carveout.ps1"

pytestmark = pytest.mark.skipif(
    shutil.which("pwsh") is None and shutil.which("powershell") is None,
    reason="PowerShell not available in environment",
)


def _pwsh() -> str:
    return shutil.which("pwsh") or shutil.which("powershell") or "powershell"


def _run_script(registry_path: Path, whatif_path: Path | None = None) -> subprocess.CompletedProcess[str]:
    whatif_args = ["-WhatIfPath", str(whatif_path)] if whatif_path else []
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
            *whatif_args,
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


@pytest.fixture
def approved_model_registry(tmp_path: Path) -> Path:
    review_date = dt.date.today() + dt.timedelta(days=60)
    return _write(
        tmp_path,
        f"""
        version: 1
        last_reviewed: {dt.date.today().isoformat()}
        reviewer_quorum: 2
        deployments:
          - model_name: gpt-4o-mini
            region: australiaeast
            purpose: production
            business_justification: "Synthetic approved model for deployment identity regression tests."
            approver_identities: [project-lead, security-reviewer]
            review_date: {review_date.isoformat()}
            data_minimisation_required: true
            classification_filter_required: true
        """,
    )


def _deployment_change(model_name: str | None, *, alias: str = "drafting-dev", change_type: str = "Modify") -> dict:
    return {
        "changeType": change_type,
        "resourceId": (
            "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/rg"
            f"/providers/Microsoft.CognitiveServices/accounts/foundry/deployments/{alias}"
        ),
        "after": {"properties": {"model": {"name": model_name}}},
    }


def _run_what_if(tmp_path: Path, registry_path: Path, changes: list[dict], *, wrapped: bool = False):
    payload = {"changes": changes}
    whatif_path = tmp_path / "whatif.json"
    whatif_path.write_text(json.dumps({"properties": payload} if wrapped else payload), encoding="utf-8")
    return _run_script(registry_path, whatif_path)


@pytest.mark.parametrize(
    ("change_type", "wrapped"),
    [("Create", False), ("Modify", True), ("NoChange", False)],
)
def test_approved_model_passes_with_independent_deployment_alias(
    tmp_path: Path,
    approved_model_registry: Path,
    change_type: str,
    wrapped: bool,
) -> None:
    result = _run_what_if(
        tmp_path,
        approved_model_registry,
        [_deployment_change("gpt-4o-mini", change_type=change_type)],
        wrapped=wrapped,
    )
    assert result.returncode == 0, result.stderr


def test_approved_alias_does_not_approve_an_unregistered_underlying_model(
    tmp_path: Path,
    approved_model_registry: Path,
) -> None:
    result = _run_what_if(
        tmp_path,
        approved_model_registry,
        [_deployment_change("gpt-5.4", alias="gpt-4o-mini")],
    )
    assert result.returncode == 4
    assert "gpt-5.4" in result.stderr
    assert "gpt-4o-mini" in result.stderr


@pytest.mark.parametrize("model_name", [None, ""])
def test_missing_proposed_model_does_not_fall_back_to_alias_or_previous_model(
    tmp_path: Path,
    approved_model_registry: Path,
    model_name: str | None,
) -> None:
    change = _deployment_change(model_name, alias="gpt-4o-mini")
    change["before"] = {"properties": {"model": {"name": "gpt-4o-mini"}}}
    result = _run_what_if(tmp_path, approved_model_registry, [change])
    assert result.returncode == 4
    assert "model" in result.stderr.lower()


@pytest.mark.parametrize("change_type", ["Ignore", "Delete"])
def test_resources_not_being_deployed_do_not_require_a_model_approval(
    tmp_path: Path,
    baseline_yaml: Path,
    change_type: str,
) -> None:
    change = _deployment_change(None, change_type=change_type)
    del change["after"]
    result = _run_what_if(tmp_path, baseline_yaml, [change])
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("location_source", ["change", "after"])
def test_proposed_non_au_location_is_rejected(
    tmp_path: Path,
    approved_model_registry: Path,
    location_source: str,
) -> None:
    change = _deployment_change("gpt-4o-mini")
    target = change if location_source == "change" else change["after"]
    target["location"] = "eastus"
    result = _run_what_if(tmp_path, approved_model_registry, [change])
    assert result.returncode == 4
    assert "eastus" in result.stderr


@pytest.fixture
def single_approver_payload(approved_model_registry: Path) -> dict:
    payload = yaml.safe_load(approved_model_registry.read_text(encoding="utf-8"))
    payload["deployments"][0]["approver_identities"] = ["project-lead"]
    payload["quorum_waiver"] = {
        "scope": "all_environments",
        "approved_by": "project-lead",
        "approval_reference": "Synthetic explicit project-lead waiver for all environments.",
        "expires_on": (dt.datetime.now(dt.UTC).date() + dt.timedelta(days=60)).isoformat(),
    }
    return payload


@pytest.mark.parametrize("environment", ["dev", "staging", "prod"])
def test_explicit_waiver_permits_one_approver_in_each_environment(
    tmp_path: Path, single_approver_payload: dict, environment: str
) -> None:
    single_approver_payload["deployments"][0]["environment"] = environment
    result = _run_script(_write(tmp_path, yaml.safe_dump(single_approver_payload)))
    assert result.returncode == 0, result.stderr
    assert "waiver active" in result.stdout


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("expires_on", "2000-01-01"),
        ("expires_on", "not-a-date"),
        ("expires_on", None),
        ("approved_by", "<approver>"),
        ("approval_reference", ""),
        ("scope", "dev"),
    ],
)
def test_expired_or_invalid_waiver_does_not_approve_a_single_reviewer(
    tmp_path: Path, single_approver_payload: dict, field: str, value: str | None
) -> None:
    single_approver_payload["quorum_waiver"][field] = value
    result = _run_script(_write(tmp_path, yaml.safe_dump(single_approver_payload)))
    assert result.returncode == 4
    assert "quorum_waiver" in result.stderr
    assert "approver_identities" in result.stderr


@pytest.mark.parametrize("environment", ["dev", "staging", "prod"])
def test_removing_waiver_restores_environment_quorum(
    tmp_path: Path, single_approver_payload: dict, environment: str
) -> None:
    del single_approver_payload["quorum_waiver"]
    single_approver_payload["deployments"][0]["environment"] = environment
    result = _run_script(_write(tmp_path, yaml.safe_dump(single_approver_payload)))
    assert result.returncode == 4
    assert f"fewer than {3 if environment == 'prod' else 2}" in result.stderr


@pytest.mark.parametrize("violation", ["no-approver", "placeholder", "region", "flags", "review-window"])
def test_waiver_does_not_disable_other_model_controls(
    tmp_path: Path, single_approver_payload: dict, violation: str
) -> None:
    row = single_approver_payload["deployments"][0]
    if violation == "no-approver":
        row["approver_identities"] = []
    elif violation == "placeholder":
        row["approver_identities"] = ["<approver>"]
    elif violation == "region":
        row["region"] = "eastus"
    elif violation == "flags":
        row["data_minimisation_required"] = False
    else:
        row["review_date"] = dt.date.today() + dt.timedelta(days=730)
    result = _run_script(_write(tmp_path, yaml.safe_dump(single_approver_payload)))
    assert result.returncode == 4


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
