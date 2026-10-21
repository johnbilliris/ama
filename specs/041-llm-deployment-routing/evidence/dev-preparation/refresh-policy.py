"""Refresh the assigned sets and target-relevant policy semantics within G0."""

import argparse
import concurrent.futures
import datetime
import json
import pathlib
import subprocess

HERE = pathlib.Path(__file__).resolve().parent
SOURCE = pathlib.Path(
    r"C:\Users\prbillir\.copilot\session-state\6cfd864e-5202-418c-8388-236f4576ce64"
    r"\files\041-governance-live-policy.json"
)
SUB = "74a25c57-d6e4-446e-8c99-7f5ace60011b"
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument(
    "--output", type=pathlib.Path, default=HERE / "validation-policy-definition-refresh.json",
)
parser.add_argument("--approval-reference", default="validation-approval.json")
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
    raise ValueError("Approval does not authorise this exact Dev policy metadata scope")
START = datetime.datetime.fromisoformat(authority["window_start"])
END = datetime.datetime.fromisoformat(authority["window_end"])
original = json.loads(SOURCE.read_text())
constraints = json.loads((HERE.parents[1] / "04-governance-constraints.json").read_text())
definitions = original["definitions"]
names = {item["definitionName"].lower() for item in constraints["constraints"]}
names.update(item["definitionName"].lower() for item in constraints["nonApplicableDenyRules"]
             if "definitionName" in item)
selected = {key: value for key, value in definitions.items()
            if value["name"].lower() in names or value["type"].lower().endswith("/policysetdefinitions")}
deny_set = next(value for value in definitions.values() if value["name"] == "MCAPSGovDenyPolicies")
for member in deny_set["properties"]["policyDefinitions"]:
    key = next(key for key in definitions if key.lower() == member["policyDefinitionId"].lower())
    selected[key] = definitions[key]


def semantic(value):
    result = {key: value["properties"].get(key) for key in (
        "policyRule", "parameters", "policyDefinitions", "policyType", "mode", "version",
    )}
    if result["parameters"]:
        # The original sanitized capture omitted parameter display metadata.
        result["parameters"] = {
            name: {key: item for key, item in definition.items() if key != "metadata"}
            for name, definition in result["parameters"].items()
        }
    return result


def collect(item):
    key, old = item
    if not START <= datetime.datetime.now(datetime.UTC) < END:
        raise RuntimeError("Outside approved G0 read window")
    command = (
        f'az rest --method get --subscription {SUB} '
        f'--url "https://management.azure.com{key}?api-version=2023-04-01" -o json'
    )
    response = subprocess.run(command, shell=True, capture_output=True, text=True, check=True)
    current = json.loads(response.stdout)
    if semantic(current) != semantic(old):
        raise RuntimeError(f"Policy semantics changed; stop for reconciliation/reapproval: {key}")
    return {"id": current["id"], "name": current["name"], "semantics": semantic(current),
            "observed_at": datetime.datetime.now(datetime.UTC).isoformat(), "comparison": "PASS"}


with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
    observations = list(executor.map(collect, selected.items()))
result = {
    "approval_reference": args.approval_reference,
    "scope": "all seven assigned initiatives, all deny-initiative members and target-relevant definitions",
    "not_claimed": "This is not rediscovery of all 329 definitions or live policy compliance state",
    "observations": observations,
    "comparison": "PASS unchanged semantic rules/defaults/initiative bindings; no mutations",
}
args.output.write_text(json.dumps(result, indent=2) + "\n")
print(f"PASS {len(observations)} relevant/initiative definition semantics unchanged")
