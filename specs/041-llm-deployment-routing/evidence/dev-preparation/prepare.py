"""Bind actual local compiler outputs and image IDs; never publish or activate."""

from __future__ import annotations

import datetime
import hashlib
import importlib.util
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
spec = importlib.util.spec_from_file_location(
    "compiled_contract", ROOT / "tests" / "contract" / "test_llm_deployment_compiled.py"
)
contract = importlib.util.module_from_spec(spec)
spec.loader.exec_module(contract)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def image(name):
    return json.loads(subprocess.check_output(
        ["docker", "image", "inspect", name], text=True, stderr=subprocess.PIPE,
    ))[0]


refresh = json.loads((HERE / "refresh.json").read_text())
observed = datetime.datetime.fromisoformat(refresh["observed_at"])
if not 0 <= (datetime.datetime.now(datetime.UTC) - observed).total_seconds() <= 3600:
    raise RuntimeError("Fresh authorized metadata is required before use")
protection = json.loads((HERE / "protection-comparison.json").read_text())
if protection["refresh_observed_at"] != refresh["observed_at"]:
    raise RuntimeError("Protection comparisons must be rerun against this exact refreshed observation")
policy = json.loads((HERE / "policy-definition-refresh.json").read_text())
if any(not 0 <= (datetime.datetime.now(datetime.UTC) - datetime.datetime.fromisoformat(
        item["observed_at"])).total_seconds() <= 3600 for item in policy["observations"]):
    raise RuntimeError("Policy definition observations require an authorized refresh")
source = json.loads((HERE / "app-source-bindings.json").read_text())
if not all(hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == value
           for name, value in source["files"].items()):
    raise RuntimeError("Application source binding changed; reconciliation/reapproval required")
if image("python:3.12-slim")["RepoDigests"] != source["base_image"]:
    raise RuntimeError("Base image binding changed; reconciliation/reapproval required")
compiled = contract.compile_bicep("build-params", HERE / "deployments.bicepparam")
template = json.loads(compiled["templateJson"])
parameters = {key: value["value"] for key, value in json.loads(compiled["parametersJson"])["parameters"].items()}
outputs = contract.wrapper_outputs(template, parameters)
environment = {
    "AZURE_AI_PROJECT_ENDPOINT": refresh["target"]["endpoint"],
    "AZURE_AI_PROJECT_REGION": refresh["target"]["region"],
    "AZURE_AI_PROJECT_DEPLOYMENTS": outputs["azureAiProjectDeployments"],
    "EMBEDDING_DEPLOYMENT_NAME": outputs["embeddingDeploymentName"],
}
for tier in contract.TIERS:
    for suffix, value in (
        ("DEPLOYMENT", parameters[tier + "DeploymentName"]),
        ("MODEL_ID", parameters[tier + "ModelName"]),
        ("MODEL_VERSION", parameters[tier + "ModelVersion"]),
        ("MODEL_KEY", outputs[tier + "DeploymentModelKey"]),
    ):
        environment[f"AZURE_AI_{tier.upper()}_{suffix}"] = value
services = {}
for service in ("api", "agents"):
    live = refresh["services"][f"ca-{service}-dev"]
    services[service] = {
        "image": None,
        "image_kind": "immutable local Docker image ID; NOT a verified ACR manifest digest",
        "registry_manifest_digest": None,
        "llm_environment": environment,
        "observed_revision": live["latestRevisionName"],
        "preserve_other_environment_and_secret_refs": True,
        "preserved_nonsecret_environment_and_secret_refs": live["revisions"][0]["containers"][0]["env"],
        "withheld_preserved_environment_names": ["APPLICATIONINSIGHTS_CONNECTION_STRING"],
        "complete_secret_bearing_configuration_digest": None,
        "rollback_pair_healthy": False,
    }
    try:
        built = image(f"ama041-{service}:preparation")
    except subprocess.CalledProcessError:
        services[service]["build_status"] = "image not locally available; see actual build/retry logs"
        continue
    services[service].update({
        "image": built["Id"],
        "os": built["Os"],
        "architecture": built["Architecture"],
        "created": built["Created"],
        "build_status": "local build succeeded",
    })
    module_path = "/app/apps/agents/common/llm_config.py" if service == "api" else "/app/common/llm_config.py"
    module = "apps.agents.common.llm_config" if service == "api" else "common.llm_config"
    code = (
        f"import hashlib,json,pathlib; from {module} import DeploymentResolver; "
        f"assert hashlib.sha256(pathlib.Path({module_path!r}).read_bytes()).hexdigest() == "
        f"{source['files'][str(pathlib.Path('apps/agents/common/llm_config.py'))]!r}; "
        f"r=DeploymentResolver.from_environment({environment!r},configuration_revision='local-041-candidate'); "
        "print(json.dumps({t:r.resolve(t).deployment_name for t in ('reasoning','drafting','simulation')}))"
    )
    smoke = subprocess.run(
        ["docker", "run", "--rm", "--platform", "linux/amd64", "--network", "none",
         "--entrypoint", "python", built["Id"], "-c", code],
        capture_output=True, text=True, check=True, timeout=90,
    )
    services[service]["network_isolated_resolver_smoke"] = json.loads(smoke.stdout)
bound = {
    "observed_at": refresh["observed_at"],
    "prepared_at": datetime.datetime.now(datetime.UTC).isoformat(),
    "scope": refresh["target"],
    "approval_reference": refresh["approval_reference"],
    "freshness_policy": {"max_observation_age_seconds": 3600, "refresh_before_what_if_and_activation": True,
                         "changed_bindings_require_reconciliation_and_reapproval": True},
    "gates": {"G1": "accepted for preservation authoring only; unhealthy app release unresolved",
              "G2": "complete discovery, exact 11 refreshed assignment names/enforcement retained",
              "G3": "pinned unchanged child compatible; local build and contract PASS",
              "G4": "NOT APPROVED; What-If/activation NOT PERFORMED"},
    "source_digest": source["digest"],
    "services": services,
    "llm_environment_digest": digest(environment),
    "complete_secret_bearing_configuration_digest": None,
    "pair_binding_digest": digest(services) if all(item["image"] for item in services.values()) else None,
    "paired_application_candidate_complete": all(item["image"] for item in services.values()),
    "candidate_binding_acceptance": "not approved for release; parent review/reapproval required before use",
    "what_if_performed": False,
    "cloud_writes_performed": False,
    "release_ready": False,
    "compiled_inventory": {
        "bounded_top_level": [{"type": item["type"], "name": item["name"]} for item in contract.resources(template)],
        "bounded_model_identities": [parameters[tier + "DeploymentName"] for tier in contract.TIERS]
        + [outputs["embeddingDeploymentName"]],
        "parent_account_writes": 0,
        "role_assignment_count": 0,
        "rai_writes": 3,
        "diagnostic_writes": ["openai-diagnostics (pre-existing definition retained)"],
        "model_resource_changes": "none in evaluated model/version/SKU/capacity/RAI/upgrade bindings; NOT live What-If",
    },
    "artifact_hashes": {},
}
for relative in (
    ".gitattributes",
    "infra/main.bicep", "infra/main.json", "infra/modules/azure-openai.bicep", "infra/modules/azure-openai.json",
    "infra/parameters/dev.bicepparam", "infra/main.parameters.dev.json",
    "infra/modules/vendor/avm-cognitive-services-deployment-0.18.0/main.bicep",
):
    bound["artifact_hashes"][relative] = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
for name in (
    "deployments.bicepparam", "deployments.parameters.json", "deployments.template.json",
    "main-dev.parameters.json", "refresh.json", "protection-comparison.json",
    "policy-definition-refresh.json",
):
    bound["artifact_hashes"][str((HERE / name).relative_to(ROOT))] = hashlib.sha256(
        (HERE / name).read_bytes()
    ).hexdigest()
(HERE / "candidate-bindings.json").write_text(json.dumps(bound, indent=2) + "\n")
print("Paired immutable LOCAL candidates complete:", bound["paired_application_candidate_complete"])
print("Available images passed network-isolated resolver smoke; no publication/activation")
if not bound["paired_application_candidate_complete"]:
    raise SystemExit(2)
