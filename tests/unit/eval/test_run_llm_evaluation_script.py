"""Tests for the LLM evaluation driver script."""

from __future__ import annotations

import dataclasses
import importlib.util
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[3]
_SCRIPT_PATH = _REPO_ROOT / "scripts" / "run_llm_evaluation.py"
_EVAL_PLATFORM_BICEP = _REPO_ROOT / "infra" / "bicep" / "modules" / "eval" / "eval-platform.bicep"


def _load_script():
    spec = importlib.util.spec_from_file_location("run_llm_evaluation", _SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_run_cmd_resolves_azure_cli_cmd_shim(monkeypatch):
    script = _load_script()
    executed: list[list[str]] = []

    def fake_which(tool: str) -> str | None:
        return r"C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin\az.CMD" if tool == "az" else None

    def fake_run(cmd: list[str], **_kwargs):
        executed.append(cmd)
        return subprocess.CompletedProcess(cmd, 0, '{"azure-cli": "2.85.0"}', "")

    monkeypatch.setattr(script.shutil, "which", fake_which)
    monkeypatch.setattr(script.subprocess, "run", fake_run)

    result = script.run_cmd("preflight", ["az", "version"], dry_run=False, capture=True)

    assert result.returncode == 0
    assert executed == [[r"C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin\az.CMD", "version"]]


def test_stage_provision_creates_resource_group_before_deployment(monkeypatch):
    script = _load_script()
    commands: list[list[str]] = []
    template = _EVAL_PLATFORM_BICEP
    parameters = _REPO_ROOT / "infra" / "bicep" / "parameters" / "eval-platform.dev.json"
    env = script.EnvironmentConfig(
        name="dev",
        resource_group="rg-ama-eval-dev",
        location="australiaeast",
        runner_job="caj-eval-runner-dev",
        reconciler_job="caj-eval-reconciler-dev",
        bicep_template=template,
        bicep_parameters=parameters,
        api_base_url="https://api.ama-dev.example",
        api_resource_uri="api://ama-api-dev",
        storage_account_query="[0]",
        keyvault_name="kv-ama-eval-dev",
        signing_key="eval-signing-key",
    )
    ctx = script.RunContext(env=env, args=SimpleNamespace(dry_run=True))

    def fake_run_cmd(stage: str, cmd: list[str], **_kwargs):
        commands.append(cmd)
        return subprocess.CompletedProcess(cmd, 0, "", "")

    monkeypatch.setattr(script, "run_cmd", fake_run_cmd)

    script.stage_provision(ctx)

    assert commands[0] == [
        "az",
        "group",
        "create",
        "--name",
        "rg-ama-eval-dev",
        "--location",
        "australiaeast",
        "--tags",
        "Environment=dev",
        "ManagedBy=Bicep",
        "Project=ama",
        "Owner=ama-eval",
        "feature=030-llm-eval-framework",
        "workload=ama-eval",
        "--output",
        "none",
    ]
    assert commands[1][:4] == ["az", "deployment", "group", "create"]
    assert "deployContainerJobs=false" in commands[1]
    assert "deployApi=false" in commands[1]
    assert commands[2][:4] == ["az", "acr", "build", "--registry"]
    assert commands[2][5:7] == ["--image", "eval-runner:dev"]
    assert str(_REPO_ROOT) not in commands[2]
    assert "<minimal-eval-runner-context>" in commands[2][-1]
    assert commands[3][:4] == ["az", "acr", "build", "--registry"]
    assert commands[3][5:7] == ["--image", "ama/api:dev"]
    assert "<minimal-api-context>" in commands[3][-1]
    assert commands[4][:4] == ["az", "deployment", "group", "create"]
    assert "deployContainerJobs=true" in commands[4]
    assert "deployApi=true" in commands[4]


def test_build_eval_runner_image_uses_minimal_temporary_context(monkeypatch):
    script = _load_script()
    commands: list[list[str]] = []
    prepared_contexts: list[Path] = []
    env = script.ENVIRONMENTS["dev"]
    ctx = script.RunContext(env=env, args=SimpleNamespace(dry_run=False))
    build_root = Path(r"C:\acr-build-context")

    class FakeTemporaryDirectory:
        def __init__(self, prefix: str):
            self.prefix = prefix

        def __enter__(self):
            return str(build_root)

        def __exit__(self, *_args):
            return False

    def fake_prepare_eval_runner_build_context(root: Path) -> Path:
        prepared_contexts.append(root)
        return root

    def fake_run_cmd(stage: str, cmd: list[str], **_kwargs):
        commands.append(cmd)
        return subprocess.CompletedProcess(cmd, 0, "", "")

    monkeypatch.setattr(script.tempfile, "TemporaryDirectory", FakeTemporaryDirectory)
    monkeypatch.setattr(script, "prepare_eval_runner_build_context", fake_prepare_eval_runner_build_context)
    monkeypatch.setattr(script, "run_cmd", fake_run_cmd)

    script.build_eval_runner_image(ctx, "provision", "acramaevaldevxpm32u")

    assert prepared_contexts == [build_root]
    assert commands == [
        [
            "az",
            "acr",
            "build",
            "--registry",
            "acramaevaldevxpm32u",
            "--image",
            "eval-runner:dev",
            "--file",
            str(build_root / script.EVAL_RUNNER_DOCKERFILE_RELATIVE),
            str(build_root),
        ]
    ]


def test_eval_platform_storage_account_name_is_capped():
    template = _EVAL_PLATFORM_BICEP.read_text(encoding="utf-8")

    assert "var storageAccountName = take(" in template
    assert ", 24)" in template
    assert "name: storageAccountName" in template
    assert "name: 'stamaeval${replace(nameSuffix, '-', '')}'" not in template


def test_eval_platform_creates_observability_resources_on_demand():
    template = _EVAL_PLATFORM_BICEP.read_text(encoding="utf-8")

    assert "param logAnalyticsWorkspaceId string" not in template
    assert "resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2023-09-01'" in template
    assert "WorkspaceResourceId: logAnalytics.id" in template
    assert "customerId: logAnalytics.properties.customerId" in template
    assert "sharedKey: logAnalytics.listKeys().primarySharedKey" in template


def test_eval_platform_relaxes_data_plane_network_rules_for_dev_only():
    template = _EVAL_PLATFORM_BICEP.read_text(encoding="utf-8")

    assert "var allowPublicEvalDataPlane = env == 'dev'" in template
    assert "var dataPlanePublicNetworkAccess = allowPublicEvalDataPlane ? 'Enabled' : 'Disabled'" in template
    assert "var dataPlaneNetworkDefaultAction = allowPublicEvalDataPlane ? 'Allow' : 'Deny'" in template
    assert "publicNetworkAccess: dataPlanePublicNetworkAccess" in template
    assert "defaultAction: dataPlaneNetworkDefaultAction" in template


def test_eval_platform_disables_key_vault_purge_protection_in_dev():
    template = _EVAL_PLATFORM_BICEP.read_text(encoding="utf-8")

    assert "enablePurgeProtection: env == 'dev' ? null : true" in template
    assert "softDeleteRetentionInDays: env == 'dev' ? 7 : 90" in template
    assert "enablePurgeProtection: true\n" not in template
    assert "softDeleteRetentionInDays: 90\n" not in template


def test_eval_platform_provisions_foundry_account_with_curated_models():
    template = _EVAL_PLATFORM_BICEP.read_text(encoding="utf-8")

    assert "resource foundry 'Microsoft.CognitiveServices/accounts@2024-10-01'" in template
    assert "kind: 'AIServices'" in template
    # 7-model curated set per user choice
    for marker in (
        "modelName: 'gpt-5.6'",
        "modelName: 'gpt-5.6-mini'",
        "modelName: 'Phi-4'",
        "modelName: 'Llama-3.3-70B-Instruct'",
        "modelName: 'Mistral-Large-3'",
        "modelName: 'DeepSeek-V3.2'",
    ):
        assert marker in template, f"missing {marker} in eval-platform.bicep"
    # Azure AI Model Inference requires MaaS chat completions on the Foundry account.
    assert "a97b65f3-24c7-4388-baec-2e87135dc908" in template
    assert "AZURE_AI_PROJECT_ENDPOINT" in template
    assert "AZURE_AI_PROJECT_DEPLOYMENTS" in template


def test_eval_runner_can_upload_sample_traces():
    template = _EVAL_PLATFORM_BICEP.read_text(encoding="utf-8")
    runner_resource = template.split("resource jobs 'Microsoft.App/jobs@", 1)[1].split(
        "// --- AMA API container",
        1,
    )[0]

    assert "{ name: 'EVAL_STORAGE_ACCOUNT',     value: storage.name }" in runner_resource
    assert "{ name: 'EVAL_TRACES_CONTAINER',    value: 'runs' }" in runner_resource


def test_script_default_models_match_bicep_curated_set():
    import importlib.util

    spec = importlib.util.spec_from_file_location("run_llm_evaluation", _SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    expected = {
        "gpt-5.6:2026-03-05",
        "gpt-5.6-mini:2026-03-17",
        "Phi-4:7",
        "Llama-3.3-70B-Instruct:9",
        "Mistral-Large-3:1",
        "DeepSeek-V3.2:1",
    }
    assert set(module.DEFAULT_MODELS) == expected


def test_script_max_cases_default_is_25():
    import importlib.util

    spec = importlib.util.spec_from_file_location("run_llm_evaluation", _SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    args = module.parse_args(["--stage", "execute", "--env", "dev"])
    assert args.max_cases == 25
    assert args.min_evaluated_samples is None


def test_eval_platform_uses_valid_key_vault_name_pattern():
    template = _EVAL_PLATFORM_BICEP.read_text(encoding="utf-8")

    assert "var keyVaultName = 'kv-amaeval-${storageEnvSegment}-${shortUniqueSuffix}${keyVaultNameSalt}'" in template
    assert "name: keyVaultName" in template
    assert "name: 'kv-ama-eval-${take(nameSuffix, 18)}'" not in template


def test_eval_platform_dev_params_set_key_vault_salt():
    import json

    dev_params_path = _REPO_ROOT / "infra" / "bicep" / "parameters" / "eval-platform.dev.json"
    dev_params = json.loads(dev_params_path.read_text(encoding="utf-8"))
    assert dev_params["parameters"]["keyVaultNameSalt"]["value"] == "a"


def test_eval_platform_includes_api_container_app_with_dev_tokens():
    template = _EVAL_PLATFORM_BICEP.read_text(encoding="utf-8")

    assert "param deployApi bool = false" in template
    assert "resource apiContainerApp 'Microsoft.App/containerApps@2024-03-01'" in template
    assert "name: 'app-ama-api-${env}'" in template
    assert "EVAL_ALLOW_DEV_TOKENS" in template
    assert "EVAL_RUNNER_JOB_NAME" in template
    assert "Microsoft.DocumentDB/databaseAccounts/sqlRoleAssignments" in template
    assert "output apiFqdn string" in template


def test_eval_platform_emits_anonymous_env_var_only_in_dev():
    """FR-022a: ``EVAL_ALLOW_ANONYMOUS=1`` and the dev-only env block must
    be appended to the API container env vars **only** when ``env == 'dev'``.

    Staging and production deployments must NOT carry the anonymous flag,
    so the role guard cannot be tricked into honouring it there.
    """

    template = _EVAL_PLATFORM_BICEP.read_text(encoding="utf-8")

    # The conditional concat() block must exist…
    assert "env == 'dev' ? [" in template
    # …and must include the EVAL_ALLOW_ANONYMOUS env var inside the dev branch.
    assert "{ name: 'EVAL_ALLOW_ANONYMOUS', value: '1' }" in template
    # ENVIRONMENT must always be set so the role guard knows where it is running.
    assert "{ name: 'ENVIRONMENT',                            value: env }" in template
    # No unconditional anonymous env var: the literal must only ever appear
    # inside the dev-only ternary branch (asserted above), never as a
    # standalone, always-on entry like the legacy EVAL_ALLOW_DEV_TOKENS line.
    assert "{ name: 'EVAL_ALLOW_ANONYMOUS',                  value:" not in template


def test_eval_platform_api_image_repository_is_ama_api():
    template = _EVAL_PLATFORM_BICEP.read_text(encoding="utf-8")

    assert "var apiImageRepository = 'ama/api'" in template
    assert "param apiImageTag string = env" in template
    assert "param evalRunnerImageTag string = env" in template


def test_provision_builds_api_image_into_acr(monkeypatch):
    script = _load_script()
    commands: list[list[str]] = []
    env = script.ENVIRONMENTS["dev"]
    ctx = script.RunContext(env=env, args=SimpleNamespace(dry_run=True))

    def fake_run_cmd(stage: str, cmd: list[str], **_kwargs):
        commands.append(cmd)
        return subprocess.CompletedProcess(cmd, 0, "", "")

    monkeypatch.setattr(script, "run_cmd", fake_run_cmd)

    script.stage_provision(ctx)

    api_build = next(
        (c for c in commands if c[:4] == ["az", "acr", "build", "--registry"] and "ama/api:dev" in c),
        None,
    )
    assert api_build is not None
    assert "<minimal-api-context>" in api_build[-1]


def test_resolve_api_base_url_uses_deployment_output(monkeypatch):
    script = _load_script()
    env = script.ENVIRONMENTS["dev"]
    ctx = script.RunContext(env=env, args=SimpleNamespace(dry_run=False, api_base_url=None))

    def fake_az_json(stage, args, dry_run):
        if args[:3] == ["deployment", "group", "show"]:
            return "app-ama-api-dev.example.azurecontainerapps.io"
        raise AssertionError(f"unexpected az_json: {args}")

    monkeypatch.setattr(script, "az_json", fake_az_json)

    script._resolve_api_base_url(ctx, "publish")

    assert ctx.env.api_base_url == "https://app-ama-api-dev.example.azurecontainerapps.io"


def test_resolve_api_base_url_respects_cli_override(monkeypatch):
    script = _load_script()
    env = script.ENVIRONMENTS["dev"]
    ctx = script.RunContext(
        env=env,
        args=SimpleNamespace(dry_run=False, api_base_url="https://api.custom.local"),
    )

    def fail_call(*_a, **_kw):
        raise AssertionError("should not call az_json when CLI override present")

    monkeypatch.setattr(script, "az_json", fail_call)

    script._resolve_api_base_url(ctx, "publish")


def test_environment_config_has_no_separate_foundry_rg():
    """All eval Azure resources MUST live in the eval RG; the legacy
    foundry_resource_group / foundry_account fields are removed so the script
    can no longer reach into a sibling RG that doesn't exist."""
    script = _load_script()

    field_names = {f.name for f in dataclasses.fields(script.EnvironmentConfig)}
    assert "foundry_resource_group" not in field_names
    assert "foundry_account" not in field_names


def test_run_cmd_surfaces_cae_reauth_message(monkeypatch, capfd):
    """When az fails with a CAE / Conditional Access challenge, the script must
    print a clear remediation pointing the operator at `az login` instead of
    just dumping a generic 'command failed' message."""
    script = _load_script()

    monkeypatch.setattr(script.shutil, "which", lambda tool: f"/usr/bin/{tool}")

    def fake_run(cmd, **_kwargs):
        return subprocess.CompletedProcess(
            cmd,
            1,
            "",
            "ERROR: Continuous access evaluation resulted in challenge with result: "
            "InteractionRequired and code: TokenCreatedWithOutdatedPolicies\n",
        )

    monkeypatch.setattr(script.subprocess, "run", fake_run)

    with pytest.raises(SystemExit):
        script.run_cmd("provision", ["az", "ad", "signed-in-user", "show"], dry_run=False, check=True)

    out, err = capfd.readouterr()
    combined = out + err
    assert "Continuous Access Evaluation" in combined or "Conditional Access" in combined
    assert "az login" in combined


def test_stage_deprovision_uses_eval_resource_group(monkeypatch):
    """stage_deprovision must call az against ctx.env.resource_group only —
    no reference to a separate foundry RG."""
    script = _load_script()
    env = script.ENVIRONMENTS["dev"]
    args = SimpleNamespace(dry_run=False, run_id="r-abc")
    ctx = script.RunContext(env=env, args=args)
    ctx.state["foundry_account"] = "aoai-amaeval-dev-xxxxx"

    az_calls: list[list[str]] = []
    run_calls: list[list[str]] = []

    def fake_az_json(stage, args, dry_run):
        az_calls.append(args)
        if args[:4] == ["cognitiveservices", "account", "deployment", "list"]:
            # First call: run-scoped lookup -> return one deployment
            # Subsequent: orphan-check -> return empty list
            query = args[args.index("--query") + 1] if "--query" in args else ""
            if query.startswith("[?tags.runId"):
                return ["dep-1"]
            return []
        return None

    def fake_run_cmd(stage, cmd, **_kwargs):
        run_calls.append(cmd)
        return subprocess.CompletedProcess(cmd, 0, "", "")

    monkeypatch.setattr(script, "az_json", fake_az_json)
    monkeypatch.setattr(script, "run_cmd", fake_run_cmd)

    script.stage_deprovision(ctx)

    # No call should reference rg-ama-foundry-* or ai-foundry-ama-*
    flat = [tok for cmd in az_calls + run_calls for tok in cmd]
    assert all(not tok.startswith("rg-ama-foundry-") for tok in flat), flat
    assert all(not tok.startswith("ai-foundry-ama-") for tok in flat), flat
    # All RG-bearing args target the eval RG
    rg_args = [
        tok
        for cmd in az_calls + run_calls
        for i, tok in enumerate(cmd)
        if i and (cmd[i - 1] in {"-g", "--resource-group", "--name"} and tok.startswith("rg-"))
    ]
    assert all(rg == "rg-ama-eval-dev" for rg in rg_args), rg_args


def test_eval_platform_uses_acr_for_eval_runner_images():
    template = _EVAL_PLATFORM_BICEP.read_text(encoding="utf-8")

    assert "resource containerRegistry 'Microsoft.ContainerRegistry/registries@2025-04-01'" in template
    assert "adminUserEnabled: false" in template
    assert "anonymousPullEnabled: false" in template
    assert "azureADAuthenticationAsArmPolicy" in template
    assert "resource acrPullAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01'" in template
    assert "registries: [" in template
    assert "server: containerRegistry.properties.loginServer" in template
    assert "identity: runnerIdentity.id" in template
    assert (
        "image: '${containerRegistry.properties.loginServer}/${evalRunnerImageRepository}:${evalRunnerImageTag}'"
        in template
    )
    assert "param evalRunnerImage string" not in template
    assert "ghcr.io" not in template


def test_eval_platform_parameters_do_not_reference_placeholder_workspace():
    parameter_paths = [
        _REPO_ROOT / "infra" / "bicep" / "parameters" / "eval-platform.dev.json",
        _REPO_ROOT / "infra" / "bicep" / "parameters" / "eval-platform.staging.json",
        _REPO_ROOT / "infra" / "bicep" / "parameters" / "eval-platform.production.json",
    ]

    for parameter_path in parameter_paths:
        params = parameter_path.read_text(encoding="utf-8")
        assert "logAnalyticsWorkspaceId" not in params
        assert "00000000-0000-0000-0000-000000000000" not in params
        assert "evalRunnerImage" not in params
        assert "ghcr.io" not in params


def test_optional_access_token_failure_returns_none(monkeypatch):
    script = _load_script()

    def fake_run_cmd(stage: str, cmd: list[str], **_kwargs):
        return subprocess.CompletedProcess(cmd, 1, "", "invalid_resource")

    monkeypatch.setattr(script, "run_cmd", fake_run_cmd)

    token = script.get_access_token("publish", "api://ama-api-dev", dry_run=False, optional=True)

    assert token is None


def test_blob_upload_network_failure_is_not_silent():
    script = _load_script()
    result = subprocess.CompletedProcess(["az", "storage", "blob", "upload"], 1, "", "network rules blocked")

    try:
        script.handle_blob_upload_result("publish", result, "dataset/cases.jsonl", script.EXIT_PUBLISH)
    except SystemExit as exc:
        assert exc.code == script.EXIT_PUBLISH
    else:
        raise AssertionError("blob upload failure should exit")


def test_blob_upload_existing_blob_is_tolerated():
    script = _load_script()
    result = subprocess.CompletedProcess(["az", "storage", "blob", "upload"], 1, "", "BlobAlreadyExists")

    script.handle_blob_upload_result("publish", result, "dataset/cases.jsonl", script.EXIT_PUBLISH)


def _make_dev_ctx(script, args=None):
    env = script.ENVIRONMENTS["dev"]
    return SimpleNamespace(env=env, dry_run=False, args=args or SimpleNamespace())


def test_grant_dev_storage_access_creates_role_assignment(monkeypatch):
    script = _load_script()
    ctx = _make_dev_ctx(script)
    az_json_calls: list[list[str]] = []
    run_cmd_calls: list[list[str]] = []

    def fake_az_json(stage, args, dry_run):
        az_json_calls.append(args)
        if args[:2] == ["account", "show"]:
            return {"id": "sub-1", "userType": "user", "user": "alice@example.com"}
        if args[:3] == ["ad", "signed-in-user", "show"]:
            return "obj-alice"
        if args[:3] == ["role", "assignment", "list"]:
            return []
        raise AssertionError(f"unexpected az_json: {args}")

    def fake_run_cmd(stage, cmd, **_kwargs):
        run_cmd_calls.append(cmd)
        return subprocess.CompletedProcess(cmd, 0, "", "")

    monkeypatch.setattr(script, "az_json", fake_az_json)
    monkeypatch.setattr(script, "run_cmd", fake_run_cmd)

    granted = script.grant_dev_storage_access(ctx, "publish", "stamaevaldevxpm32u345uu7")

    assert granted is True
    assert any(c[:4] == ["az", "role", "assignment", "create"] for c in run_cmd_calls)


def test_grant_dev_storage_access_skips_when_existing(monkeypatch):
    script = _load_script()
    ctx = _make_dev_ctx(script)
    run_cmd_calls: list[list[str]] = []

    def fake_az_json(stage, args, dry_run):
        if args[:2] == ["account", "show"]:
            return {"id": "sub-1", "userType": "user", "user": "alice@example.com"}
        if args[:3] == ["ad", "signed-in-user", "show"]:
            return "obj-alice"
        if args[:3] == ["role", "assignment", "list"]:
            return ["/subscriptions/sub-1/.../roleAssignments/abc"]
        raise AssertionError(f"unexpected az_json: {args}")

    def fake_run_cmd(stage, cmd, **_kwargs):
        run_cmd_calls.append(cmd)
        return subprocess.CompletedProcess(cmd, 0, "", "")

    monkeypatch.setattr(script, "az_json", fake_az_json)
    monkeypatch.setattr(script, "run_cmd", fake_run_cmd)

    granted = script.grant_dev_storage_access(ctx, "publish", "stamaevaldevxpm32u345uu7")

    assert granted is False
    assert run_cmd_calls == []


def test_grant_dev_storage_access_tolerates_existing_assignment(monkeypatch):
    script = _load_script()
    ctx = _make_dev_ctx(script)

    def fake_az_json(stage, args, dry_run):
        if args[:2] == ["account", "show"]:
            return {"id": "sub-1", "userType": "user", "user": "alice@example.com"}
        if args[:3] == ["role", "assignment", "list"]:
            return []
        return "obj-alice"

    def fake_run_cmd(stage, cmd, **_kwargs):
        return subprocess.CompletedProcess(cmd, 1, "", "RoleAssignmentExists: already exists")

    monkeypatch.setattr(script, "az_json", fake_az_json)
    monkeypatch.setattr(script, "run_cmd", fake_run_cmd)

    script.grant_dev_storage_access(ctx, "publish", "stamaevaldevxpm32u345uu7")


def test_grant_dev_storage_access_skipped_outside_dev(monkeypatch):
    script = _load_script()
    env = script.ENVIRONMENTS["staging"]
    ctx = SimpleNamespace(env=env, dry_run=False, args=SimpleNamespace())

    def fail_call(*_a, **_kw):
        raise AssertionError("should not be called outside dev")

    monkeypatch.setattr(script, "az_json", fail_call)
    monkeypatch.setattr(script, "run_cmd", fail_call)

    script.grant_dev_storage_access(ctx, "publish", "stamaevalstagingxxx")


def test_wait_for_rbac_propagation_only_when_granted(monkeypatch):
    script = _load_script()
    sleep_calls: list[float] = []
    monkeypatch.setattr(script.time, "sleep", lambda s: sleep_calls.append(s))

    script.wait_for_rbac_propagation("publish", granted=False)
    assert sleep_calls == []

    script.wait_for_rbac_propagation("publish", granted=True)
    assert sleep_calls == [script._DEV_RBAC_PROPAGATION_SECONDS]


def test_api_base_url_override_from_cli():
    script = _load_script()
    args = script.parse_args(["--stage", "publish", "--env", "dev", "--api-base-url", "https://api.dev.local/"])
    assert args.api_base_url == "https://api.dev.local/"


def test_api_base_url_override_from_env(monkeypatch):
    script = _load_script()
    monkeypatch.setenv("AMA_API_BASE_URL", "https://api.dev.local")
    args = script.parse_args(["--stage", "publish", "--env", "dev"])
    assert args.api_base_url == "https://api.dev.local"


# ---------------------------------------------------------------------------
# FR-022a: dev-only anonymous-mode auth branching
# ---------------------------------------------------------------------------


class _FakeResp:
    def __init__(self, status_code: int, body: dict | None = None) -> None:
        self.status_code = status_code
        self._body = body or {}

    def json(self) -> dict:
        return self._body


def _dev_ctx_with_base_url(script, base_url: str = "https://api.dev.local"):
    env = script.ENVIRONMENTS["dev"].__class__(
        **{**script.ENVIRONMENTS["dev"].__dict__, "api_base_url": base_url},
    )
    return script.RunContext(env=env, args=SimpleNamespace(dry_run=False))


def test_detect_anonymous_mode_returns_true_when_health_advertises_it(monkeypatch):
    script = _load_script()
    ctx = _dev_ctx_with_base_url(script)
    captured: list[str] = []

    def fake_get(url, timeout):  # noqa: ARG001
        captured.append(url)
        return _FakeResp(200, {"status": "ok", "anonymousAccess": True})

    monkeypatch.setattr(script.requests, "get", fake_get)

    assert script.detect_anonymous_mode(ctx, "publish") is True
    assert captured == ["https://api.dev.local/api/eval/health"]
    # Cached on second call (no second HTTP request).
    assert script.detect_anonymous_mode(ctx, "publish") is True
    assert len(captured) == 1


def test_detect_anonymous_mode_returns_false_when_health_says_off(monkeypatch):
    script = _load_script()
    ctx = _dev_ctx_with_base_url(script)
    monkeypatch.setattr(
        script.requests,
        "get",
        lambda url, timeout: _FakeResp(200, {"status": "ok", "anonymousAccess": False}),  # noqa: ARG005
    )
    assert script.detect_anonymous_mode(ctx, "publish") is False


def test_detect_anonymous_mode_falls_back_when_probe_fails(monkeypatch):
    script = _load_script()
    ctx = _dev_ctx_with_base_url(script)

    def boom(url, timeout):  # noqa: ARG001
        raise script.requests.exceptions.ConnectionError("dns fail")

    monkeypatch.setattr(script.requests, "get", boom)
    # Should NOT raise — the script must fall back to bearer-token auth on probe failure.
    assert script.detect_anonymous_mode(ctx, "publish") is False


def test_detect_anonymous_mode_short_circuits_outside_dev(monkeypatch):
    script = _load_script()
    env = script.ENVIRONMENTS["staging"]
    ctx = script.RunContext(env=env, args=SimpleNamespace(dry_run=False))

    def must_not_call(*_a, **_kw):
        raise AssertionError("anonymous probe should never run outside dev")

    monkeypatch.setattr(script.requests, "get", must_not_call)
    assert script.detect_anonymous_mode(ctx, "publish") is False


def test_get_eval_token_returns_none_when_anonymous_mode_on(monkeypatch):
    script = _load_script()
    ctx = _dev_ctx_with_base_url(script)
    monkeypatch.setattr(
        script.requests,
        "get",
        lambda url, timeout: _FakeResp(200, {"anonymousAccess": True}),  # noqa: ARG005
    )

    token = script.get_eval_token(ctx, "publish")

    assert token is None  # No Authorization header will be sent.


def test_get_eval_token_returns_dev_token_when_anonymous_mode_off(monkeypatch):
    script = _load_script()
    ctx = _dev_ctx_with_base_url(script)
    monkeypatch.setattr(
        script.requests,
        "get",
        lambda url, timeout: _FakeResp(200, {"anonymousAccess": False}),  # noqa: ARG005
    )
    monkeypatch.setenv("USERNAME", "alice")

    token = script.get_eval_token(ctx, "publish")

    assert isinstance(token, str)
    assert token.startswith("dev:alice:")
    assert "Eval.Operator" in token
    assert "Eval.Viewer" in token
    assert "Eval.Auditor" in token


def test_get_eval_token_falls_back_to_dev_token_when_probe_fails(monkeypatch):
    script = _load_script()
    ctx = _dev_ctx_with_base_url(script)

    def boom(url, timeout):  # noqa: ARG001
        raise script.requests.exceptions.ConnectionError("api unreachable")

    monkeypatch.setattr(script.requests, "get", boom)
    monkeypatch.setenv("USERNAME", "bob")

    token = script.get_eval_token(ctx, "publish")

    assert isinstance(token, str)
    assert token.startswith("dev:bob:")


def test_get_eval_token_outside_dev_uses_entra(monkeypatch):
    script = _load_script()
    env = script.ENVIRONMENTS["staging"]
    ctx = script.RunContext(env=env, args=SimpleNamespace(dry_run=False))

    captured: list[tuple[str, str]] = []

    def fake_get_access_token(stage, resource_uri, dry_run, **_):
        captured.append((stage, resource_uri))
        return "real-entra-jwt"

    monkeypatch.setattr(script, "get_access_token", fake_get_access_token)

    token = script.get_eval_token(ctx, "publish")

    assert token == "real-entra-jwt"
    assert captured == [("publish", env.api_resource_uri)]


def test_eval_request_headers_omits_authorization_when_token_none():
    script = _load_script()
    headers = script._eval_request_headers(None, content_type="application/json")
    assert "Authorization" not in headers
    assert headers == {"Content-Type": "application/json"}


def test_eval_request_headers_includes_authorization_when_token_present():
    script = _load_script()
    headers = script._eval_request_headers("abc")
    assert headers == {"Authorization": "Bearer abc"}


def test_stage_execute_omits_authorization_header_when_anonymous(monkeypatch):
    """End-to-end: when the API advertises anonymous mode, the script must
    POST /api/eval/runs **without** an Authorization header (FR-022a)."""

    script = _load_script()
    env = script.ENVIRONMENTS["dev"]
    # Force a known api_base_url so we don't depend on Azure deployments.
    env_override = env.__class__(**{**env.__dict__, "api_base_url": "https://api.dev.local"})
    ctx = script.RunContext(
        env=env_override,
        args=SimpleNamespace(
            dry_run=False,
            models="openai/gpt-frontier:2026-04-01",
            metric_set="1.0.0",
            mode="ad-hoc",
            timeout_minutes=1,
            poll_seconds=0,
            output_dir=str(_REPO_ROOT / ".eval-out"),
            continue_on_gate_block=True,
            api_base_url="https://api.dev.local",
        ),
    )

    captured_posts: list[dict] = []
    captured_gets: list[dict] = []

    def fake_get(url, timeout=None, headers=None):  # noqa: ARG001
        captured_gets.append({"url": url, "headers": headers or {}})
        if url.endswith("/api/eval/health"):
            return _FakeResp(200, {"anonymousAccess": True})
        # poll_status / fetch_scorecard
        if url.endswith("/scorecard"):
            return _FakeResp(200, {"modelVerdicts": []})
        return _FakeResp(200, {"runId": "r-1", "status": "succeeded", "progressPercent": 100})

    def fake_post(url, headers=None, json=None, timeout=None):  # noqa: ARG001
        captured_posts.append({"url": url, "headers": headers or {}})
        return _FakeResp(201, {"runId": "r-1", "status": "queued"})

    monkeypatch.setattr(script.requests, "get", fake_get)
    monkeypatch.setattr(script.requests, "post", fake_post)
    # Skip _resolve_api_base_url's az_json since base url is preset.
    monkeypatch.setattr(script, "_resolve_api_base_url", lambda *a, **kw: None)

    script.stage_execute(ctx)

    # No Authorization header on any HTTP call.
    assert all("Authorization" not in (p["headers"] or {}) for p in captured_posts), captured_posts
    assert all("Authorization" not in (g["headers"] or {}) for g in captured_gets), captured_gets
    # Exactly one POST to /api/eval/runs went out.
    assert any(p["url"].endswith("/api/eval/runs") for p in captured_posts)


def test_stage_execute_sends_dev_bearer_when_anonymous_mode_off(monkeypatch):
    """Inverse of the above: when the API does NOT advertise anonymous mode,
    the script falls back to the dev bearer token (existing behaviour)."""

    script = _load_script()
    env = script.ENVIRONMENTS["dev"]
    env_override = env.__class__(**{**env.__dict__, "api_base_url": "https://api.dev.local"})
    ctx = script.RunContext(
        env=env_override,
        args=SimpleNamespace(
            dry_run=False,
            models="openai/gpt-frontier:2026-04-01",
            metric_set="1.0.0",
            mode="ad-hoc",
            timeout_minutes=1,
            poll_seconds=0,
            output_dir=str(_REPO_ROOT / ".eval-out"),
            continue_on_gate_block=True,
            api_base_url="https://api.dev.local",
        ),
    )

    captured_posts: list[dict] = []

    def fake_get(url, timeout=None, headers=None):  # noqa: ARG001
        if url.endswith("/api/eval/health"):
            return _FakeResp(200, {"anonymousAccess": False})
        if url.endswith("/scorecard"):
            return _FakeResp(200, {"modelVerdicts": []})
        return _FakeResp(200, {"runId": "r-1", "status": "succeeded", "progressPercent": 100})

    def fake_post(url, headers=None, json=None, timeout=None):  # noqa: ARG001
        captured_posts.append({"url": url, "headers": headers or {}})
        return _FakeResp(201, {"runId": "r-1", "status": "queued"})

    monkeypatch.setattr(script.requests, "get", fake_get)
    monkeypatch.setattr(script.requests, "post", fake_post)
    monkeypatch.setattr(script, "_resolve_api_base_url", lambda *a, **kw: None)
    monkeypatch.setenv("USERNAME", "carol")

    script.stage_execute(ctx)

    runs_post = next(p for p in captured_posts if p["url"].endswith("/api/eval/runs"))
    assert runs_post["headers"].get("Authorization", "").startswith("Bearer dev:carol:")
