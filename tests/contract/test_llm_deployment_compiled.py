"""Actual Bicep compiler contracts; no ARM requests or deployment simulation."""

from __future__ import annotations

import copy
import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

from apps.agents.common.llm_config import FoundryConfigurationError, parse_deployment_map

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / "specs" / "041-llm-deployment-routing" / "evidence" / "dev-preparation"
TIERS = ("reasoning", "drafting", "simulation")


def compile_bicep(command: str, path: Path) -> dict:
    executable = shutil.which("bicep") or str(Path.home() / ".azure" / "bin" / "bicep.exe")
    result = subprocess.run(
        [executable, command, str(path), "--stdout"],
        capture_output=True,
        text=True,
        check=True,
        timeout=120,
        cwd=ROOT,
    )
    return json.loads(result.stdout)


@pytest.mark.parametrize("environment", ["staging", "production"])
def test_non_dev_parameters_require_their_own_explicit_model_profile(monkeypatch, environment):
    variable = f"AMA_{environment.upper()}_MODEL_PARAMETERS"
    path = ROOT / "infra" / "parameters" / f"{environment}.bicepparam"
    monkeypatch.delenv(variable, raising=False)
    with pytest.raises(subprocess.CalledProcessError) as error:
        compile_bicep("build-params", path)
    assert variable in error.value.stderr

    profile = {}
    for tier in TIERS:
        profile[f"{tier}ModelName"] = f"synthetic-{environment}-{tier}"
        profile[f"{tier}ModelVersion"] = f"synthetic-{environment}-version"
        profile[f"{tier}VersionUpgradeOption"] = "NoAutoUpgrade"
    profile["embeddingVersionUpgradeOption"] = "OnceNewDefaultVersionAvailable"
    profile["deploymentOperatingStates"] = {
        tier: {"currentCapacity": index, "deploymentState": "Paused"}
        for index, tier in enumerate((*TIERS, "embedding"), 1)
    }
    monkeypatch.setenv(variable, json.dumps(profile))
    result = compile_bicep("build-params", path)
    compiled = json.loads(result["parametersJson"])["parameters"]
    assert {name: compiled[name]["value"] for name in profile} == profile


class ArmExpressions:
    """Fail-closed evaluator for the pure expressions emitted by this wrapper."""

    def __init__(self, template, parameters, references=None):
        self.template = template
        self.parameters = parameters
        self.references = references or {}

    def value(self, value, scope=None):
        if isinstance(value, list):
            return [self.value(item, scope) for item in value]
        if isinstance(value, dict):
            return {key: self.value(item, scope) for key, item in value.items()}
        if not isinstance(value, str) or not value.startswith("["):
            return value
        tokens = re.findall(r"'(?:[^']|'')*'|[A-Za-z_]\w*|\d+|[(),.]", value[1:-1])
        position = 0

        def parse():
            nonlocal position
            token = tokens[position]
            position += 1
            if token.startswith("'"):
                node = ("literal", token[1:-1].replace("''", "'"))
            elif token.isdigit():
                node = ("literal", int(token))
            else:
                assert tokens[position] == "(", token
                position += 1
                args = []
                while tokens[position] != ")":
                    args.append(parse())
                    if tokens[position] == ",":
                        position += 1
                position += 1
                node = ("call", token, args)
            while position < len(tokens) and tokens[position] == ".":
                position += 1
                node = ("member", node, tokens[position])
                position += 1
            return node

        tree = parse()
        assert position == len(tokens), value

        def evaluate(node, bindings):
            if node[0] == "literal":
                return node[1]
            if node[0] == "member":
                return evaluate(node[1], bindings)[node[2]]
            name, nodes = node[1:]
            if name == "lambda":
                argument = evaluate(nodes[0], bindings)
                return lambda item: evaluate(nodes[1], {**bindings, argument: item})
            args = [evaluate(item, bindings) for item in nodes]
            if name == "parameters":
                key = args[0]
                return self.value(
                    self.parameters[key]
                    if key in self.parameters
                    else self.template["parameters"][key]["defaultValue"],
                    bindings,
                )
            if name == "variables":
                return self.value(self.template["variables"][args[0]], bindings)
            if name == "lambdaVariables":
                return bindings[args[0]]
            if name == "groupBy":
                grouped = {}
                for item in args[0]:
                    grouped.setdefault(args[1](item), []).append(item)
                return grouped
            if name == "union":
                return list(dict.fromkeys(item for array in args for item in array))
            if name == "resourceId":
                return "/".join(args)
            if name == "reference":
                return self.references[args[0]]
            functions = {
                "format": lambda pattern, *values: pattern.format(*values),
                "map": lambda array, function: list(map(function, array)),
                "filter": lambda array, function: list(filter(function, array)),
                "flatten": lambda arrays: [item for array in arrays for item in array],
                "createArray": lambda *values: list(values),
                "createObject": lambda *values: dict(zip(values[::2], values[1::2])),
                "items": lambda obj: [{"key": key, "value": obj[key]} for key in sorted(obj)],
                "length": len,
                "equals": lambda left, right: left == right,
                "contains": lambda collection, value: value in collection,
                "not": lambda value: not value,
                "first": lambda array: array[0],
                "concat": lambda *arrays: [item for array in arrays for item in array],
                "join": lambda array, separator: separator.join(array),
                "tryGet": lambda obj, key: obj.get(key),
                "coalesce": lambda *values: next(value for value in values if value is not None),
                "true": lambda: True,
                "false": lambda: False,
            }
            assert name in functions, f"Unsupported expression: {name}"
            return functions[name](*args)

        return evaluate(tree, scope or {})


@pytest.fixture(scope="module")
def compiled():
    result = compile_bicep("build-params", EVIDENCE / "deployments.bicepparam")
    template = json.loads(result["templateJson"])
    parameters = {key: value["value"] for key, value in json.loads(result["parametersJson"])["parameters"].items()}
    main = compile_bicep("build", ROOT / "infra" / "main.bicep")
    main_parameters = compile_bicep("build-params", ROOT / "infra" / "parameters" / "dev.bicepparam")
    main_parameters = {
        key: value["value"] for key, value in json.loads(main_parameters["parametersJson"])["parameters"].items()
    }
    return template, parameters, main, main_parameters


def modules(template):
    return {
        resource["name"]: resource
        for resource in resources(template)
        if resource["type"] == "Microsoft.Resources/deployments"
    }


def resources(template):
    value = template["resources"]
    return list(value.values()) if isinstance(value, dict) else value


def resource_references(template, resource, evaluator):
    references = {resource["type"] + "/" + evaluator.value(resource["name"])}
    if isinstance(template["resources"], dict):
        references.update(key for key, value in template["resources"].items() if value is resource)
    return references


def test_checked_in_arm_artifacts_match_actual_compiler(compiled):
    template, _, main, _ = compiled
    assert json.loads((ROOT / "infra" / "modules" / "azure-openai.json").read_text()) == template
    assert json.loads((ROOT / "infra" / "main.json").read_text()) == main


def wrapper_outputs(template, parameters):
    evaluator = ArmExpressions(template, parameters)
    for module in modules(template).values():
        reference = {
            "outputs": {"name": {"value": evaluator.value(module["properties"]["parameters"]["name"]["value"])}}
        }
        for key in resource_references(template, module, evaluator):
            evaluator.references[key] = reference
    return {
        name: evaluator.value(output["value"])
        for name, output in template["outputs"].items()
        if name != "openAiEndpoint"
    }


def test_compiled_nine_selections_are_passed_through_and_dev_names_are_explicit(compiled):
    template, parameters, main, main_parameters = compiled
    outer = modules(main)["azure-openai-deployments"]["properties"]["parameters"]
    evaluator = ArmExpressions(main, main_parameters)
    for tier in TIERS:
        child = modules(template)[f"{tier}-model-deployment"]["properties"]["parameters"]
        for suffix in ("DeploymentName", "ModelName", "ModelVersion"):
            name = tier + suffix
            assert outer[name]["value"] == f"[parameters('{name}')]"
            assert evaluator.value(outer[name]["value"]) == parameters[name]
        assert child["model"]["value"]["name"] == f"[parameters('{tier}ModelName')]"
        assert child["model"]["value"]["version"] == f"[parameters('{tier}ModelVersion')]"
        assert child["name"]["value"] == f"[parameters('{tier}DeploymentName')]"
        assert parameters[tier + "ModelName"] == "gpt-5.4"
        assert main["parameters"][tier + "DeploymentName"]["defaultValue"] == (
            f"[format('{tier}-{{0}}', parameters('environmentName'))]"
        )
        assert "defaultValue" not in template["parameters"][tier + "ModelVersion"]
    assert len({parameters[tier + "DeploymentName"] for tier in TIERS}) == 3
    assert {parameters[tier + "DeploymentName"] for tier in TIERS} == {
        "gpt-5.4-dev",
        "gpt-5.4-mini-dev",
        "gpt-5.4-sim-dev",
    }


@pytest.mark.parametrize("mode", ("shared", "distinct", "same-base", "identical-alias", "collision"))
def test_actual_compiled_csv_and_both_service_environment_contracts(compiled, mode):
    template, original, main, main_parameters = compiled
    parameters = dict(original)
    main_parameters = dict(main_parameters)
    if mode in ("distinct", "identical-alias"):
        for tier in TIERS:
            parameters[tier + "ModelName"] = main_parameters[tier + "ModelName"] = (
                f"test-{tier}" if mode == "distinct" else tier
            )
    if mode == "same-base":
        for index, tier in enumerate(TIERS):
            parameters[tier + "ModelVersion"] = main_parameters[tier + "ModelVersion"] = str(index)
    if mode == "collision":
        parameters["draftingModelName"] = main_parameters["draftingModelName"] = "reasoning"
    outputs = wrapper_outputs(template, parameters)
    raw = outputs["azureAiProjectDeployments"]
    if mode == "collision":
        with pytest.raises(FoundryConfigurationError):
            parse_deployment_map(raw)
        return
    mapping = parse_deployment_map(raw)
    assert len(raw.split(",")) == len(mapping)
    assert mapping["text-embedding-3-large@1"] == "text-embedding-3-large-dev"
    assert mapping["text-embedding-3-large"] == "text-embedding-3-large-dev"
    for tier in TIERS:
        assert mapping[tier] == parameters[tier + "DeploymentName"]
        model = parameters[tier + "ModelName"]
        version = parameters[tier + "ModelVersion"]
        if mode == "shared":
            assert model not in mapping and f"{model}@{version}" not in mapping
        else:
            assert mapping[f"{model}@{version}"] == parameters[tier + "DeploymentName"]
            assert (model in mapping) == (mode in ("distinct", "identical-alias"))
    reference = {"outputs": {key: {"value": value} for key, value in outputs.items()}}
    evaluator = ArmExpressions(
        main,
        main_parameters,
        {
            "Microsoft.Resources/deployments/azure-openai-deployments": reference,
            "openAiDeployments": reference,
        },
    )
    for service in ("api", "agents"):
        app = next(
            item
            for item in resources(main)
            if item["type"] == "Microsoft.App/containerApps" and f"}}{service}-" in item["name"]
        )
        environment = {entry["name"]: entry["value"] for entry in app["properties"]["template"]["containers"][0]["env"]}
        assert evaluator.value(environment["AZURE_AI_PROJECT_DEPLOYMENTS"]) == raw
        assert evaluator.value(environment["EMBEDDING_DEPLOYMENT_NAME"]) == "text-embedding-3-large-dev"
        for tier in TIERS:
            for suffix, expected in (
                ("DEPLOYMENT", parameters[tier + "DeploymentName"]),
                ("MODEL_ID", parameters[tier + "ModelName"]),
                ("MODEL_VERSION", parameters[tier + "ModelVersion"]),
                ("MODEL_KEY", parameters[tier + "ModelName"] + "@" + parameters[tier + "ModelVersion"]),
            ):
                assert evaluator.value(environment[f"AZURE_AI_{tier.upper()}_{suffix}"]) == expected


def test_actual_compiled_protections_embedding_and_serialization_match_observed_baseline(compiled):
    template, parameters, main, main_parameters = compiled
    baseline = json.loads((EVIDENCE / "convergence-preservation-baseline.json").read_text())
    accepted = json.loads((EVIDENCE.parents[1] / "deployment-baseline.json").read_text())
    base_policy = next(item["properties"] for item in baseline["rai"]["value"] if item["name"] == "Microsoft.DefaultV2")
    assert base_policy["mode"] == accepted["rai"]["mode"]
    assert base_policy["contentFilters"] == accepted["rai"]["base_filters"]
    evaluator = ArmExpressions(template, parameters)
    chain = []
    for tier in (*TIERS, "embedding"):
        module = modules(template)[f"{tier}-model-deployment"]
        bound = evaluator.value(module["properties"]["parameters"])
        bound = {key: value["value"] for key, value in bound.items()}
        observed = next(item for item in baseline["deployments"]["value"] if item["name"] == bound["name"])
        assert bound["accountName"] == baseline["target"]["account"]
        assert bound["model"] == observed["properties"]["model"]
        assert bound["sku"] == observed["sku"]
        assert bound["raiPolicyName"] == observed["properties"]["raiPolicyName"]
        assert bound["versionUpgradeOption"] == observed["properties"]["versionUpgradeOption"]
        child = module["properties"]["template"]
        writes = [resource for resource in resources(child) if not resource.get("existing")]
        assert len(writes) == 1 and writes[0]["type"] == "Microsoft.CognitiveServices/accounts/deployments"
        assert writes[0]["apiVersion"] == "2026-05-01"
        expected = {
            key: value
            for key, value in observed["properties"].items()
            if key not in {"capabilities", "provisioningState", "rateLimits"}
        }
        assert ArmExpressions(child, bound).value(writes[0]["properties"]) == expected
        if tier != "embedding":
            policy = next(
                item
                for item in resources(template)
                if item["type"].endswith("/raiPolicies") and tier + "RaiPolicyName" in item["name"]
            )
            actual = evaluator.value(policy["properties"])
            live = next(
                item["properties"] for item in baseline["rai"]["value"] if item["name"] == bound["raiPolicyName"]
            )
            assert actual == {key: value for key, value in live.items() if key != "type"}
            if chain:
                assert any(
                    evaluator.value(dependency) in resource_references(template, chain[-1], evaluator)
                    for dependency in policy["dependsOn"]
                )
            assert any(
                evaluator.value(dependency) in resource_references(template, policy, evaluator)
                for dependency in module["dependsOn"]
            )
        else:
            assert any(
                evaluator.value(dependency) in resource_references(template, chain[-1], evaluator)
                for dependency in module["dependsOn"]
            )
        chain.append(module)
    assert all(
        item.get("existing") for item in resources(template) if item["type"] == "Microsoft.CognitiveServices/accounts"
    )
    assert template["parameters"]["agentPrincipalIds"]["defaultValue"] == []
    diagnostic = next(item for item in resources(template) if item["type"] == "Microsoft.Insights/diagnosticSettings")
    configured = evaluator.value(diagnostic["properties"])
    observed = baseline["diagnostics"]["value"][0]["properties"]
    assert configured["workspaceId"].lower() == observed["workspaceId"].lower()
    for category_type in ("logs", "metrics"):
        expected = [
            {key: value for key, value in item.items() if value is not None} for item in observed[category_type]
        ]
        assert configured[category_type] == expected
    outer = modules(main)["azure-openai-deployments"]["properties"]["parameters"]
    selected = ArmExpressions(main, main_parameters).value(outer["diagnosticSettings"]["value"])
    assert selected == parameters["diagnosticSettings"]
    json_parameters = json.loads((ROOT / "infra" / "main.parameters.dev.json").read_text())["parameters"]
    assert json_parameters["openAiDiagnosticSettings"]["value"] == selected
    selected_state = ArmExpressions(main, main_parameters).value(outer["deploymentOperatingStates"]["value"])
    assert selected_state == parameters["deploymentOperatingStates"]
    assert json_parameters["deploymentOperatingStates"]["value"] == selected_state


@pytest.mark.parametrize("tier", (*TIERS, "embedding"))
@pytest.mark.parametrize("state,capacity", (("Paused", 0), ("Running", 17)))
def test_compiled_operating_state_is_explicit_and_independent_of_sku(compiled, tier, state, capacity):
    template, original, _, _ = compiled
    parameters = copy.deepcopy(original)
    parameters["deploymentOperatingStates"][tier] = {"currentCapacity": capacity, "deploymentState": state}
    module = modules(template)[f"{tier}-model-deployment"]
    bound = ArmExpressions(template, parameters).value(module["properties"]["parameters"])
    bound = {key: value["value"] for key, value in bound.items()}
    child = module["properties"]["template"]
    deployment = next(item for item in resources(child) if item["type"].endswith("/deployments"))
    properties = ArmExpressions(child, bound).value(deployment["properties"])
    assert properties["currentCapacity"] == capacity
    assert properties["deploymentState"] == state
    assert "defaultValue" not in template["parameters"]["deploymentOperatingStates"]
    assert "defaultValue" not in child["parameters"]["operatingState"]


@pytest.mark.parametrize("tier", TIERS)
def test_actual_compiled_rai_preserves_complete_action_semantics(compiled, tier):
    template, parameters, _, _ = compiled
    baseline = json.loads((EVIDENCE / "convergence-preservation-baseline.json").read_text())
    policy = next(
        item
        for item in resources(template)
        if item["type"].endswith("/raiPolicies") and tier + "RaiPolicyName" in item["name"]
    )
    actual = ArmExpressions(template, parameters).value(policy["properties"])
    name = ArmExpressions(template, parameters).value(policy["name"]).split("/")[-1]
    live = next(item["properties"] for item in baseline["rai"]["value"] if item["name"] == name)
    assert actual == {key: value for key, value in live.items() if key != "type"}


def test_vendored_source_bytes_are_the_published_child():
    path = ROOT / "infra" / "modules" / "vendor" / "avm-cognitive-services-deployment-0.18.0"
    assert hashlib.sha256((path / "main.bicep").read_bytes()).hexdigest() == (
        "a0d007d0f61a143949c0d0acb771f59c9bc96f72db4d952fc03dc8a4d1834aa1"
    )
    assert hashlib.sha256((path / "LICENSE").read_bytes()).hexdigest() == (
        "c2cfccb812fe482101a8f04597dfc5a9991a6b2748266c47ac91b6a5aae15383"
    )


@pytest.mark.parametrize("settings", ({}, {"logs": []}, {"metrics": []}))
def test_diagnostic_snapshot_overrides_only_explicit_fields(compiled, settings):
    template, parameters, _, _ = compiled
    diagnostic = next(item for item in resources(template) if item["type"] == "Microsoft.Insights/diagnosticSettings")
    configured = ArmExpressions(template, {**parameters, "diagnosticSettings": settings}).value(
        diagnostic["properties"],
    )
    assert configured["logs"] == settings.get(
        "logs",
        [
            {"category": "RequestResponse", "enabled": True},
            {"category": "Audit", "enabled": True},
        ],
    )
    assert configured["metrics"] == settings.get(
        "metrics",
        [
            {"category": "AllMetrics", "enabled": True},
        ],
    )
