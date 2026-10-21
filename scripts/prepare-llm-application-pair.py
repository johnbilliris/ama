"""Prepare privacy-safe, application-only JSON Merge PATCH evidence; never deploy."""

from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import re
import shutil
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "ama_pair_preflight", ROOT / "scripts" / "verify-llm-deployment-preflight.py"
)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("Cannot load deployment preflight helpers")
preflight = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = preflight
SPEC.loader.exec_module(preflight)

SUBSCRIPTION = "74a25c57-d6e4-446e-8c99-7f5ace60011b"
RESOURCE_GROUP = f"/subscriptions/{SUBSCRIPTION}/resourceGroups/ama"
APP_IDS = {
    "api": f"{RESOURCE_GROUP}/providers/Microsoft.App/containerApps/ca-api-dev",
    "agents": f"{RESOURCE_GROUP}/providers/Microsoft.App/containerApps/ca-agents-dev",
}
ACR_ID = f"{RESOURCE_GROUP}/providers/Microsoft.ContainerRegistry/registries/crdevw3uq6w"
API_VERSION = "2025-07-01"
ROUTING_NAMES = frozenset(
    ["AZURE_AI_PROJECT_DEPLOYMENTS", "AZURE_AI_PROJECT_REGION"]
    + [
        f"AZURE_AI_{tier}_{field}"
        for tier in ("REASONING", "DRAFTING", "SIMULATION")
        for field in ("DEPLOYMENT", "MODEL_ID", "MODEL_VERSION", "MODEL_KEY")
    ]
)
CONTAINER_FIELDS = frozenset({"name", "image", "command", "args", "env", "resources", "volumeMounts", "probes"})


def named(items: Any, location: str) -> dict[str, dict[str, Any]]:
    preflight.require(isinstance(items, list), location, "expected an explicit array")
    result: dict[str, dict[str, Any]] = {}
    for index, value in enumerate(items):
        entry = preflight.object_at(value, f"{location}[{index}]")
        name = preflight.text(entry.get("name"), f"{location}[{index}].name")
        preflight.require(name not in result, location, "duplicate name; cannot preserve ambiguously")
        result[name] = entry
    return result


def routing_from_inventory(inventory: dict[str, Any]) -> dict[str, str]:
    target = preflight.object_at(inventory.get("target"), "inventory.target")
    region = preflight.text(target.get("region"), "inventory.target.region")
    preflight.same(region, "australiaeast", "inventory.target.region")
    deployments = named(inventory["deployments"]["value"], "deployments")
    aliases = {"reasoning": "gpt-5.4-dev", "drafting": "gpt-5.4-mini-dev", "simulation": "gpt-5.4-sim-dev"}
    result: dict[str, str] = {"AZURE_AI_PROJECT_REGION": region}
    for tier, alias in aliases.items():
        preflight.require(alias in deployments, tier, "approved existing deployment is missing")
        model = deployments[alias]["properties"]["model"]
        for field, value in {
            "DEPLOYMENT": alias,
            "MODEL_ID": model["name"],
            "MODEL_VERSION": model["version"],
            "MODEL_KEY": f"{model['name']}@{model['version']}",
        }.items():
            result[f"AZURE_AI_{tier.upper()}_{field}"] = preflight.text(value, f"{tier}.{field}")
    embedding = deployments.get("text-embedding-3-large-dev")
    preflight.require(embedding is not None, "embedding", "approved existing embedding deployment is missing")
    model = embedding["properties"]["model"]
    coordinates = [f"{tier}={alias}" for tier, alias in aliases.items()]
    coordinates.extend(
        [
            f"{model['name']}=text-embedding-3-large-dev",
            f"{model['name']}@{model['version']}=text-embedding-3-large-dev",
        ]
    )
    result["AZURE_AI_PROJECT_DEPLOYMENTS"] = ",".join(coordinates)
    return result


def validate_authority(authority: dict[str, Any], now: datetime) -> None:
    for name, expected in {
        "subscription": SUBSCRIPTION,
        "resource_group": "ama",
        "account": "cog-dev-w3uq6w",
        "region": "australiaeast",
    }.items():
        preflight.same(authority.get(name), expected, f"authority.{name}")
    start = preflight.timestamp(authority.get("window_start"), "authority.window_start")
    end = preflight.timestamp(authority.get("window_end"), "authority.window_end")
    preflight.require(start <= now < end, "authority", "outside the approved observation window")
    operation = "refresh target and protection metadata, effective policy semantics and existing app revisions"
    preflight.require(operation in authority.get("allowed", []), "authority", "metadata read is not authorised")


def read_resource(resource_id: str, authority: dict[str, Any], *, api_version: str = API_VERSION) -> dict[str, Any]:
    validate_authority(authority, datetime.now(UTC))
    preflight.require(resource_id in {*APP_IDS.values(), ACR_ID}, "resource_id", "outside the bounded app/ACR read set")
    cli = shutil.which("az")
    preflight.require(cli is not None, "metadata", "Azure CLI executable is unavailable")
    response = subprocess.run(
        [
            cli,
            "rest",
            "--method",
            "get",
            "--subscription",
            SUBSCRIPTION,
            "--url",
            f"https://management.azure.com{resource_id}?api-version={api_version}",
            "-o",
            "json",
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=90,
    )
    preflight.require(response.returncode == 0, "metadata", "Azure metadata GET failed; no response values logged")
    try:
        return preflight.object_at(
            json.loads(
                response.stdout,
                object_pairs_hook=preflight.unique_object,
                parse_constant=preflight.reject_constant,
                parse_float=preflight.finite_float,
            ),
            "metadata",
        )
    except (ValueError, RecursionError) as exc:
        raise preflight.EvidenceError("metadata: invalid Azure JSON response; no values logged") from exc


def pinned_traffic(app: dict[str, Any]) -> list[dict[str, Any]]:
    properties = app["properties"]
    traffic = properties["configuration"]["ingress"].get("traffic")
    preflight.require(isinstance(traffic, list) and bool(traffic), "traffic", "explicit existing allocation required")
    result = copy.deepcopy(traffic)
    for item in result:
        preflight.require(
            set(item) <= {"revisionName", "latestRevision", "weight", "label"},
            "traffic",
            "unknown allocation field requires review",
        )
        if item.get("latestRevision") is True:
            preflight.require(not item.get("revisionName"), "traffic", "ambiguous latest/named allocation")
            item["revisionName"] = preflight.text(properties.get("latestRevisionName"), "latestRevisionName")
        item.pop("latestRevision", None)
        preflight.text(item.get("revisionName"), "traffic.revisionName")
        preflight.require(type(item.get("weight")) is int and 0 <= item["weight"] <= 100, "traffic", "invalid weight")
    preflight.require(sum(item["weight"] for item in result) == 100, "traffic", "allocation must total 100")
    preflight.require(
        len({item["revisionName"] for item in result}) == len(result), "traffic", "duplicate revision allocation"
    )
    return result


def prepare_patch(
    app: dict[str, Any],
    role: str,
    image: str,
    routing: dict[str, str],
    revision_suffix: str,
    login_server: str,
    *,
    configure_registry_identity: bool = False,
    bootstrap_hold: bool = True,
    agents_revision_url: str | None = None,
) -> dict[str, Any]:
    preflight.require(role in APP_IDS, "role", "unknown application")
    preflight.same(app.get("id", "").lower(), APP_IDS[role].lower(), "application.id")
    preflight.require(
        isinstance(app.get("location"), str) and app["location"].casefold() in {"australiaeast", "australia east"},
        "application.location",
        "the existing Australia East location is required",
    )
    preflight.require(
        re.fullmatch(re.escape(f"{login_server}/ama/{role}@sha256:") + r"[0-9a-f]{64}", image) is not None,
        "image",
        "a verified digest-pinned image in the exact Dev ACR repository is required",
    )
    preflight.require(
        re.fullmatch(r"[a-z][a-z0-9-]{0,47}", revision_suffix) is not None
        and not revision_suffix.endswith("-")
        and "--" not in revision_suffix,
        "revision_suffix",
        "invalid explicit revision suffix",
    )
    preflight.require(set(routing) == ROUTING_NAMES, "routing.keys", "expected the complete explicit routing map")
    preflight.require(
        all(isinstance(value, str) and value.strip() for value in routing.values()),
        "routing",
        "blank/non-string selection",
    )
    preflight.require(
        not app["properties"]["template"].get("initContainers"),
        "initContainers",
        "held startup cannot contain unreviewed init-container activity",
    )
    source = app["properties"]["template"]["containers"]
    containers = copy.deepcopy(source)
    by_name = named(containers, "containers")
    preflight.require(len(by_name) == 1, "containers", "primary container selection requires review for sidecars")
    container = next(iter(by_name.values()))
    preflight.require(
        set(container) <= CONTAINER_FIELDS, "containers", "unknown writable/response field requires review"
    )
    preflight.require(
        not container.get("command") and not container.get("args"),
        "containers",
        "runtime command override requires separate review",
    )
    resources = container.get("resources", {})
    preflight.require(set(resources) <= {"cpu", "memory", "ephemeralStorage"}, "resources", "unknown resource field")
    resources.pop("ephemeralStorage", None)
    env = named(container.get("env", []), "environment")
    binding = validation_binding(app, role, revision_suffix, bootstrap_hold, agents_revision_url)
    changes = {**routing, **binding, "AMA_BOOTSTRAP_HOLD": str(bootstrap_hold).lower()}
    if role == "agents":
        changes["AMA_AGENTS_RUNTIME"] = "dispatcher"
    for name, value in changes.items():
        preflight.require(name not in env or "secretRef" not in env[name], "environment", "cannot replace a secretRef")
        if name in env:
            env[name].clear()
            env[name].update({"name": name, "value": value})
        else:
            container.setdefault("env", []).append({"name": name, "value": value})
    container["image"] = image
    prefix = "/api/health" if role == "api" else "/health"
    port = 8000 if role == "api" else 8080
    preflight.same(app["properties"]["configuration"]["ingress"]["targetPort"], port, "preserved.ingress.targetPort")
    container["probes"] = [
        {
            "type": kind,
            "httpGet": {"path": f"{prefix}/{path}", "port": port, "scheme": "HTTP"},
            "periodSeconds": 5,
            "initialDelaySeconds": 1,
            "successThreshold": 1,
            "timeoutSeconds": 2,
            "failureThreshold": threshold,
        }
        for kind, path, threshold in [
            ("Startup", "startup", 30),
            ("Liveness", "liveness", 3),
            ("Readiness", "readiness", 3),
        ]
    ]
    registry_changes = registry_configuration(app, login_server, configure_registry_identity)
    return {
        "location": app["location"],
        "properties": {
            "configuration": {
                "activeRevisionsMode": "Multiple",
                "ingress": {"traffic": pinned_traffic(app)},
                **registry_changes,
            },
            "template": {"revisionSuffix": revision_suffix, "containers": containers},
        },
    }


def validation_binding(
    app: dict[str, Any], role: str, revision_suffix: str, bootstrap_hold: bool, agents_revision_url: str | None
) -> dict[str, str]:
    preflight.require(type(bootstrap_hold) is bool, "bootstrap_hold", "an explicit boolean is required")
    if bootstrap_hold or role == "agents":
        preflight.require(agents_revision_url is None, "pair_binding", "unexpected agents binding")
        return {}
    preflight.same(role, "api", "pair_binding.role")
    properties = app["properties"]
    fqdn = preflight.text(properties.get("latestRevisionFqdn"), "pair_binding.source_fqdn")
    revision, _, domain = fqdn.partition(".")
    preflight.same(revision, properties.get("latestRevisionName"), "pair_binding.source_revision")
    preflight.require(
        domain.endswith(".australiaeast.azurecontainerapps.io") and not domain.startswith("internal."),
        "pair_binding.environment",
        "the existing external Australia East API environment is required",
    )
    expected = f"https://ca-agents-dev--{revision_suffix}.internal.{domain}"
    preflight.same(agents_revision_url, expected, "pair_binding.exact_agents_revision")
    return {"AGENTS_BASE_URL": expected}


def registry_configuration(app: dict[str, Any], login_server: str, approved: bool) -> dict[str, Any]:
    registries = app["properties"]["configuration"].get("registries") or []
    preflight.require(isinstance(registries, list), "registries", "expected registry array")
    matching = [item for item in registries if item.get("server") == login_server]
    preflight.require(len(matching) <= 1, "registries", "duplicate server configuration")
    if matching and matching[0].get("identity") == "system":
        return {}
    preflight.require(approved, "registries", "system-identity registry configuration requires explicit approval")
    preflight.require(
        "SystemAssigned" in {part.strip() for part in app.get("identity", {}).get("type", "").split(",")},
        "identity",
        "existing system-assigned identity required; identity creation is not authorised",
    )
    configured = copy.deepcopy(registries)
    replacement = {"server": login_server, "identity": "system"}
    if matching:
        preflight.require(
            set(matching[0]) <= {"server", "identity", "username", "passwordSecretRef"},
            "registries",
            "unknown target registry field requires review",
        )
        configured[registries.index(matching[0])] = replacement
    else:
        configured.append(replacement)
    return {"registries": configured}


def merge_patch(before: Any, patch: Any) -> Any:
    if not isinstance(patch, dict):
        return copy.deepcopy(patch)
    result = copy.deepcopy(before) if isinstance(before, dict) else {}
    for key, value in patch.items():
        if value is None:
            result.pop(key, None)
        else:
            result[key] = merge_patch(result.get(key), value)
    return result


def proposal_evidence(
    app: dict[str, Any],
    patch: dict[str, Any],
    role: str,
    *,
    configure_registry_identity: bool = False,
    login_server: str = "crdevw3uq6w.azurecr.io",
    bootstrap_hold: bool = True,
    agents_revision_url: str | None = None,
) -> dict[str, Any]:
    configuration = patch["properties"]["configuration"]
    registry_changes = registry_configuration(app, login_server, configure_registry_identity)
    preflight.require(set(patch) == {"location", "properties"}, "patch.keys", "unexpected envelope field")
    preflight.require(set(patch["properties"]) == {"configuration", "template"}, "patch.properties", "unexpected field")
    preflight.require(
        set(configuration) == {"activeRevisionsMode", "ingress"} | registry_changes.keys(),
        "patch.configuration",
        "unexpected field",
    )
    if registry_changes:
        preflight.same(configuration["registries"], registry_changes["registries"], "patch.registries")
    preflight.require(set(configuration["ingress"]) == {"traffic"}, "patch.ingress", "unexpected field")
    preflight.require(
        set(patch["properties"]["template"]) == {"revisionSuffix", "containers"}, "patch.template", "unexpected field"
    )
    preflight.same(patch["location"], app["location"], "preserved.location")
    preflight.same(configuration["activeRevisionsMode"], "Multiple", "patch.revision_mode")
    preflight.same(configuration["ingress"]["traffic"], pinned_traffic(app), "preserved.traffic")
    previous = named(app["properties"]["template"]["containers"], "source.containers")
    proposed = named(patch["properties"]["template"]["containers"], "patch.containers")
    preflight.require(previous.keys() == proposed.keys(), "containers", "container set changed")
    binding = validation_binding(
        app, role, patch["properties"]["template"]["revisionSuffix"], bootstrap_hold, agents_revision_url
    )
    allowed_env = ROUTING_NAMES | {"AMA_BOOTSTRAP_HOLD"} | binding.keys()
    if role == "agents":
        allowed_env |= {"AMA_AGENTS_RUNTIME"}
    for name, before in previous.items():
        after = proposed[name]
        preflight.require(set(after) <= CONTAINER_FIELDS, "container", "unknown field")
        for field in set(before) | set(after):
            if field not in {"image", "env", "probes", "resources"}:
                preflight.same(after.get(field), before.get(field), f"preserved.container.{field}")
        resources = {key: value for key, value in before.get("resources", {}).items() if key != "ephemeralStorage"}
        preflight.same(after.get("resources", {}), resources, "preserved.container.resources")
        old_env, new_env = named(before.get("env", []), "source.env"), named(after.get("env", []), "patch.env")
        for key in (old_env.keys() | new_env.keys()) - allowed_env:
            preflight.same(new_env.get(key), old_env.get(key), f"preserved.env.{key}")
        preflight.same(
            new_env.get("AMA_BOOTSTRAP_HOLD"),
            {"name": "AMA_BOOTSTRAP_HOLD", "value": str(bootstrap_hold).lower()},
            "patch.hold",
        )
        for key, value in binding.items():
            preflight.same(new_env.get(key), {"name": key, "value": value}, f"patch.binding.{key}")
        if role == "agents":
            preflight.same(
                new_env.get("AMA_AGENTS_RUNTIME"),
                {"name": "AMA_AGENTS_RUNTIME", "value": "dispatcher"},
                "patch.runtime",
            )
    expected = merge_patch(app, patch)
    for field in ("identity", "tags"):
        preflight.same(expected.get(field), app.get(field), f"preserved.{field}")
    for field in ("secrets", "dapr", "runtime", "identitySettings"):
        preflight.same(
            expected["properties"]["configuration"].get(field),
            app["properties"]["configuration"].get(field),
            f"preserved.configuration.{field}",
        )
    for field in ("scale", "volumes", "initContainers", "serviceBinds", "terminationGracePeriodSeconds"):
        preflight.same(
            expected["properties"]["template"].get(field),
            app["properties"]["template"].get(field),
            f"preserved.template.{field}",
        )
    return {
        "app": role,
        "resource_id": APP_IDS[role],
        "method": "PATCH",
        "content_type": "application/json",
        "api_version": API_VERSION,
        "source_sha256": preflight.canonical_digest(app),
        "patch_sha256": preflight.canonical_digest(patch),
        "expected_sha256": preflight.canonical_digest(expected),
        "secret_definitions_submitted": False,
        "business_hold": bootstrap_hold,
        **({"agents_revision_url": agents_revision_url} if binding else {}),
        "candidate_traffic_weight": 0,
        "arm_what_if_equivalence_claimed": False,
        "execution_authorised": False,
    }


def normalized_application(app: dict[str, Any]) -> dict[str, Any]:
    result = {
        key: copy.deepcopy(app.get(key))
        for key in ("id", "name", "type", "location", "identity", "tags", "kind", "managedBy", "extendedLocation")
    }
    properties = copy.deepcopy(app["properties"])
    for key in (
        "provisioningState",
        "runningStatus",
        "latestRevisionName",
        "latestReadyRevisionName",
        "latestRevisionFqdn",
        "customDomainVerificationId",
        "outboundIpAddresses",
        "eventStreamEndpoint",
    ):
        properties.pop(key, None)
    properties["configuration"]["ingress"]["traffic"] = pinned_traffic(app)
    for registry in properties["configuration"].get("registries", []):
        if registry.get("identity") == "system":
            for field in ("username", "passwordSecretRef"):
                if registry.get(field) in ("", None):
                    registry.pop(field, None)
    probe_order = {"Startup": 0, "Liveness": 1, "Readiness": 2}
    for container in properties["template"]["containers"]:
        container.get("resources", {}).pop("ephemeralStorage", None)
        if container.get("probes") is not None:
            kinds = [probe.get("type") for probe in container["probes"]]
            preflight.require(
                all(kind in probe_order for kind in kinds) and len(kinds) == len(set(kinds)),
                "probes",
                "unknown or duplicate probe type",
            )
            container["probes"].sort(key=lambda probe: probe_order[probe["type"]])
    result["properties"] = properties
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--authority", type=Path, required=True)
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--api-image")
    parser.add_argument("--agents-image")
    parser.add_argument("--revision-suffix")
    parser.add_argument("--configure-registry-identity", action="store_true")
    args = parser.parse_args()
    try:
        authority = preflight.load(args.authority, "authority")
        inventory = preflight.load(args.inventory, "inventory")
        now = datetime.now(UTC)
        validate_authority(authority, now)
        observed = preflight.timestamp(inventory.get("observed_at"), "inventory.observed_at")
        preflight.require(0 <= (now - observed).total_seconds() <= 3600, "inventory", "stale preservation evidence")
        apps = {role: read_resource(resource_id, authority) for role, resource_id in APP_IDS.items()}
        acr = read_resource(ACR_ID, authority, api_version="2023-07-01")
        login_server = preflight.text(acr["properties"].get("loginServer"), "registry.loginServer")
        summary: dict[str, Any] = {
            "observed_at": now.isoformat(),
            "authority_reference": str(args.authority),
            "target_subscription": SUBSCRIPTION,
            "login_server": login_server,
            "scope": "application-only preparation; zero Foundry writes",
            "secrets_persisted": False,
            "deployment_performed": False,
            "release_ready": False,
            "applications": {},
        }
        for role, app in apps.items():
            entries = named(app["properties"]["template"]["containers"], f"{role}.containers")
            summary["applications"][role] = {
                "source_sha256": preflight.canonical_digest(app),
                "revision_mode": app["properties"]["configuration"].get("activeRevisionsMode"),
                "revision": app["properties"].get("latestRevisionName"),
                "identity_type": app.get("identity", {}).get("type"),
                "container_names": list(entries),
                "environment_names": sorted({item["name"] for c in entries.values() for item in c.get("env", [])}),
                "registry_identity_configured": any(
                    item.get("server") == login_server and item.get("identity")
                    for item in app["properties"]["configuration"].get("registries", [])
                ),
            }
        if any((args.api_image, args.agents_image, args.revision_suffix)):
            preflight.require(
                all((args.api_image, args.agents_image, args.revision_suffix)),
                "images",
                "both digest-pinned images and an explicit revision suffix required",
            )
            routing = routing_from_inventory(inventory)
            summary["proposals"] = [
                proposal_evidence(
                    apps[role],
                    prepare_patch(
                        apps[role],
                        role,
                        image,
                        routing,
                        args.revision_suffix,
                        login_server,
                        configure_registry_identity=args.configure_registry_identity,
                    ),
                    role,
                    configure_registry_identity=args.configure_registry_identity,
                    login_server=login_server,
                )
                for role, image in (("api", args.api_image), ("agents", args.agents_image))
            ]
        args.output.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
        print("PASS bounded application inspection/preparation; no PATCH, secret operation or deployment performed")
        return 0
    except preflight.EvidenceError as exc:
        print(f"ERROR application-pair preparation blocked: {exc}", file=sys.stderr)
        return 2
    except (KeyError, TypeError, OSError, subprocess.TimeoutExpired) as exc:
        print(f"ERROR application-pair preparation blocked ({type(exc).__name__}); no values logged", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
