"""Compare supplied local P1 evidence without network calls, writes or authority inference.

Usage and JSON contracts: specs/041-llm-deployment-routing/{rollout-evidence,naming-migration}.md.
Exit codes: 0 comparison passed (not target readiness), 1 invalid evidence, 2 usage.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "apps" / "agents"))

from common.llm_config import (  # noqa: E402
    DeploymentResolver,
    FoundryConfigurationError,
    parse_deployment_entries,
    parse_deployment_map,
)

KINDS = ("inventory", "baseline", "outputs", "candidate")
TIERS = ("reasoning", "drafting", "simulation")
TARGET_FIELDS = ("tenant", "subscription", "resource_group", "account_id", "environment", "endpoint", "region")
BINDING_FIELDS = ("configuration_digest", "api_image", "agents_image", "compiled_proposal_revision")
INVALIDATION_EVENTS = (
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
MIGRATION_STAGES = ("provision", "canary", "switch", "forward", "rollback", "retain", "retire")
MIGRATION_CHECKS = ("common", "maf", "controller", "dispatcher", "chat", "streaming", "provenance", "isolation")


class EvidenceError(ValueError):
    """Missing, unreadable, stale or inconsistent supplied evidence."""


def require(condition: bool, location: str, rule: str) -> None:
    if not condition:
        raise EvidenceError(f"{location}: {rule}")


def object_at(value: Any, location: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise EvidenceError(f"{location}: required JSON object is missing or unreadable")
    return value


def text(value: Any, location: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise EvidenceError(f"{location}: required non-empty string")
    return value


def timestamp(value: Any, location: str) -> datetime:
    raw = text(value, location)
    try:
        result = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        raise EvidenceError(f"{location}: required ISO-8601 timestamp with timezone") from None
    require(result.tzinfo is not None, location, "timestamp must include timezone")
    return result


def same(actual: Any, expected: Any, location: str) -> None:
    require(
        json.dumps(actual, sort_keys=True) == json.dumps(expected, sort_keys=True),
        location,
        "mismatch; reconcile/recollect and reapprove, never substitute defaults",
    )


def approval(value: Any, location: str, now: datetime, *, observed: datetime | None = None) -> None:
    item = object_at(value, location)
    text(item.get("approver"), location + ".approver")
    approved = timestamp(item.get("approved_at"), location + ".approved_at")
    expires = timestamp(item.get("valid_until"), location + ".valid_until")
    require(approved <= now <= expires, location, "approval not current or expired")
    if observed is not None:
        require(observed <= approved, location, "approval predates observation")


def strings(value: Any, fields: tuple[str, ...], location: str) -> dict[str, Any]:
    item = object_at(value, location)
    for field in fields:
        text(item.get(field), location + "." + field)
    return item


def readable(value: Any, location: str) -> None:
    require(value is not None, location, "unreadable/null property")
    if isinstance(value, dict):
        require(bool(value), location, "empty/unreadable property object")
        for child in value.values():
            readable(child, location)
    elif isinstance(value, list):
        for child in value:
            readable(child, location)
    elif isinstance(value, str):
        text(value, location)
    else:
        require(isinstance(value, (bool, int, float)), location, "invalid property type")
        if isinstance(value, float):
            require(math.isfinite(value), location, "non-finite property")


def services_at(value: Any, location: str) -> dict[str, Any]:
    services = object_at(value, location)
    require(set(services) == {"api", "agents"}, location, "both API and agents pairs required")
    for name in ("api", "agents"):
        service = strings(services[name], ("image", "revision"), location + "." + name)
        require(
            bool(re.fullmatch(r"sha256:[0-9a-f]{64}", service["image"])),
            location,
            "immutable image digest required",
        )
        environment = object_at(service.get("environment"), location + "." + name + ".environment")
        require(bool(environment), location, "environment snapshot required")
        for setting in environment.values():
            require(isinstance(setting, str), location, "environment settings must be strings")
    return services


def deployment_at(value: Any, location: str, *, embedding: bool = False) -> dict[str, Any]:
    deployment = strings(
        value,
        ("name", "model_id", "model_version", "format", "sku", "rai_policy", "version_upgrade"),
        location,
    )
    capacity = deployment.get("capacity")
    require(type(capacity) is int and capacity > 0, location + ".capacity", "positive integer required")
    object_at(deployment.get("effective_filters"), location + ".effective_filters")
    readable(deployment, location)
    if embedding:
        dimensions = deployment.get("dimensions")
        require(type(dimensions) is int and dimensions > 0, location + ".dimensions", "positive integer required")
    return deployment


def snapshot_at(value: Any, location: str) -> dict[str, Any]:
    snapshot = object_at(value, location)
    deployments = object_at(snapshot.get("deployments"), location + ".deployments")
    require(set(deployments) == set(TIERS), location + ".deployments", "three explicit tier identities required")
    for tier in TIERS:
        deployment_at(deployments[tier], location + ".deployments." + tier)
    deployment_at(snapshot.get("embedding"), location + ".embedding", embedding=True)
    controls = object_at(snapshot.get("controls"), location + ".controls")
    for field in ("rbac", "managed_identity", "access", "network", "authentication", "diagnostics"):
        object_at(controls.get(field), location + ".controls." + field)
    same(controls.get("residency"), "AU", location + ".controls.residency")
    readable(controls, location + ".controls")
    services_at(snapshot.get("services"), location + ".services")
    return snapshot


def expected_map(snapshot: dict[str, Any], current_env: dict[str, str]) -> dict[str, str]:
    deployments = snapshot["deployments"]
    embedding = snapshot["embedding"]
    coordinates: dict[str, set[str]] = {}
    for deployment in [*deployments.values(), embedding]:
        for key in (deployment["model_id"], f"{deployment['model_id']}@{deployment['model_version']}"):
            coordinates.setdefault(key, set()).add(deployment["name"])
    result = {tier: deployments[tier]["name"] for tier in TIERS}
    for key, destinations in coordinates.items():
        if "@" in key and len(destinations) == 1:
            result[key] = next(iter(destinations))
    # Historical CSV may contain the known conflicting coordinate. Validate each
    # raw entry, then retain only unambiguous legacy keys; never reuse it as a candidate map.
    legacy: dict[str, set[str]] = {}
    raw = text(current_env.get("AZURE_AI_PROJECT_DEPLOYMENTS"), "baseline.snapshot.services.environment.CSV")
    for entry in raw.split(","):
        text(entry, "baseline.snapshot.services.environment.CSV entry")
        for parsed in parse_deployment_entries(entry):
            legacy.setdefault(parsed.routing_key, set()).add(parsed.deployment_name)
    for key, destinations in legacy.items():
        if key in TIERS or len(destinations) != 1 or len(coordinates.get(key, destinations)) != 1:
            continue
        result.setdefault(key, next(iter(destinations)))
    return result


def routing_checks(
    snapshot: dict[str, Any],
    current: dict[str, Any],
    services: dict[str, Any],
    target: dict[str, Any],
) -> None:
    for service_name in ("api", "agents"):
        environment = services[service_name]["environment"]
        location = "candidate.services." + service_name + ".environment"
        for setting, expected in (
            ("AZURE_AI_PROJECT_ENDPOINT", target["endpoint"]),
            ("AZURE_AI_PROJECT_REGION", target["region"]),
            ("EMBEDDING_DEPLOYMENT_NAME", snapshot["embedding"]["name"]),
        ):
            same(environment.get(setting), expected, location + "." + setting)
        for tier in TIERS:
            deployment = snapshot["deployments"][tier]
            prefix = "AZURE_AI_" + tier.upper() + "_"
            for suffix, field in (("DEPLOYMENT", "name"), ("MODEL_ID", "model_id"), ("MODEL_VERSION", "model_version")):
                same(environment.get(prefix + suffix), deployment[field], location + "." + prefix + suffix)
            same(
                environment.get(prefix + "MODEL_KEY"),
                f"{deployment['model_id']}@{deployment['model_version']}",
                location + "." + prefix + "MODEL_KEY",
            )
        try:
            # Validate the complete raw CSV before any lossy map conversion.
            raw = text(environment.get("AZURE_AI_PROJECT_DEPLOYMENTS"), location + ".AZURE_AI_PROJECT_DEPLOYMENTS")
            mapping = parse_deployment_map(raw)
            resolver = DeploymentResolver.from_environment(
                environment,
                configuration_revision=services[service_name]["revision"],
            )
            for tier in TIERS:
                resolver.resolve(tier)
            expected = expected_map(snapshot, current["services"][service_name]["environment"])
        except FoundryConfigurationError:
            raise EvidenceError(
                location + ": invalid CSV or simulation isolation; check shared routing contract",
            ) from None
        same(mapping, expected, location + ".AZURE_AI_PROJECT_DEPLOYMENTS aliases/coordinates/legacy/embedding")


def verify(evidence: dict[str, dict[str, Any]], now: datetime) -> None:
    """Validate P1 supplied evidence; this cannot authenticate collection or grant release authority."""
    baseline, inventory, outputs, candidate = (
        evidence[kind] for kind in ("baseline", "inventory", "outputs", "candidate")
    )
    target = strings(baseline.get("target"), TARGET_FIELDS, "baseline.target")
    require(target["region"].lower().startswith("australia"), "baseline.target.region", "AU residency required")
    policy = strings(baseline.get("freshness_policy"), ("id", "version"), "baseline.freshness_policy")
    approval(policy.get("approval"), "baseline.freshness_policy.approval", now)
    windows = object_at(policy.get("max_age_seconds"), "baseline.freshness_policy.max_age_seconds")
    actions = object_at(policy.get("invalidation_actions"), "baseline.freshness_policy.invalidation_actions")
    for event in INVALIDATION_EVENTS:
        decision = actions.get(event)
        require(
            isinstance(decision, list)
            and bool(decision)
            and all(isinstance(action, str) and action in ("recollect", "reapprove") for action in decision),
            "baseline.freshness_policy.invalidation_actions",
            "explicit recollection/reapproval decisions required",
        )
    services = services_at(candidate.get("services"), "candidate.services")
    bindings = strings(candidate.get("bindings"), BINDING_FIELDS, "candidate.bindings")
    environments = {name: service["environment"] for name, service in services.items()}
    config_digest = hashlib.sha256(
        json.dumps(environments, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8"),
    ).hexdigest()
    same(bindings["configuration_digest"], config_digest, "candidate.bindings.configuration_digest")
    for name in ("api", "agents"):
        same(bindings[name + "_image"], services[name]["image"], "candidate.bindings." + name + "_image")
    for kind in KINDS:
        item = evidence[kind]
        strings(item.get("target"), TARGET_FIELDS, kind + ".target")
        same(item["target"], target, kind + ".target")
        text(item.get("source_revision"), kind + ".source_revision")
        observed = timestamp(item.get("observed_at"), kind + ".observed_at")
        require(observed <= now, kind + ".observed_at", "observation cannot be in the future")
        approval(item.get("approval"), kind + ".approval", now, observed=observed)
        same(item.get("policy_id"), policy["id"], kind + ".policy_id")
        same(item.get("policy_version"), policy["version"], kind + ".policy_version")
        require(kind in windows, "freshness_policy.max_age_seconds." + kind, "explicit window or null required")
        window = windows[kind]
        if window is not None:
            require(
                type(window) in (int, float)
                and (not isinstance(window, float) or math.isfinite(window))
                and window > 0,
                "freshness_policy.max_age_seconds." + kind,
                "positive seconds or explicit null required",
            )
            require((now - observed).total_seconds() <= window, kind, "expired under supplied freshness policy")
        invalidation = object_at(item.get("invalidation"), kind + ".invalidation")
        evaluated = timestamp(invalidation.get("evaluated_at"), kind + ".invalidation.evaluated_at")
        require(observed <= evaluated <= now, kind + ".invalidation", "evaluation must cover this observation")
        require(
            invalidation.get("events") == [],
            kind + ".invalidation",
            "unevaluated or invalidating events; follow approved recollection/reapproval policy",
        )
        item_bindings = strings(item.get("bindings"), BINDING_FIELDS, kind + ".bindings")
        if kind == "baseline" and item_bindings != bindings:
            reconciliation = object_at(item.get("reconciliation"), "baseline.reconciliation (bindings changed)")
            for field, expected in (
                ("from_bindings", item_bindings),
                ("to_bindings", bindings),
                ("target", target),
                ("source_revision", item["source_revision"]),
                ("policy_id", policy["id"]),
                ("policy_version", policy["version"]),
            ):
                same(reconciliation.get(field), expected, "baseline.reconciliation." + field)
            approval(reconciliation.get("approval"), "baseline.reconciliation.approval", now, observed=observed)
        else:
            same(item_bindings, bindings, kind + ".bindings")
    authority = strings(
        inventory.get("collection_authority"),
        ("reference", "approver"),
        "inventory.collection_authority",
    )
    same(authority.get("target"), target, "inventory.collection_authority.target")
    operations = authority.get("operations")
    require(
        isinstance(operations, list) and all(operation in operations for operation in ("inventory", "metadata")),
        "inventory.collection_authority.operations",
        "inventory and metadata collection scope required",
    )
    start = timestamp(authority.get("valid_from"), "inventory.collection_authority.valid_from")
    end = timestamp(authority.get("valid_until"), "inventory.collection_authority.valid_until")
    for kind in ("inventory", "baseline"):
        observed = timestamp(evidence[kind]["observed_at"], kind + ".observed_at")
        require(start <= observed <= end, "inventory.collection_authority", "collection outside authorised window")
    same(baseline.get("state"), "approved", "baseline.state")
    current = snapshot_at(baseline.get("snapshot"), "baseline.snapshot")
    actual = snapshot_at(inventory.get("snapshot"), "inventory.snapshot")
    proposal = snapshot_at(outputs.get("snapshot"), "outputs.snapshot")
    same(actual, current, "inventory.snapshot")
    for field in ("deployments", "embedding", "controls"):
        same(proposal[field], current[field], "outputs.snapshot." + field)
    same(proposal["services"], services, "outputs.snapshot.services")
    parameters = object_at(outputs.get("parameters"), "outputs.parameters")
    expected_parameters = {}
    for tier in TIERS:
        for suffix, field in (("DeploymentName", "name"), ("ModelName", "model_id"), ("ModelVersion", "model_version")):
            expected_parameters[tier + suffix] = current["deployments"][tier][field]
    same(parameters, expected_parameters, "outputs.parameters")
    same(outputs.get("child_parameters"), parameters, "outputs.child_parameters")
    routing_checks(proposal, current, services, target)


def canonical_digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8"),
    ).hexdigest()


def migration_metadata(
    value: Any,
    kind: str,
    baseline: dict[str, Any],
    bindings: dict[str, Any],
    now: datetime,
    location: str,
) -> dict[str, Any]:
    item = object_at(value, location)
    same(item.get("target"), baseline["target"], location + ".target")
    text(item.get("source_revision"), location + ".source_revision")
    observed = timestamp(item.get("observed_at"), location + ".observed_at")
    require(observed <= now, location + ".observed_at", "observation cannot be in the future")
    approval(item.get("approval"), location + ".approval", now, observed=observed)
    policy = baseline["freshness_policy"]
    same(item.get("policy_id"), policy["id"], location + ".policy_id")
    same(item.get("policy_version"), policy["version"], location + ".policy_version")
    windows = policy["max_age_seconds"]
    require(kind in windows, location + ".max_age_seconds", "explicit approved window or null required")
    window = windows[kind]
    if window is not None:
        require(
            type(window) in (int, float) and (not isinstance(window, float) or math.isfinite(window)) and window > 0,
            location + ".max_age_seconds",
            "positive finite seconds or explicit null required",
        )
        require((now - observed).total_seconds() <= window, location, "expired under supplied freshness policy")
    invalidation = object_at(item.get("invalidation"), location + ".invalidation")
    evaluated = timestamp(invalidation.get("evaluated_at"), location + ".invalidation.evaluated_at")
    require(observed <= evaluated <= now, location + ".invalidation", "evaluation must cover observation")
    same(invalidation.get("events"), [], location + ".invalidation.events")
    same(item.get("bindings"), bindings, location + ".bindings")
    return item


def migration_quota(
    record: dict[str, Any],
    old: dict[str, Any],
    new: dict[str, Any],
    target: dict[str, Any],
) -> None:
    expected: dict[tuple[str, str, str, str], dict[str, int]] = {}
    for snapshot in (old, new):
        for deployment in snapshot["deployments"].values():
            key = (target["subscription"], target["region"], deployment["model_id"], deployment["sku"])
            expected.setdefault(key, {})[deployment["name"]] = deployment["capacity"]
    pools = record.get("pools")
    if not isinstance(pools, list):
        raise EvidenceError("migration.quota.pools: actual quota pool evidence required")
    seen = set()
    for value in pools:
        pool = strings(value, ("subscription", "region", "model_id", "sku"), "migration.quota.pool")
        key = tuple(pool[field] for field in ("subscription", "region", "model_id", "sku"))
        require(key in expected and key not in seen, "migration.quota.pool", "wrong or duplicate actual pool")
        seen.add(key)
        allocations = object_at(pool.get("allocations"), "migration.quota.allocations")
        for capacity in allocations.values():
            require(type(capacity) is int and capacity > 0, "migration.quota.allocations", "positive integer required")
        same(allocations, expected[key], "migration.quota.allocations old+new")
        for field in ("limit", "other_allocated", "margin"):
            amount = pool.get(field)
            require(type(amount) is int and amount >= 0, "migration.quota." + field, "nonnegative integer required")
        require(
            pool["limit"] >= sum(allocations.values()) + pool["other_allocated"] + pool["margin"],
            "migration.quota.headroom",
            "actual pool must cover old+new, other allocations and approved operational margin",
        )
    same(sorted(seen), sorted(expected), "migration.quota.pools")


def migration_checks(record: dict[str, Any], services: dict[str, Any], location: str) -> None:
    same(record.get("services"), services, location + ".services")
    checks = object_at(record.get("checks"), location + ".checks")
    for name in MIGRATION_CHECKS:
        same(checks.get(name), True, location + ".checks." + name)


def verify_migration(
    evidence: dict[str, dict[str, Any]],
    migration: dict[str, Any],
    stage: str,
    now: datetime,
) -> None:
    """Compare supplied P2 records only; no action, state transition or authority is granted."""
    baseline = evidence["baseline"]
    old = evidence["outputs"]["snapshot"]
    proposal = snapshot_at(migration.get("proposal"), "migration.proposal")
    old_names = {deployment["name"] for deployment in old["deployments"].values()} | {old["embedding"]["name"]}
    new_names = []
    for tier in TIERS:
        before = old["deployments"][tier]
        after = proposal["deployments"][tier]
        require(after["name"] not in old_names, "migration.proposal.name", "replacement collides with old identity")
        new_names.append(after["name"])
        same(
            {key: value for key, value in after.items() if key != "name"},
            {key: value for key, value in before.items() if key != "name"},
            "migration.proposal." + tier + ".unchanged_model_protections",
        )
    require(len(set(new_names)) == len(TIERS), "migration.proposal.name", "unique replacements required")
    for field in ("embedding", "controls"):
        same(proposal[field], old[field], "migration.proposal." + field)
    new_bindings = strings(migration.get("new_bindings"), BINDING_FIELDS, "migration.new_bindings")
    services = proposal["services"]
    same(
        new_bindings["configuration_digest"],
        canonical_digest({name: service["environment"] for name, service in services.items()}),
        "migration.new_bindings.configuration_digest",
    )
    for name in ("api", "agents"):
        same(new_bindings[name + "_image"], services[name]["image"], "migration.new_bindings." + name)
    renamed = {old["deployments"][tier]["name"]: proposal["deployments"][tier]["name"] for tier in TIERS}
    compatible_current: dict[str, Any] = {"services": {}}
    for name, service in evidence["candidate"]["services"].items():
        entries = parse_deployment_entries(service["environment"]["AZURE_AI_PROJECT_DEPLOYMENTS"])
        compatible_current["services"][name] = {
            "environment": {
                "AZURE_AI_PROJECT_DEPLOYMENTS": ",".join(
                    f"{entry.routing_key}={renamed.get(entry.deployment_name, entry.deployment_name)}"
                    for entry in entries
                ),
            },
        }
    routing_checks(proposal, compatible_current, services, baseline["target"])
    bindings = {
        "old": evidence["candidate"]["bindings"],
        "new": new_bindings,
        "old_services": evidence["candidate"]["services"],
        "new_services": services,
        "proposal_digest": canonical_digest(proposal),
        "procedure_digest": canonical_digest(
            {"window": migration.get("window"), "decisions": migration.get("decisions")},
        ),
    }
    migration_metadata(migration, "migration", baseline, bindings, now, "migration")
    window = object_at(migration.get("window"), "migration.window")
    start = timestamp(window.get("start"), "migration.window.start")
    end = timestamp(window.get("end"), "migration.window.end")
    require(start <= now <= end, "migration.window", "outside approved migration window")
    strings(migration.get("decisions"), ("observation", "retention", "rollback_triggers"), "migration.decisions")
    records = object_at(migration.get("records"), "migration.records")
    approvals = object_at(migration.get("approvals"), "migration.approvals")

    def record(kind: str) -> dict[str, Any]:
        location = "migration.records." + kind
        item = migration_metadata(records.get(kind), kind, baseline, bindings, now, location)
        text(item.get("reference"), location + ".reference")
        return item

    def stage_approval(selected: str, gate: str) -> None:
        location = "migration.approvals." + selected
        item = migration_metadata(approvals.get(selected), "migration", baseline, bindings, now, location)
        text(item.get("reference"), location + ".reference")
        same(item.get("gate"), gate, location + ".gate")
        same(item.get("stage"), selected, location + ".stage")

    stage_approval("provision", "G5a")
    for kind in ("governance", "what_if"):
        same(record(kind).get("passed"), True, "migration.records." + kind + ".passed")
    migration_quota(record("quota"), old, proposal, baseline["target"])
    rollback = record("rollback")
    same(rollback.get("retained"), True, "migration.rollback.retained")
    migration_checks(rollback, evidence["candidate"]["services"], "migration.rollback")
    if stage == "provision":
        return

    readiness = record("readiness")
    same(readiness.get("snapshot"), proposal, "migration.readiness.snapshot")
    for field in ("provisioning_succeeded", "ready"):
        same(readiness.get(field), True, "migration.readiness." + field)
    authority = strings(
        readiness.get("collection_authority"),
        ("reference", "approver"),
        "migration.readiness.collection_authority",
    )
    same(authority.get("target"), baseline["target"], "migration.readiness.collection_authority.target")
    operations = authority.get("operations")
    require(
        isinstance(operations, list) and "metadata" in operations,
        "migration.readiness.collection_authority.operations",
        "G0 metadata scope required",
    )
    observed = timestamp(readiness["observed_at"], "migration.readiness.observed_at")
    provision_approved = timestamp(
        approvals["provision"]["approval"]["approved_at"],
        "migration.approvals.provision.approval.approved_at",
    )
    require(
        observed >= provision_approved,
        "migration.readiness.observed_at",
        "post-provision evidence must follow G5a",
    )
    valid_from = timestamp(authority.get("valid_from"), "migration.readiness.collection_authority.valid_from")
    valid_until = timestamp(authority.get("valid_until"), "migration.readiness.collection_authority.valid_until")
    require(
        valid_from <= observed <= valid_until,
        "migration.readiness.collection_authority",
        "outside G0 collection window",
    )
    stage_approval(stage, "G6" if stage == "retire" else "G5b")
    ready_approved = timestamp(readiness["approval"]["approved_at"], "migration.readiness.approval.approved_at")
    traffic_approved = timestamp(
        approvals[stage]["approval"]["approved_at"],
        "migration.approvals." + stage + ".approval.approved_at",
    )
    require(
        traffic_approved >= ready_approved,
        "migration.approvals." + stage,
        "stage approval must follow actual readiness evidence approval",
    )
    if stage in ("forward", "retain", "retire"):
        verification = record("verification")
        same(verification.get("outcome"), "pass", "migration.verification.outcome")
        migration_checks(verification, services, "migration.verification")
    if stage in ("retain", "retire"):
        observation = record("observation")
        for field in ("criteria_met", "rollback_rehearsal_passed", "retain_old"):
            same(observation.get(field), True, "migration.observation." + field)
    if stage == "retire":
        same(record("dependencies").get("remaining"), [], "migration.dependencies.remaining")


def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        require(key not in result, "JSON", "duplicate property; supply unambiguous evidence")
        result[key] = value
    return result


def reject_constant(value: str) -> Any:
    raise EvidenceError("JSON: non-finite constants are invalid evidence")


def finite_float(value: str) -> float:
    result = float(value)
    require(math.isfinite(result), "JSON", "non-finite numbers are invalid evidence")
    return result


def load(path: Path, kind: str) -> dict[str, Any]:
    try:
        content = path.read_text(encoding="utf-8")
        value = json.loads(
            content,
            object_pairs_hook=unique_object,
            parse_constant=reject_constant,
            parse_float=finite_float,
        )
    except (OSError, UnicodeError):
        raise EvidenceError(kind + ": cannot read UTF-8 evidence file; check path and permissions") from None
    except json.JSONDecodeError as exc:
        raise EvidenceError(f"{kind}: malformed JSON at line {exc.lineno}, column {exc.colno}") from None
    except EvidenceError:
        raise
    except (ValueError, RecursionError):
        raise EvidenceError(kind + ": JSON number/nesting exceeds parser limits; supply readable evidence") from None
    return object_at(value, kind)


def main() -> int:
    """Read local P1 and optional P2 evidence and report comparison status only."""
    parser = argparse.ArgumentParser(description=__doc__)
    for kind in KINDS:
        parser.add_argument("--" + kind, required=True, type=Path)
    parser.add_argument("--migration", type=Path, help="Optional local P2 evidence, never an execution request")
    parser.add_argument("--stage", choices=MIGRATION_STAGES, help="P2 stage to compare; requires --migration")
    parser.add_argument("--at", help="ISO-8601 evaluation time; omit for current UTC (synthetic testing only)")
    args = parser.parse_args()
    if bool(args.migration) != bool(args.stage):
        parser.error("--migration and --stage must be supplied together")
    try:
        evidence = {kind: load(getattr(args, kind), kind) for kind in KINDS}
        migration = load(args.migration, "migration") if args.migration else None
        if args.at:
            require(
                all(item.get("synthetic") is True for item in evidence.values()),
                "--at",
                "evaluation-time override is restricted to labelled synthetic evidence",
            )
            if migration is not None:
                labelled = [migration]
                for section in ("records", "approvals"):
                    labelled.extend(object_at(migration.get(section), "migration." + section).values())
                require(
                    all(object_at(item, "migration.synthetic").get("synthetic") is True for item in labelled),
                    "--at",
                    "evaluation-time override requires labelled synthetic migration records and approvals",
                )
        now = timestamp(args.at, "--at") if args.at else datetime.now(UTC)
        verify(evidence, now)
        if migration is not None:
            verify_migration(evidence, migration, args.stage, now)
    except EvidenceError as exc:
        print("ERROR: " + str(exc), file=sys.stderr)
        return 1
    report = {
        "status": "pass",
        "scope": "local supplied-evidence comparison only",
        "target_readiness": "not established",
    }
    if migration is not None:
        report.update(migration_stage=args.stage, operational_authority="not granted")
    print(json.dumps(report))
    return 0


if __name__ == "__main__":
    sys.exit(main())
