"""Synthetic P2 procedure checks; no target approval, readiness or inference."""

from __future__ import annotations

import copy
import json
import runpy
import socket
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest

from tests.contract.test_llm_deployment_configuration import CLI, KINDS, NOW, TIERS, digest, synthetic_bundle

STAGES = ("provision", "canary", "switch", "forward", "rollback", "retain", "retire")
CHECKS = ("common", "maf", "controller", "dispatcher", "chat", "streaming", "provenance", "isolation")


def migration_bundle(*, shared: bool = False) -> tuple[dict[str, Any], dict[str, Any]]:
    """Construct a labelled tabletop, deliberately not operational evidence."""
    bundle = synthetic_bundle(shared=shared)
    replacement = synthetic_bundle(purpose_names=True, shared=shared)
    old = bundle["candidate"]
    new = replacement["candidate"]
    window = {"start": "2040-01-01T10:00:00Z", "end": "2040-01-01T13:00:00Z"}
    decisions = {
        "observation": "synthetic observation criterion; no production duration selected",
        "retention": "keep both resource sets and corrected pairs pending separate G6",
        "rollback_triggers": "any route, model, safety, streaming or audit discrepancy",
    }
    bindings = {
        "old": copy.deepcopy(old["bindings"]),
        "new": copy.deepcopy(new["bindings"]),
        "old_services": copy.deepcopy(old["services"]),
        "new_services": copy.deepcopy(new["services"]),
        "proposal_digest": digest(replacement["outputs"]["snapshot"]),
        "procedure_digest": digest({"window": window, "decisions": decisions}),
    }
    metadata = {
        key: copy.deepcopy(bundle["inventory"][key])
        for key in (
            "synthetic",
            "target",
            "observed_at",
            "source_revision",
            "approval",
            "policy_id",
            "policy_version",
            "invalidation",
        )
    }
    metadata["bindings"] = bindings
    migration = {
        **copy.deepcopy(metadata),
        "proposal": copy.deepcopy(replacement["outputs"]["snapshot"]),
        "new_bindings": copy.deepcopy(new["bindings"]),
        "window": window,
        "decisions": decisions,
        "records": {},
    }
    records = migration["records"]
    for kind in (
        "governance",
        "what_if",
        "quota",
        "rollback",
        "readiness",
        "verification",
        "observation",
        "dependencies",
    ):
        records[kind] = {**copy.deepcopy(metadata), "reference": "synthetic-" + kind}
        bundle["baseline"]["freshness_policy"]["max_age_seconds"][kind] = 7200
    bundle["baseline"]["freshness_policy"]["max_age_seconds"]["migration"] = 7200
    records["governance"]["passed"] = True
    records["what_if"]["passed"] = True
    records["quota"]["pools"] = [
        {
            "subscription": metadata["target"]["subscription"],
            "region": metadata["target"]["region"],
            "model_id": bundle["outputs"]["snapshot"]["deployments"][tier]["model_id"],
            "sku": "synthetic-sku",
            "limit": 100,
            "other_allocated": 4,
            "margin": 2,
            "allocations": {
                bundle["outputs"]["snapshot"]["deployments"][tier]["name"]: index,
                replacement["outputs"]["snapshot"]["deployments"][tier]["name"]: index,
            },
        }
        for index, tier in enumerate(TIERS, 1)
    ]
    if shared:
        pools = records["quota"]["pools"]
        pools[0]["allocations"] = {name: value for pool in pools for name, value in pool["allocations"].items()}
        records["quota"]["pools"] = pools[:1]
    records["rollback"].update(
        services=copy.deepcopy(old["services"]),
        retained=True,
        checks=dict.fromkeys(CHECKS, True),
    )
    records["readiness"].update(
        snapshot=copy.deepcopy(migration["proposal"]),
        provisioning_succeeded=True,
        ready=True,
        collection_authority=copy.deepcopy(bundle["inventory"]["collection_authority"]),
    )
    records["readiness"]["observed_at"] = "2040-01-01T11:40:00Z"
    records["readiness"]["invalidation"]["evaluated_at"] = "2040-01-01T11:42:00Z"
    records["readiness"]["approval"]["approved_at"] = "2040-01-01T11:45:00Z"
    records["verification"].update(
        services=copy.deepcopy(new["services"]),
        checks=dict.fromkeys(CHECKS, True),
        outcome="pass",
    )
    records["observation"].update(criteria_met=True, rollback_rehearsal_passed=True, retain_old=True)
    records["dependencies"]["remaining"] = []
    migration["approvals"] = {
        stage: {
            **copy.deepcopy(metadata),
            "gate": "G5a" if stage == "provision" else "G6" if stage == "retire" else "G5b",
            "stage": stage,
            "reference": "synthetic-independent-" + stage,
        }
        for stage in STAGES
    }
    for stage in STAGES:
        if stage != "provision":
            migration["approvals"][stage]["approval"]["approved_at"] = "2040-01-01T11:50:00Z"
    return bundle, migration


def run_migration(
    tmp_path: Path,
    bundle: dict[str, Any],
    migration: dict[str, Any],
    stage: str = "provision",
) -> subprocess.CompletedProcess[str]:
    arguments = []
    for kind, value in {**bundle, "migration": migration}.items():
        path = tmp_path / f"{kind}.json"
        path.write_text(json.dumps(value), encoding="utf-8")
        arguments.extend(("--" + kind, str(path)))
    before = {path: path.read_bytes() for path in tmp_path.iterdir()}
    result = subprocess.run(
        [sys.executable, str(CLI), *arguments, "--stage", stage, "--at", NOW],
        cwd=tmp_path,
        text=True,
        capture_output=True,
        check=False,
        timeout=15,
    )
    assert before == {path: path.read_bytes() for path in tmp_path.iterdir()}
    return result


@pytest.mark.parametrize("stage", STAGES)
def test_synthetic_stage_comparison_never_grants_authority(tmp_path: Path, stage: str) -> None:
    bundle, migration = migration_bundle()
    result = run_migration(tmp_path, bundle, migration, stage)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == {
        "status": "pass",
        "scope": "local supplied-evidence comparison only",
        "target_readiness": "not established",
        "migration_stage": stage,
        "operational_authority": "not granted",
    }


def test_g5a_does_not_require_uncreated_replacement_readiness(tmp_path: Path) -> None:
    bundle, migration = migration_bundle()
    del migration["records"]["readiness"]
    assert run_migration(tmp_path, bundle, migration).returncode == 0
    result = run_migration(tmp_path, bundle, migration, "switch")
    assert result.returncode == 1
    assert "readiness" in result.stderr


@pytest.mark.parametrize("stage", STAGES)
def test_independent_stage_approval_required(tmp_path: Path, stage: str) -> None:
    bundle, migration = migration_bundle()
    del migration["approvals"][stage]
    result = run_migration(tmp_path, bundle, migration, stage)
    assert result.returncode == 1
    assert "approvals." + stage in result.stderr


@pytest.mark.parametrize("kind", ("migration", "quota", "governance", "what_if", "rollback", "readiness"))
@pytest.mark.parametrize(
    "field",
    ("target", "source_revision", "observed_at", "approval", "policy_id", "policy_version", "bindings", "invalidation"),
)
def test_evidence_metadata_is_mandatory(tmp_path: Path, kind: str, field: str) -> None:
    bundle, migration = migration_bundle()
    record = migration if kind == "migration" else migration["records"][kind]
    del record[field]
    result = run_migration(tmp_path, bundle, migration, "switch")
    assert result.returncode == 1
    assert field in result.stderr


@pytest.mark.parametrize(
    "mutation",
    (
        "model",
        "protection",
        "embedding",
        "controls",
        "collision",
        "quota_missing",
        "quota_pool",
        "quota_old_missing",
        "quota_new_missing",
        "quota_exhausted",
        "quota_bool",
        "old_pair",
        "rollback_unverified",
        "rollback_not_retained",
        "decision",
        "window",
        "expired",
        "invalidation",
        "policy_window",
        "wrong_binding",
        "g5a_is_not_g5b",
        "readiness_drift",
        "readiness_not_ready",
        "g0_missing",
        "g0_scope",
        "g0_operations",
        "g0_window",
        "governance_failed",
        "what_if_failed",
        "candidate_drift",
        "approval_scope",
        "approval_stage",
        "approval_expired",
    ),
)
def test_fail_closed_without_operations(tmp_path: Path, mutation: str) -> None:
    bundle, migration = migration_bundle()
    records = migration["records"]
    if mutation in ("model", "protection"):
        field = "model_version" if mutation == "model" else "effective_filters"
        migration["proposal"]["deployments"]["simulation"][field] = "changed"
    elif mutation in ("embedding", "controls"):
        migration["proposal"][mutation] = {}
    elif mutation == "collision":
        migration["proposal"]["deployments"]["simulation"]["name"] = "old-0"
    elif mutation == "quota_missing":
        del records["quota"]
    elif mutation == "quota_pool":
        records["quota"]["pools"][0]["region"] = "other"
    elif mutation in ("quota_old_missing", "quota_new_missing"):
        name = "old-0" if mutation == "quota_old_missing" else "reasoning-synthetic"
        del records["quota"]["pools"][0]["allocations"][name]
    elif mutation == "quota_exhausted":
        records["quota"]["pools"][0]["limit"] = 1
    elif mutation == "quota_bool":
        records["quota"]["pools"][0]["margin"] = True
    elif mutation == "old_pair":
        records["rollback"]["services"]["agents"]["revision"] = "pre-P1-ambiguous"
    elif mutation == "rollback_unverified":
        records["rollback"]["checks"]["isolation"] = False
    elif mutation == "rollback_not_retained":
        records["rollback"]["retained"] = False
    elif mutation == "decision":
        del migration["decisions"]["retention"]
    elif mutation == "window":
        migration["window"]["end"] = "2039-01-01T00:00:00Z"
    elif mutation == "expired":
        records["quota"]["observed_at"] = "2039-01-01T00:00:00Z"
    elif mutation == "invalidation":
        records["quota"]["invalidation"]["events"] = ["model"]
    elif mutation == "policy_window":
        del bundle["baseline"]["freshness_policy"]["max_age_seconds"]["quota"]
    elif mutation == "wrong_binding":
        records["quota"]["bindings"]["old"]["api_image"] = "other"
    elif mutation == "g5a_is_not_g5b":
        migration["approvals"]["switch"]["gate"] = "G5a"
    elif mutation == "readiness_drift":
        records["readiness"]["snapshot"]["deployments"]["reasoning"]["capacity"] = 999
    elif mutation == "readiness_not_ready":
        records["readiness"]["ready"] = False
    elif mutation.startswith("g0_"):
        authority = records["readiness"]["collection_authority"]
        if mutation == "g0_missing":
            del records["readiness"]["collection_authority"]
        elif mutation == "g0_scope":
            authority["target"]["account_id"] = "other"
        elif mutation == "g0_operations":
            authority["operations"] = ["inventory"]
        else:
            authority["valid_until"] = "2039-01-01T00:00:00Z"
    elif mutation in ("governance_failed", "what_if_failed"):
        records[mutation.removesuffix("_failed")]["passed"] = False
    elif mutation == "candidate_drift":
        migration["proposal"]["services"]["agents"]["environment"]["AZURE_AI_SIMULATION_DEPLOYMENT"] = "old-0"
    elif mutation == "approval_scope":
        migration["approvals"]["switch"]["target"]["environment"] = "different"
    elif mutation == "approval_stage":
        migration["approvals"]["switch"]["stage"] = "canary"
    else:
        migration["approvals"]["switch"]["approval"]["valid_until"] = "2039-01-01T00:00:00Z"
    result = run_migration(tmp_path, bundle, migration, "switch")
    assert result.returncode == 1, result.stdout
    assert result.stdout == ""


def test_failed_forward_still_allows_separately_approved_rollback(tmp_path: Path) -> None:
    bundle, migration = migration_bundle()
    migration["records"]["verification"]["outcome"] = "failed"
    migration["records"]["verification"]["checks"]["streaming"] = False
    assert run_migration(tmp_path, bundle, migration, "forward").returncode == 1
    assert run_migration(tmp_path, bundle, migration, "rollback").returncode == 0


@pytest.mark.parametrize("mutation", ("observation", "rehearsal", "dependency", "g6"))
def test_retirement_never_follows_traffic_approval_implicitly(tmp_path: Path, mutation: str) -> None:
    bundle, migration = migration_bundle()
    if mutation == "observation":
        migration["records"]["observation"]["criteria_met"] = False
    elif mutation == "rehearsal":
        migration["records"]["observation"]["rollback_rehearsal_passed"] = False
    elif mutation == "dependency":
        migration["records"]["dependencies"]["remaining"] = ["worker/old-0"]
    else:
        del migration["approvals"]["retire"]
    result = run_migration(tmp_path, bundle, migration, "retire")
    assert result.returncode == 1


def test_override_rejects_unlabelled_migration(tmp_path: Path) -> None:
    bundle, migration = migration_bundle()
    migration["synthetic"] = False
    result = run_migration(tmp_path, bundle, migration)
    assert result.returncode == 1
    assert "synthetic" in result.stderr


def test_no_dependencies_added_to_existing_cli_contract() -> None:
    assert KINDS == ("inventory", "baseline", "outputs", "candidate")


@pytest.mark.parametrize("exhausted", (False, True))
def test_shared_model_uses_one_aggregate_actual_pool(tmp_path: Path, exhausted: bool) -> None:
    bundle, migration = migration_bundle(shared=True)
    if exhausted:
        migration["records"]["quota"]["pools"][0]["limit"] = 17
    result = run_migration(tmp_path, bundle, migration)
    assert result.returncode == (1 if exhausted else 0), result.stderr


@pytest.mark.parametrize("stage", STAGES)
def test_comparison_cannot_open_network(monkeypatch: pytest.MonkeyPatch, stage: str) -> None:
    calls = []

    def forbidden(*args: Any, **kwargs: Any) -> Any:
        calls.append((args, kwargs))
        raise AssertionError("offline migration must not open sockets")

    monkeypatch.setattr(socket, "socket", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)
    module = runpy.run_path(str(CLI))
    bundle, migration = migration_bundle()
    now = datetime.fromisoformat(NOW.replace("Z", "+00:00"))
    module["verify"](bundle, now)
    module["verify_migration"](bundle, migration, stage, now)
    assert calls == []


@pytest.mark.parametrize("tier", TIERS)
@pytest.mark.parametrize(
    "field",
    ("model_id", "model_version", "format", "sku", "capacity", "rai_policy", "effective_filters", "version_upgrade"),
)
def test_replacement_parity_is_not_just_a_name_check(tmp_path: Path, tier: str, field: str) -> None:
    bundle, migration = migration_bundle()
    replacement = migration["proposal"]["deployments"][tier]
    replacement[field] = 99 if field == "capacity" else {"changed": True} if field == "effective_filters" else "changed"
    result = run_migration(tmp_path, bundle, migration)
    assert result.returncode == 1
    assert "unchanged_model_protections" in result.stderr


@pytest.mark.parametrize("route", ("extra_legacy", "wrong_tier"))
def test_rebound_new_config_still_requires_exact_compatible_routes(tmp_path: Path, route: str) -> None:
    bundle, migration = migration_bundle()
    for service in migration["proposal"]["services"].values():
        environment = service["environment"]
        if route == "extra_legacy":
            environment["AZURE_AI_PROJECT_DEPLOYMENTS"] += ",invented=reasoning-synthetic"
        else:
            environment["AZURE_AI_SIMULATION_DEPLOYMENT"] = "reasoning-synthetic"
    migration["new_bindings"]["configuration_digest"] = digest(
        {name: service["environment"] for name, service in migration["proposal"]["services"].items()}
    )
    result = run_migration(tmp_path, bundle, migration)
    assert result.returncode == 1
    assert "candidate.services" in result.stderr


@pytest.mark.parametrize("section", ("records", "approvals"))
def test_nested_synthetic_label_cannot_be_bypassed(tmp_path: Path, section: str) -> None:
    bundle, migration = migration_bundle()
    next(iter(migration[section].values()))["synthetic"] = False
    result = run_migration(tmp_path, bundle, migration)
    assert result.returncode == 1
    assert "synthetic" in result.stderr


@pytest.mark.parametrize("missing", ("--stage", "--migration"))
def test_migration_flags_must_be_paired(tmp_path: Path, missing: str) -> None:
    bundle, migration = migration_bundle()
    assert run_migration(tmp_path, bundle, migration).returncode == 0
    args = [sys.executable, str(CLI)]
    for kind in KINDS:
        args.extend(("--" + kind, str(tmp_path / (kind + ".json"))))
    args.extend(["--migration", str(tmp_path / "migration.json")] if missing == "--stage" else ["--stage", "provision"])
    result = subprocess.run(args, text=True, capture_output=True, check=False, timeout=15)
    assert result.returncode == 2
    assert "must be supplied together" in result.stderr


@pytest.mark.parametrize("early", ("readiness", "traffic"))
def test_postprovision_evidence_precedes_traffic_approval(tmp_path: Path, early: str) -> None:
    bundle, migration = migration_bundle()
    if early == "readiness":
        migration["records"]["readiness"]["observed_at"] = "2040-01-01T11:00:00Z"
    else:
        migration["approvals"]["switch"]["approval"]["approved_at"] = "2040-01-01T11:30:00Z"
    result = run_migration(tmp_path, bundle, migration, "switch")
    assert result.returncode == 1
    assert "must follow" in result.stderr
