"""Offline failure evidence uses synthetic times/policy, never a production TTL."""

from __future__ import annotations

import copy
import subprocess
import sys
from pathlib import Path

import pytest

from tests.contract.test_llm_deployment_configuration import (
    CLI,
    KINDS,
    NOW,
    rebind,
    run_cli,
    synthetic_bundle,
)


@pytest.mark.parametrize("kind", KINDS)
@pytest.mark.parametrize(
    "field",
    (
        "target",
        "observed_at",
        "source_revision",
        "approval",
        "policy_id",
        "policy_version",
        "bindings",
        "invalidation",
    ),
)
def test_each_evidence_item_requires_complete_metadata(tmp_path: Path, kind: str, field: str) -> None:
    bundle = synthetic_bundle()
    del bundle[kind][field]
    result = run_cli(tmp_path, bundle)
    assert result.returncode == 1
    assert field in result.stderr
    assert result.stdout == ""


@pytest.mark.parametrize(
    "field",
    (
        "tenant",
        "subscription",
        "resource_group",
        "account_id",
        "environment",
        "endpoint",
        "region",
    ),
)
def test_scope_cannot_cross_environment(tmp_path: Path, field: str) -> None:
    bundle = synthetic_bundle()
    bundle["inventory"]["target"][field] = "different"
    result = run_cli(tmp_path, bundle)
    assert result.returncode == 1
    assert "target" in result.stderr


@pytest.mark.parametrize(
    "mutation,diagnostic",
    (
        ("policy_missing", "freshness_policy"),
        ("policy_unapproved", "approval"),
        ("policy_version", "policy_version"),
        ("policy_window", "max_age_seconds"),
        ("policy_actions", "invalidation_actions"),
        ("expired", "expired"),
        ("future", "observed_at"),
        ("invalidated", "invalidation"),
        ("g0_missing", "collection_authority"),
        ("g0_scope", "target"),
        ("g0_operations", "operations"),
        ("g0_window", "collection_authority"),
        ("unapproved", "approval"),
        ("state", "state"),
        ("unreconciled", "reconciliation"),
        ("reconciliation_target", "reconciliation"),
    ),
)
def test_authority_freshness_and_reconciliation_fail_closed(
    tmp_path: Path,
    mutation: str,
    diagnostic: str,
) -> None:
    bundle = synthetic_bundle()
    baseline = bundle["baseline"]
    policy = baseline["freshness_policy"]
    if mutation == "policy_missing":
        del baseline["freshness_policy"]
    elif mutation == "policy_unapproved":
        del policy["approval"]
    elif mutation == "policy_version":
        baseline["policy_version"] = "other-version"
    elif mutation == "policy_window":
        del policy["max_age_seconds"]["inventory"]
    elif mutation == "policy_actions":
        del policy["invalidation_actions"]["network"]
    elif mutation == "expired":
        policy["max_age_seconds"]["inventory"] = 1
    elif mutation == "future":
        bundle["inventory"]["observed_at"] = "2041-01-01T11:00:00Z"
    elif mutation == "invalidated":
        bundle["inventory"]["invalidation"]["events"] = ["network"]
    elif mutation == "g0_missing":
        del bundle["inventory"]["collection_authority"]
    elif mutation == "g0_scope":
        bundle["inventory"]["collection_authority"]["target"]["account_id"] = "wrong"
    elif mutation == "g0_operations":
        bundle["inventory"]["collection_authority"]["operations"] = []
    elif mutation == "g0_window":
        bundle["inventory"]["collection_authority"]["valid_until"] = "2039-01-01T00:00:00Z"
    elif mutation == "unapproved":
        baseline["approval"]["approver"] = ""
    elif mutation == "state":
        baseline["state"] = "observed"
    else:
        baseline["bindings"]["configuration_digest"] = "pre-candidate"
        if mutation == "reconciliation_target":
            baseline["reconciliation"] = {
                "from_bindings": copy.deepcopy(baseline["bindings"]),
                "to_bindings": copy.deepcopy(bundle["candidate"]["bindings"]),
                "source_revision": baseline["source_revision"],
                "target": {**baseline["target"], "account_id": "wrong"},
                "policy_id": baseline["policy_id"],
                "policy_version": baseline["policy_version"],
                "approval": copy.deepcopy(baseline["approval"]),
            }
    result = run_cli(tmp_path, bundle)
    assert result.returncode == 1
    assert diagnostic in result.stderr


def test_explicit_baseline_to_exact_candidate_reconciliation(tmp_path: Path) -> None:
    bundle = synthetic_bundle()
    baseline = bundle["baseline"]
    baseline["bindings"]["configuration_digest"] = "pre-candidate"
    baseline["reconciliation"] = {
        "from_bindings": copy.deepcopy(baseline["bindings"]),
        "to_bindings": copy.deepcopy(bundle["candidate"]["bindings"]),
        "target": copy.deepcopy(baseline["target"]),
        "source_revision": baseline["source_revision"],
        "policy_id": baseline["policy_id"],
        "policy_version": baseline["policy_version"],
        "approval": copy.deepcopy(baseline["approval"]),
    }
    result = run_cli(tmp_path, bundle)
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("kind", KINDS)
@pytest.mark.parametrize("binding", ("configuration_digest", "api_image", "agents_image", "compiled_proposal_revision"))
def test_revision_binding_missing_or_changed(tmp_path: Path, kind: str, binding: str) -> None:
    bundle = synthetic_bundle()
    bundle[kind]["bindings"][binding] = "wrong-binding"
    result = run_cli(tmp_path, bundle)
    assert result.returncode == 1
    assert "binding" in result.stderr


@pytest.mark.parametrize(
    "section,field",
    (
        ("reasoning", "name"),
        ("reasoning", "model_id"),
        ("drafting", "model_version"),
        ("simulation", "format"),
        ("reasoning", "sku"),
        ("drafting", "capacity"),
        ("simulation", "rai_policy"),
        ("simulation", "effective_filters"),
        ("simulation", "version_upgrade"),
        ("embedding", "dimensions"),
        ("embedding", "name"),
        ("controls", "rbac"),
        ("controls", "managed_identity"),
        ("controls", "network"),
        ("controls", "authentication"),
        ("controls", "access"),
        ("controls", "diagnostics"),
        ("controls", "residency"),
    ),
)
@pytest.mark.parametrize("unreadable", (False, True))
def test_drift_and_unreadable_properties_are_not_defaults(
    tmp_path: Path,
    section: str,
    field: str,
    unreadable: bool,
) -> None:
    bundle = synthetic_bundle()
    snapshot = bundle["inventory"]["snapshot"]
    node = snapshot[section] if section in ("embedding", "controls") else snapshot["deployments"][section]
    node[field] = None if unreadable else "changed"
    result = run_cli(tmp_path, bundle)
    assert result.returncode == 1
    assert "snapshot" in result.stderr


@pytest.mark.parametrize("service", ("api", "agents"))
@pytest.mark.parametrize("field", ("image", "revision", "environment"))
def test_candidate_is_one_exact_image_config_pair(tmp_path: Path, service: str, field: str) -> None:
    bundle = synthetic_bundle()
    bundle["outputs"]["snapshot"]["services"][service][field] = "wrong-pair"
    result = run_cli(tmp_path, bundle)
    assert result.returncode == 1
    assert "services" in result.stderr


def test_simulation_cannot_collide_with_live_even_with_consistent_proposal(tmp_path: Path) -> None:
    bundle = synthetic_bundle(shared=True)
    for kind in ("baseline", "inventory", "outputs"):
        bundle[kind]["snapshot"]["deployments"]["simulation"]["name"] = "old-0"
    for key in ("parameters", "child_parameters"):
        bundle["outputs"][key]["simulationDeploymentName"] = "old-0"
    for kind in ("candidate", "outputs"):
        services = bundle[kind]["services"] if kind == "candidate" else bundle[kind]["snapshot"]["services"]
        for service in services.values():
            env = service["environment"]
            env["AZURE_AI_SIMULATION_DEPLOYMENT"] = "old-0"
            env["AZURE_AI_PROJECT_DEPLOYMENTS"] = env["AZURE_AI_PROJECT_DEPLOYMENTS"].replace(
                "simulation=old-2",
                "simulation=old-0",
            )
    rebind(bundle)
    result = run_cli(tmp_path, bundle)
    assert result.returncode == 1
    assert "simulation" in result.stderr


@pytest.mark.parametrize(
    "contents",
    (
        "{broken",
        "[]",
        "null",
        '{"approval": NaN}',
        '{"target": 1, "target": 2}',
        '{"overflow": 1e9999}',
        "[" * 2000 + "]" * 2000,
    ),
)
def test_malformed_json_and_root_types(tmp_path: Path, contents: str) -> None:
    path = tmp_path / "bad.json"
    path.write_text(contents, encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(CLI), *[arg for kind in KINDS for arg in (f"--{kind}", str(path))], "--at", NOW],
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 1
    assert result.stdout == ""
    assert "ERROR:" in result.stderr
    assert "Traceback" not in result.stderr


def test_missing_file_and_cli_argument_exit_codes(tmp_path: Path) -> None:
    result = subprocess.run([sys.executable, str(CLI)], text=True, capture_output=True, check=False)
    assert result.returncode == 2
    missing = tmp_path / "missing.json"
    result = subprocess.run(
        [sys.executable, str(CLI), *[arg for kind in KINDS for arg in (f"--{kind}", str(missing))]],
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 1
    assert result.stdout == ""
    assert "inventory" in result.stderr
    assert "Traceback" not in result.stderr


def test_diagnostics_do_not_echo_evidence_payload(tmp_path: Path) -> None:
    bundle = synthetic_bundle()
    bundle["inventory"]["target"]["account_id"] = "SENSITIVE_SENTINEL"
    result = run_cli(tmp_path, bundle)
    assert result.returncode == 1
    assert "SENSITIVE_SENTINEL" not in result.stderr + result.stdout


@pytest.mark.parametrize("change", ("approval_expired", "binding_missing", "type", "not_synthetic"))
def test_additional_closed_evidence_boundaries(tmp_path: Path, change: str) -> None:
    bundle = synthetic_bundle()
    if change == "approval_expired":
        bundle["candidate"]["approval"]["valid_until"] = "2040-01-01T11:59:00Z"
    elif change == "binding_missing":
        del bundle["outputs"]["bindings"]["compiled_proposal_revision"]
    elif change == "type":
        bundle["baseline"]["freshness_policy"]["max_age_seconds"]["baseline"] = []
    else:
        del bundle["candidate"]["synthetic"]
    result = run_cli(tmp_path, bundle)
    assert result.returncode == 1
    assert result.stdout == ""
    assert "ERROR:" in result.stderr
    assert "Traceback" not in result.stderr


def test_pre_candidate_current_csv_conflicts_are_cleaned_not_replayed(tmp_path: Path) -> None:
    bundle = synthetic_bundle(shared=True)
    for kind in ("baseline", "inventory"):
        for service in bundle[kind]["snapshot"]["services"].values():
            service["environment"]["AZURE_AI_PROJECT_DEPLOYMENTS"] += (
                ",synthetic-shared@synthetic-v=old-0,synthetic-shared@synthetic-v=old-2"
            )
    result = run_cli(tmp_path, bundle)
    assert result.returncode == 0, result.stderr


def test_cli_has_no_network_or_write_path(tmp_path: Path) -> None:
    bundle = synthetic_bundle()
    assert run_cli(tmp_path, bundle).returncode == 0
    paths = [arg for kind in KINDS for arg in (f"--{kind}", str(tmp_path / f"{kind}.json"))]
    guard = """
import os, runpy, sys
write_mask = os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND
def guard(event, args):
    if event.startswith(("socket.", "subprocess.")) or event in ("os.remove", "os.rename", "os.mkdir"):
        raise RuntimeError("forbidden external or mutation operation")
    if event == "open" and isinstance(args[2], int) and args[2] & write_mask:
        raise RuntimeError("forbidden write")
sys.dont_write_bytecode = True
sys.addaudithook(guard)
sys.argv = sys.argv[1:]
runpy.run_path(sys.argv[0], run_name="__main__")
"""
    result = subprocess.run(
        [sys.executable, "-c", guard, str(CLI), *paths, "--at", NOW],
        cwd=tmp_path,
        text=True,
        capture_output=True,
        check=False,
        timeout=15,
    )
    assert result.returncode == 0, result.stderr
    assert result.stderr == ""


@pytest.mark.parametrize("section", ("deployments", "embedding", "controls"))
def test_compiled_proposal_must_preserve_baseline_properties(tmp_path: Path, section: str) -> None:
    bundle = synthetic_bundle()
    proposal = bundle["outputs"]["snapshot"]
    if section == "deployments":
        proposal[section]["reasoning"]["effective_filters"]["synthetic-filter"]["enabled"] = False
    elif section == "embedding":
        proposal[section]["model_version"] = "unapproved-version"
    else:
        proposal[section]["network"]["synthetic-setting"] = True
    result = run_cli(tmp_path, bundle)
    assert result.returncode == 1
    assert "outputs.snapshot." + section in result.stderr


def test_unreadable_file_has_actionable_diagnostic(tmp_path: Path) -> None:
    result = subprocess.run(
        [sys.executable, str(CLI), *[arg for kind in KINDS for arg in (f"--{kind}", str(tmp_path))]],
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 1
    assert result.stdout == ""
    assert "inventory: cannot read UTF-8 evidence file" in result.stderr
    assert "Traceback" not in result.stderr
