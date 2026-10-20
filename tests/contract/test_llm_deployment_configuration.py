"""Synthetic compiled/preflight evidence, NOT acceptance of actual Bicep output."""

from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[2]
CLI = ROOT / "scripts" / "verify-llm-deployment-preflight.py"
NOW = "2040-01-01T12:00:00Z"
KINDS = ("inventory", "baseline", "outputs", "candidate")
TIERS = ("reasoning", "drafting", "simulation")
EVENTS = (
    "destination",
    "model",
    "protection",
    "embedding",
    "policy",
    "rbac",
    "network",
    "images",
    "configuration",
    "compiled_proposal",
    "scope",
    "drift",
)


def digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def synthetic_bundle(*, shared: bool = False, purpose_names: bool = False) -> dict[str, Any]:
    """Build independently labelled synthetic evidence; no approved target values."""
    target = {
        "tenant": "synthetic-tenant",
        "subscription": "synthetic-subscription",
        "resource_group": "synthetic-rg",
        "account_id": "/synthetic/account",
        "environment": "synthetic",
        "endpoint": "https://synthetic.invalid",
        "region": "australiaeast",
    }
    deployments = {}
    for index, tier in enumerate(TIERS):
        deployments[tier] = {
            "name": f"{tier}-synthetic" if purpose_names else f"old-{index}",
            "model_id": "synthetic-shared" if shared else f"synthetic-model-{index}",
            "model_version": "synthetic-v" if shared else f"synthetic-v{index}",
            "format": "OpenAI",
            "sku": "synthetic-sku",
            "capacity": index + 1,
            "rai_policy": f"synthetic-policy-{index}",
            "effective_filters": {"synthetic-filter": {"enabled": True, "threshold": index}},
            "version_upgrade": "synthetic-upgrade",
        }
    embedding = {
        **copy.deepcopy(deployments["drafting"]),
        "name": "old-e",
        "model_id": "text-embedding-3-large",
        "model_version": "1",
        "dimensions": 3072,
    }
    controls: dict[str, Any] = {
        key: {"synthetic-setting": False}
        for key in ("rbac", "managed_identity", "access", "network", "authentication", "diagnostics")
    }
    controls["residency"] = "AU"
    env = {
        "AZURE_AI_PROJECT_ENDPOINT": target["endpoint"],
        "AZURE_AI_PROJECT_REGION": target["region"],
        "EMBEDDING_DEPLOYMENT_NAME": embedding["name"],
    }
    entries = []
    for tier, deployment in deployments.items():
        prefix = f"AZURE_AI_{tier.upper()}_"
        for suffix, field in (("DEPLOYMENT", "name"), ("MODEL_ID", "model_id"), ("MODEL_VERSION", "model_version")):
            env[prefix + suffix] = deployment[field]
        key = f"{deployment['model_id']}@{deployment['model_version']}"
        env[prefix + "MODEL_KEY"] = key
        entries.append(f"{tier}={deployment['name']}")
        if not shared:
            entries.extend((f"{key}={deployment['name']}", f"{deployment['model_id']}={deployment['name']}"))
    entries.append("text-embedding-3-large@1=old-e")
    env["AZURE_AI_PROJECT_DEPLOYMENTS"] = ",".join(entries)
    services: dict[str, Any] = {
        name: {"image": "sha256:" + str(index) * 64, "revision": f"corrected-{name}", "environment": copy.deepcopy(env)}
        for index, name in enumerate(("api", "agents"), 1)
    }
    binding = {
        "configuration_digest": digest({name: service["environment"] for name, service in services.items()}),
        "api_image": services["api"]["image"],
        "agents_image": services["agents"]["image"],
        "compiled_proposal_revision": "synthetic-compiled-1",
    }
    approval = {
        "approver": "synthetic-reviewer",
        "approved_at": "2040-01-01T11:30:00Z",
        "valid_until": "2040-01-01T13:00:00Z",
    }
    evidence: dict[str, Any] = {}
    for kind in KINDS:
        evidence[kind] = {
            "synthetic": True,
            "target": copy.deepcopy(target),
            "observed_at": "2040-01-01T11:00:00Z",
            "source_revision": f"synthetic-{kind}-source",
            "approval": copy.deepcopy(approval),
            "policy_id": "synthetic-policy",
            "policy_version": "synthetic-1",
            "bindings": copy.deepcopy(binding),
            "invalidation": {"evaluated_at": "2040-01-01T11:20:00Z", "events": []},
        }
    snapshot = {"deployments": deployments, "embedding": embedding, "controls": controls, "services": services}
    for kind in ("inventory", "baseline", "outputs"):
        evidence[kind]["snapshot"] = copy.deepcopy(snapshot)
    # Current pairs and candidate pairs intentionally differ: changing code/config is allowed, not model resources.
    for kind in ("inventory", "baseline"):
        for name in ("api", "agents"):
            evidence[kind]["snapshot"]["services"][name]["revision"] = f"current-{name}"
            evidence[kind]["snapshot"]["services"][name]["image"] = "sha256:" + "a" * 64
    evidence["candidate"]["services"] = copy.deepcopy(services)
    parameters = {}
    for tier, deployment in deployments.items():
        for suffix, field in (("DeploymentName", "name"), ("ModelName", "model_id"), ("ModelVersion", "model_version")):
            parameters[tier + suffix] = deployment[field]
    evidence["outputs"]["parameters"] = parameters
    evidence["outputs"]["child_parameters"] = copy.deepcopy(parameters)
    evidence["inventory"]["collection_authority"] = {
        "reference": "synthetic-G0",
        "approver": "synthetic-collector-authoriser",
        "target": copy.deepcopy(target),
        "operations": ["inventory", "metadata"],
        "valid_from": "2040-01-01T10:00:00Z",
        "valid_until": "2040-01-01T13:00:00Z",
    }
    evidence["baseline"]["state"] = "approved"
    evidence["baseline"]["freshness_policy"] = {
        "id": "synthetic-policy",
        "version": "synthetic-1",
        "approval": copy.deepcopy(approval),
        "max_age_seconds": dict.fromkeys(KINDS, 7200),
        "invalidation_actions": {event: ["recollect", "reapprove"] for event in EVENTS},
    }
    return evidence


def rebind(bundle: dict[str, Any]) -> None:
    """Rebind intentional synthetic candidate edits, leaving comparison failures observable."""
    services = bundle["candidate"]["services"]
    binding = {
        **bundle["candidate"]["bindings"],
        "configuration_digest": digest({name: value["environment"] for name, value in services.items()}),
        "api_image": services["api"]["image"],
        "agents_image": services["agents"]["image"],
    }
    for kind in KINDS:
        bundle[kind]["bindings"] = copy.deepcopy(binding)


def run_cli(tmp_path: Path, bundle: dict[str, Any], *, now: str = NOW) -> subprocess.CompletedProcess[str]:
    paths: list[str] = []
    for kind in KINDS:
        path = tmp_path / f"{kind}.json"
        path.write_text(json.dumps(bundle[kind]), encoding="utf-8")
        paths.extend((f"--{kind}", str(path)))
    before = {path: path.read_bytes() for path in tmp_path.iterdir() if path.is_file()}
    result = subprocess.run(
        [sys.executable, str(CLI), *paths, "--at", now],
        cwd=tmp_path,
        text=True,
        capture_output=True,
        check=False,
        timeout=15,
    )
    assert before == {path: path.read_bytes() for path in before}
    assert set(tmp_path.iterdir()) == set(before)
    return result


@pytest.mark.parametrize("shared,purpose_names", [(False, False), (True, False), (False, True)])
def test_synthetic_compiled_selection_and_clean_environment_acceptance(
    tmp_path: Path,
    shared: bool,
    purpose_names: bool,
) -> None:
    result = run_cli(tmp_path, synthetic_bundle(shared=shared, purpose_names=purpose_names))
    assert result.returncode == 0, result.stderr
    assert result.stderr == ""
    report = json.loads(result.stdout)
    assert report == {
        "status": "pass",
        "scope": "local supplied-evidence comparison only",
        "target_readiness": "not established",
    }


@pytest.mark.parametrize("tier", TIERS)
@pytest.mark.parametrize("suffix", ("DeploymentName", "ModelName", "ModelVersion"))
@pytest.mark.parametrize("boundary", ("parameters", "child_parameters"))
def test_each_of_nine_selections_is_checked(tmp_path: Path, tier: str, suffix: str, boundary: str) -> None:
    bundle = synthetic_bundle()
    bundle["outputs"][boundary][tier + suffix] = "not-passed-through"
    result = run_cli(tmp_path, bundle)
    assert result.returncode == 1
    assert boundary in result.stderr


@pytest.mark.parametrize("service", ("api", "agents"))
@pytest.mark.parametrize("suffix", ("DEPLOYMENT", "MODEL_ID", "MODEL_VERSION", "MODEL_KEY"))
def test_complete_same_tier_identity_required_for_both_services(tmp_path: Path, service: str, suffix: str) -> None:
    bundle = synthetic_bundle()
    del bundle["candidate"]["services"][service]["environment"]["AZURE_AI_DRAFTING_" + suffix]
    bundle["outputs"]["snapshot"]["services"] = copy.deepcopy(bundle["candidate"]["services"])
    rebind(bundle)
    result = run_cli(tmp_path, bundle)
    assert result.returncode == 1
    assert "DRAFTING_" + suffix in result.stderr


@pytest.mark.parametrize(
    "change",
    ("conflict", "ambiguous", "alias", "embedding", "embedding_coordinate", "legacy", "rename"),
)
def test_generated_output_invariants_fail_closed(tmp_path: Path, change: str) -> None:
    bundle = synthetic_bundle(shared=change == "ambiguous")
    for kind in ("candidate", "outputs"):
        services = bundle[kind]["services"] if kind == "candidate" else bundle[kind]["snapshot"]["services"]
        for service in services.values():
            env = service["environment"]
            raw = env["AZURE_AI_PROJECT_DEPLOYMENTS"]
            if change == "conflict":
                raw += ",reasoning=unrelated"
            elif change == "ambiguous":
                raw += ",synthetic-shared@synthetic-v=old-0"
            elif change == "alias":
                raw = raw.replace("reasoning=old-0,", "")
            elif change == "embedding":
                env["EMBEDDING_DEPLOYMENT_NAME"] = "changed-e"
            elif change == "embedding_coordinate":
                raw = raw.replace(",text-embedding-3-large@1=old-e", "")
            elif change == "legacy":
                raw = raw.replace("synthetic-model-0=old-0,", "")
            else:
                env["AZURE_AI_REASONING_DEPLOYMENT"] = "reasoning-synthetic"
            env["AZURE_AI_PROJECT_DEPLOYMENTS"] = raw
    rebind(bundle)
    result = run_cli(tmp_path, bundle)
    assert result.returncode == 1
    assert result.stdout == ""
    assert "ERROR:" in result.stderr


def test_purpose_defaults_cannot_replace_approved_existing_resources(tmp_path: Path) -> None:
    bundle = synthetic_bundle()
    for tier in TIERS:
        bundle["outputs"]["snapshot"]["deployments"][tier]["name"] = tier + "-synthetic"
        for boundary in ("parameters", "child_parameters"):
            bundle["outputs"][boundary][tier + "DeploymentName"] = tier + "-synthetic"
    result = run_cli(tmp_path, bundle)
    assert result.returncode == 1
    assert "outputs.snapshot.deployments" in result.stderr
