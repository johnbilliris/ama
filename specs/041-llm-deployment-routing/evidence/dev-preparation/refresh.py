"""Bounded G0 metadata capture; expires with this run's explicit read approval."""

import argparse
import datetime
import importlib.util
import json
import pathlib
import subprocess

SUB = "74a25c57-d6e4-446e-8c99-7f5ace60011b"
ROOT = f"/subscriptions/{SUB}/resourceGroups/ama"
ACCOUNT = ROOT + "/providers/Microsoft.CognitiveServices/accounts/cog-dev-w3uq6w"
HERE = pathlib.Path(__file__).resolve().parent
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--output", type=pathlib.Path, default=pathlib.Path(__file__).with_name("validation-refresh.json"))
parser.add_argument("--approval-reference", default="validation-approval.json")
parser.add_argument("--held-bootstrap", action="store_true")
parser.add_argument(
    "--application-state-reference", choices=["unheld-staging-v2.json", "dependency-staging.json"]
)
args = parser.parse_args()
authority = json.loads((HERE / args.approval_reference).read_text())
if (
    authority["subscription"] != SUB
    or authority["resource_group"] != "ama"
    or authority["account"] != "cog-dev-w3uq6w"
    or authority["region"] != "australiaeast"
    or "refresh target and protection metadata, effective policy semantics and existing app revisions"
    not in authority["allowed"]
):
    raise ValueError("Approval does not authorise this exact Dev metadata scope")
START = datetime.datetime.fromisoformat(authority["window_start"])
END = datetime.datetime.fromisoformat(authority["window_end"])


def get(path):
    if not START <= datetime.datetime.now(datetime.UTC) < END:
        raise RuntimeError("Outside this run's approved G0 read window")
    command = (
        f'az rest --method get --subscription {SUB} '
        f'--url "https://management.azure.com{path}" -o json'
    )
    result = subprocess.run(command, shell=True, capture_output=True, text=True, check=True)
    return json.loads(result.stdout)


observed = datetime.datetime.now(datetime.UTC).isoformat()
account = get(ACCOUNT + "?api-version=2026-05-01")
deployments = get(ACCOUNT + "/deployments?api-version=2026-05-01")
rai = get(ACCOUNT + "/raiPolicies?api-version=2024-10-01")
diagnostics = get(ACCOUNT + "/providers/Microsoft.Insights/diagnosticSettings?api-version=2021-05-01-preview")
policy = get(ROOT + "/providers/Microsoft.Authorization/policyAssignments?api-version=2025-03-01&$filter=atScope()")
rbac = get(ACCOUNT + "/providers/Microsoft.Authorization/roleAssignments?api-version=2022-04-01&$filter=atScope()")
services = {}
app_resources = {}
for name in ("ca-api-dev", "ca-agents-dev"):
    app = get(ROOT + f"/providers/Microsoft.App/containerApps/{name}?api-version=2025-07-01")
    app_resources[name] = app
    revisions = get(ROOT + f"/providers/Microsoft.App/containerApps/{name}/revisions?api-version=2025-07-01")
    properties = app["properties"]
    services[name] = {
        "identity": app.get("identity"),
        "latestRevisionName": properties.get("latestRevisionName"),
        "configuration": {key: value for key, value in properties["configuration"].items() if key != "secrets"},
        "revisions": [],
    }
    for revision in revisions["value"]:
        properties = revision["properties"]
        containers = []
        for container in properties["template"]["containers"]:
            containers.append({
                "name": container["name"],
                "image": container["image"],
                "env": [
                    entry if "secretRef" in entry else {"name": entry["name"], "literal_value_withheld": True}
                    for entry in container.get("env", [])
                ],
            })
        services[name]["revisions"].append({
            "name": revision["name"],
            "healthState": properties.get("healthState"),
            "runningState": properties.get("runningState"),
            "active": properties.get("active"),
            "containers": containers,
        })

base = json.loads(pathlib.Path("specs/041-llm-deployment-routing/deployment-baseline.json").read_text())
assert account["name"] == base["target"]["account_name"] and account["kind"] == "AIServices"
assert account["sku"]["name"] == "S0" and account["location"] == "australiaeast"
assert account["properties"]["disableLocalAuth"] is True
assert account["properties"]["publicNetworkAccess"] == "Enabled"
assert account["identity"]["principalId"] == base["account_controls"]["managed_identity"]["principal_id"]
assert len(deployments["value"]) == 4 and len(policy["value"]) == 11
for old in base["deployments"]:
    live = next(item for item in deployments["value"] if item["name"] == old["deployment_name"])
    for key in ("name", "version", "format"):
        assert live["properties"]["model"][key] == old["model"][key]
    assert live["sku"]["name"] == old["sku"] and live["sku"]["capacity"] == old["capacity"]
    assert live["properties"]["raiPolicyName"] == old["rai_policy_name"]
    assert live["properties"]["versionUpgradeOption"] == old["version_upgrade_option"]
for name in base["rai"]["custom_policy_names"]:
    properties = next(item["properties"] for item in rai["value"] if item["name"] == name)
    assert properties["basePolicyName"] == "Microsoft.DefaultV2" and properties["mode"] == "Blocking"
    assert properties["contentFilters"] == base["rai"]["identical_overrides_per_custom_policy"]
default_policy = next(item["properties"] for item in rai["value"] if item["name"] == "Microsoft.DefaultV2")
assert default_policy["mode"] == base["rai"]["mode"]
assert default_policy["contentFilters"] == base["rai"]["base_filters"]
held = None
pair = None
if args.held_bootstrap and args.application_state_reference:
    raise ValueError("Select only one exact application source state")
if args.held_bootstrap:
    held = json.loads((HERE / "held-bootstrap-staging.json").read_text())
    assert held["operation"] == "041-dev-application-only-held-bootstrap"
    assert held["complete"] is True and held["business_hold"] is True
    module = importlib.util.spec_from_file_location(
        "refresh_held_pair", HERE.parents[3] / "scripts" / "prepare-llm-application-pair.py"
    )
    assert module is not None and module.loader is not None
    pair = importlib.util.module_from_spec(module)
    module.loader.exec_module(pair)
elif args.application_state_reference:
    held = json.loads((HERE / args.application_state_reference).read_text())
    assert held["operation"] == (
        "041-dev-dependency-remediation"
        if args.application_state_reference == "dependency-staging.json"
        else "041-dev-unheld-zero-traffic-validation"
    )
    assert held["complete"] is True and held["business_promotion"] is False
    module = importlib.util.spec_from_file_location(
        "refresh_unheld_pair", HERE.parents[3] / "scripts" / "prepare-llm-application-pair.py"
    )
    assert module is not None and module.loader is not None
    pair = importlib.util.module_from_spec(module)
    module.loader.exec_module(pair)
for role, old in base["services"].items():
    live = services[old["app_name"]]
    old_revision = next(item for item in live["revisions"] if item["name"] == old["active_revision"])
    assert old_revision["containers"][0]["image"] == old["image"]
    if held is None:
        assert live["latestRevisionName"] == old["active_revision"]
    else:
        entry = held["applications"][role]
        assert entry["verified"] is True
        assert live["latestRevisionName"] == entry["revision_name"]
        assert pair.preflight.canonical_digest(
            pair.normalized_application(app_resources[old["app_name"]])
        ) == entry["expected_normalized_sha256"]

controls = {key: account["properties"].get(key) for key in (
    "disableLocalAuth", "publicNetworkAccess", "networkAcls", "privateEndpointConnections",
    "encryption", "restrictOutboundNetworkAccess", "endpoint", "customSubDomainName",
)}
assert controls["networkAcls"] is None and controls["privateEndpointConnections"] == []
assert diagnostics["value"][0]["properties"]["workspaceId"].lower() == (
    base["account_controls"]["diagnostics"]["workspace_id"].lower()
)
result = {
    "observed_at": observed,
    "completed_at": datetime.datetime.now(datetime.UTC).isoformat(),
    "approval_reference": args.approval_reference,
    "max_observation_age_seconds": 3600,
    "reapproval_on_changed_bindings": True,
    "literal_environment_values": "withheld; names and secret references only",
    "target": base["target"],
    "comparison": "PASS model/protection and exact reviewed-state invariants" if held else "PASS preservation invariants; no release approval",
    "application_state_reference": args.application_state_reference or (
        "held-bootstrap-staging.json" if held else "deployment-baseline.json"
    ),
    "account_controls": controls,
    "identity": account.get("identity"),
    "tags": account.get("tags"),
    "deployments": deployments,
    "rai": rai,
    "diagnostics": diagnostics,
    "policy_assignments": policy,
    "rbac": rbac,
    "services": services,
    "release_ready": False,
}
args.output.write_text(json.dumps(result, indent=2) + "\n")
print(f"PASS fresh preservation metadata at {observed}; four deployments, eleven policies; exact application state verified")
