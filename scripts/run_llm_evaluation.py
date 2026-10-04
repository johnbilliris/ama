#!/usr/bin/env python3
"""run_llm_evaluation.py — automate the manual LLM evaluation workflow.

Executes the five-stage workflow documented in
``docs/llm-evaluation/manual-evaluation-guide.md``:

    1. preflight   — tool + identity + clean-baseline checks
    2. provision   — `az deployment group create` for the eval platform (idempotent)
    3. publish     — validate + upload the disaster dataset, register with the API
    4. execute     — submit a run, poll progress, fetch the scorecard
    5. archive     — sign + upload the evidence bundle
    6. deprovision — force-deprovision orphans + trigger the reconciler

Each stage is independently invocable via the ``--stage`` flag. The default
``--stage all`` chains them. Any non-zero exit code halts the chain. Every
stage emits a single structured-JSON line to stdout for downstream tooling
(CI consumers, ``jq`` pipelines, audit shippers) plus human-readable
``[stage] message`` lines on stderr.

Usage examples:

    # Full end-to-end ad-hoc run, three Foundry models
    python scripts/run_llm_evaluation.py \\
        --stage all \\
        --models openai/gpt-frontier:2026-04-01,openai/gpt-mid:2026-04-01,microsoft/phi-small:2026-04-01

    # Just the preflight + provision (one-time per environment)
    python scripts/run_llm_evaluation.py --stage preflight,provision --env dev

    # Re-archive a run that aborted before sign-off
    python scripts/run_llm_evaluation.py --stage archive --run-id <runId>

    # Dry-run — print every shell command but do not execute
    python scripts/run_llm_evaluation.py --stage all --dry-run

The script is intentionally dependency-light (stdlib + ``requests``) so it
runs on a vanilla operator workstation without ``pip install -e``.
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, NoReturn

try:
    import requests
except ImportError:
    sys.stderr.write(
        "FATAL: 'requests' is required. Install via 'pip install requests'.\n",
    )
    sys.exit(2)


REPO_ROOT = Path(__file__).resolve().parent.parent
DATASET_DIR = REPO_ROOT / "packages" / "eval-dataset" / "data" / "dataset-disaster-core-1.0.0"
DATASET_CASES = DATASET_DIR / "cases.jsonl"
DATASET_MANIFEST = DATASET_DIR / "manifest.json"
EVAL_RUNNER_DOCKERFILE_RELATIVE = Path("apps") / "eval-runner" / "Dockerfile"
EVAL_RUNNER_DOCKERFILE = REPO_ROOT / EVAL_RUNNER_DOCKERFILE_RELATIVE
EVAL_RUNNER_IMAGE_REPOSITORY = "eval-runner"
EVAL_RUNNER_BUILD_CONTEXT_PATHS = [
    EVAL_RUNNER_DOCKERFILE_RELATIVE,
    Path("apps") / "eval-runner" / "pyproject.toml",
    Path("apps") / "eval-runner" / "src",
    Path("packages") / "eval-core" / "pyproject.toml",
    Path("packages") / "eval-core" / "src",
    Path("apps") / "__init__.py",
    Path("apps") / "api" / "__init__.py",
    Path("apps") / "api" / "app" / "__init__.py",
    Path("apps") / "api" / "app" / "repositories" / "__init__.py",
    Path("apps") / "api" / "app" / "repositories" / "eval",
]

API_DOCKERFILE_RELATIVE = Path("apps") / "api" / "Dockerfile"
API_DOCKERFILE = REPO_ROOT / API_DOCKERFILE_RELATIVE
API_IMAGE_REPOSITORY = "ama/api"
API_BUILD_CONTEXT_PATHS = [
    API_DOCKERFILE_RELATIVE,
    Path("apps") / "__init__.py",
    Path("apps") / "api" / "pyproject.toml",
    Path("apps") / "api" / "app",
    Path("apps") / "agents" / "__init__.py",
    Path("apps") / "agents" / "common",
    Path("apps") / "agents" / "communication",
    Path("apps") / "agents" / "evacuation",
    Path("packages"),
]

DEFAULT_MODELS = [
    "gpt-5.4:2026-03-05",
    "gpt-5.4-mini:2026-03-17",
    "gpt-4o-mini:2024-07-18",
    "Phi-4:7",
    "Llama-3.3-70B-Instruct:9",
    "Mistral-Large-3:1",
    "DeepSeek-V3.2:1",
]

TOOL_INSTALL_HINTS = {
    "az": (
        "Install Azure CLI 2.60+ (Windows: winget install -e --id Microsoft.AzureCLI), "
        "restart or refresh your shell PATH, then run az login for the AMA tenant."
    ),
    "git": "Install Git and make sure git is available on PATH.",
    "python": "Install Python 3.11+ and make sure python is available on PATH.",
}

EXIT_OK = 0
EXIT_USAGE = 2
EXIT_PREFLIGHT = 10
EXIT_PROVISION = 11
EXIT_PUBLISH = 12
EXIT_EXECUTE = 13
EXIT_ARCHIVE = 14
EXIT_DEPROVISION = 15
EXIT_GATE_BLOCK = 20


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class EnvironmentConfig:
    name: str
    resource_group: str
    location: str
    runner_job: str
    reconciler_job: str
    bicep_template: Path
    bicep_parameters: Path
    api_base_url: str
    api_resource_uri: str
    storage_account_query: str  # az CLI query that yields the storage account name
    keyvault_name: str
    signing_key: str  # KV key name


ENVIRONMENTS: dict[str, EnvironmentConfig] = {
    "dev": EnvironmentConfig(
        name="dev",
        resource_group="rg-ama-eval-dev",
        location="australiaeast",
        runner_job="caj-eval-runner-dev",
        reconciler_job="caj-eval-reconciler-dev",
        bicep_template=REPO_ROOT / "infra" / "bicep" / "modules" / "eval" / "eval-platform.bicep",
        bicep_parameters=REPO_ROOT / "infra" / "bicep" / "parameters" / "eval-platform.dev.json",
        api_base_url="https://api.ama-dev.example",
        api_resource_uri="api://ama-api-dev",
        storage_account_query="[?starts_with(name, 'stamaevaldev')].name | [0]",
        keyvault_name="kv-ama-eval-dev",
        signing_key="eval-signing-key",
    ),
    "staging": EnvironmentConfig(
        name="staging",
        resource_group="rg-ama-eval-staging",
        location="australiaeast",
        runner_job="caj-eval-runner-staging",
        reconciler_job="caj-eval-reconciler-staging",
        bicep_template=REPO_ROOT / "infra" / "bicep" / "modules" / "eval" / "eval-platform.bicep",
        bicep_parameters=REPO_ROOT / "infra" / "bicep" / "parameters" / "eval-platform.staging.json",
        api_base_url="https://api.ama-staging.example",
        api_resource_uri="api://ama-api-staging",
        storage_account_query="[?starts_with(name, 'stamaevalstaging')].name | [0]",
        keyvault_name="kv-ama-eval-staging",
        signing_key="eval-signing-key",
    ),
}


# ---------------------------------------------------------------------------
# Logging / IO helpers
# ---------------------------------------------------------------------------


@dataclass
class RunContext:
    env: EnvironmentConfig
    args: argparse.Namespace
    state: dict[str, Any] = field(default_factory=dict)

    @property
    def dry_run(self) -> bool:
        return bool(self.args.dry_run)


def log_event(stage: str, level: str, message: str, **extra: Any) -> None:
    """Emit a structured JSON line on stdout and a human line on stderr."""
    payload = {
        "ts": datetime.now(UTC).isoformat(timespec="seconds"),
        "stage": stage,
        "level": level,
        "message": message,
        **extra,
    }
    sys.stdout.write(json.dumps(payload, default=str) + "\n")
    sys.stdout.flush()
    sys.stderr.write(f"[{stage}:{level}] {message}\n")


def fail(stage: str, message: str, code: int, **extra: Any) -> NoReturn:
    log_event(stage, "error", message, **extra)
    sys.exit(code)


def required_tool_missing_message(tool: str) -> str:
    hint = TOOL_INSTALL_HINTS.get(tool)
    if not hint:
        return f"required tool not on PATH: {tool}"
    return f"required tool not on PATH: {tool}. {hint}"


def resolve_command(cmd: list[str]) -> list[str]:
    executable = shutil.which(cmd[0])
    if not executable:
        return cmd
    return [executable, *cmd[1:]]


def resource_group_tags(env: EnvironmentConfig) -> list[str]:
    return [
        f"Environment={env.name}",
        "ManagedBy=Bicep",
        "Project=ama",
        "Owner=ama-eval",
        "feature=030-llm-eval-framework",
        "workload=ama-eval",
    ]


def run_cmd(
    stage: str,
    cmd: list[str],
    *,
    dry_run: bool,
    check: bool = True,
    capture: bool = False,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run a shell command with structured logging."""
    pretty = " ".join(shlex.quote(c) for c in cmd)
    log_event(stage, "info", f"$ {pretty}")
    if dry_run:
        return subprocess.CompletedProcess(cmd, 0, "", "")
    resolved_cmd = resolve_command(cmd)
    merged_env = {
        "PYTHONIOENCODING": "utf-8",
        "PYTHONUTF8": "1",
        **os.environ,
        **(env or {}),
    }
    result = subprocess.run(
        resolved_cmd,
        check=False,
        text=True,
        capture_output=capture,
        env=merged_env,
        encoding="utf-8",
        errors="replace",
    )
    if check and result.returncode != 0:
        _detect_az_reauth_required(stage, result)
        log_event(
            stage,
            "error",
            f"command failed (exit={result.returncode})",
            stdout=result.stdout,
            stderr=result.stderr,
        )
        sys.exit(EXIT_PREFLIGHT)
    return result


_AZ_REAUTH_HINTS = (
    "Continuous access evaluation",
    "TokenCreatedWithOutdatedPolicies",
    "AADSTS50173",  # CAE token policy violation
    "AADSTS70043",  # refresh token expired due to inactivity
    "AADSTS50076",  # MFA required
    "AADSTS530003",  # device management policy violation
    "AADSTS700003",  # MAM/DLP policy violation
    "InteractionRequired",
)


def _detect_az_reauth_required(stage: str, result: subprocess.CompletedProcess[str]) -> None:
    """Surface a clear remediation when Azure CLI hits a CAE / conditional access challenge."""
    blob = f"{result.stdout or ''}\n{result.stderr or ''}"
    if not any(hint in blob for hint in _AZ_REAUTH_HINTS):
        return
    log_event(
        stage,
        "error",
        (
            "Azure CLI access token requires interactive re-authentication "
            "(Continuous Access Evaluation / Conditional Access challenge). "
            "Run: `az logout; az login --scope https://management.azure.com/.default` "
            "and retry."
        ),
        stderr=result.stderr,
    )


# ---------------------------------------------------------------------------
# Azure helpers
# ---------------------------------------------------------------------------


def az_json(stage: str, args: list[str], dry_run: bool) -> Any:
    """Run ``az`` and parse JSON. In dry-run mode returns ``None``."""
    if dry_run:
        log_event(stage, "info", f"[dry-run] az {' '.join(args)}")
        return None
    res = run_cmd(stage, ["az", *args, "-o", "json"], dry_run=False, capture=True)
    return json.loads(res.stdout) if res.stdout else None


def get_access_token(stage: str, resource_uri: str, dry_run: bool, *, optional: bool = False) -> str | None:
    if dry_run:
        return "DRY-RUN-TOKEN"
    res = run_cmd(
        stage,
        ["az", "account", "get-access-token", "--resource", resource_uri, "--query", "accessToken", "-o", "tsv"],
        dry_run=False,
        capture=True,
        check=not optional,
    )
    if optional and res.returncode != 0:
        log_event(
            stage,
            "warn",
            "could not acquire optional Azure access token; skipping API registration",
            resource_uri=resource_uri,
            stderr=res.stderr,
        )
        return None
    token = res.stdout.strip()
    if not token:
        if optional:
            log_event(
                stage,
                "warn",
                "optional Azure access token was empty; skipping API registration",
                resource_uri=resource_uri,
            )
            return None
        fail(stage, "could not acquire Azure access token", EXIT_PREFLIGHT)
    return token


def deploy_eval_platform(
    ctx: RunContext,
    stage: str,
    *,
    deploy_container_jobs: bool,
    deploy_api: bool = False,
    extra_parameters: list[str] | None = None,
) -> Any:
    parameters: list[str] = [
        f"@{ctx.env.bicep_parameters}",
        f"deployContainerJobs={str(deploy_container_jobs).lower()}",
        f"deployApi={str(deploy_api).lower()}",
    ]
    if extra_parameters:
        parameters.extend(extra_parameters)
    res = run_cmd(
        stage,
        [
            "az",
            "deployment",
            "group",
            "create",
            "--resource-group",
            ctx.env.resource_group,
            "--template-file",
            str(ctx.env.bicep_template),
            "--parameters",
            *parameters,
            "-o",
            "json",
        ],
        dry_run=ctx.dry_run,
        capture=True,
    )
    if ctx.dry_run:
        return None
    if not res.stdout:
        fail(stage, "deployment produced no output", EXIT_PROVISION)
    return json.loads(res.stdout)


def deployment_output(deployment: Any, name: str, stage: str) -> str:
    try:
        value = deployment["properties"]["outputs"][name]["value"]
    except KeyError:
        fail(stage, f"deployment output missing: {name}", EXIT_PROVISION)
    if not isinstance(value, str) or not value.strip():
        fail(stage, f"deployment output empty: {name}", EXIT_PROVISION)
    return value


_DEV_STORAGE_ROLE = "Storage Blob Data Contributor"
_DEV_RBAC_PROPAGATION_SECONDS = 60


def grant_dev_storage_access(ctx: RunContext, stage: str, storage_account_name: str) -> bool:
    """Grant the current Azure CLI principal Storage Blob Data Contributor on the dev
    storage account so an operator running this script locally can upload datasets and
    archive evidence with ``--auth-mode login``. No-op outside dev. Returns True when a
    new role assignment was created (caller should wait for RBAC propagation)."""
    if ctx.env.name != "dev":
        return False
    if ctx.dry_run:
        log_event(stage, "info", f"[dry-run] grant {_DEV_STORAGE_ROLE} on {storage_account_name}")
        return False

    account = az_json(stage, ["account", "show", "--query", "{id:id,userType:user.type,user:user.name}"], ctx.dry_run)
    subscription_id = account.get("id") if isinstance(account, dict) else None
    user_type = (account.get("userType") if isinstance(account, dict) else None) or "user"
    user_name = account.get("user") if isinstance(account, dict) else None
    if not subscription_id:
        log_event(stage, "warn", "could not resolve subscription id; skipping dev storage role grant")
        return False

    if user_type == "servicePrincipal":
        principal_id = az_json(stage, ["ad", "sp", "show", "--id", str(user_name), "--query", "id"], ctx.dry_run)
        principal_type = "ServicePrincipal"
    else:
        principal_id = az_json(stage, ["ad", "signed-in-user", "show", "--query", "id"], ctx.dry_run)
        principal_type = "User"
    if not principal_id:
        log_event(stage, "warn", "could not resolve current principal id; skipping dev storage role grant")
        return False

    scope = (
        f"/subscriptions/{subscription_id}/resourceGroups/{ctx.env.resource_group}"
        f"/providers/Microsoft.Storage/storageAccounts/{storage_account_name}"
    )
    existing = az_json(
        stage,
        [
            "role",
            "assignment",
            "list",
            "--assignee",
            str(principal_id),
            "--role",
            _DEV_STORAGE_ROLE,
            "--scope",
            scope,
            "--query",
            "[].id",
        ],
        ctx.dry_run,
    )
    if existing:
        log_event(stage, "info", f"{_DEV_STORAGE_ROLE} already granted on {storage_account_name}")
        return False

    res = run_cmd(
        stage,
        [
            "az",
            "role",
            "assignment",
            "create",
            "--assignee-object-id",
            str(principal_id),
            "--assignee-principal-type",
            principal_type,
            "--role",
            _DEV_STORAGE_ROLE,
            "--scope",
            scope,
        ],
        dry_run=False,
        capture=True,
        check=False,
    )
    if res.returncode == 0:
        log_event(
            stage,
            "ok",
            f"granted {_DEV_STORAGE_ROLE} to {principal_type} {principal_id} on {storage_account_name}",
        )
        return True
    if "RoleAssignmentExists" in res.stderr or "already exists" in res.stderr.lower():
        log_event(stage, "info", f"{_DEV_STORAGE_ROLE} already granted on {storage_account_name}")
        return False
    fail(
        stage,
        f"failed to grant {_DEV_STORAGE_ROLE} on {storage_account_name}",
        EXIT_PROVISION if stage == "provision" else EXIT_PUBLISH,
        stderr=res.stderr,
    )


def wait_for_rbac_propagation(stage: str, granted: bool) -> None:
    if not granted:
        return
    log_event(stage, "info", f"waiting {_DEV_RBAC_PROPAGATION_SECONDS}s for RBAC propagation")
    time.sleep(_DEV_RBAC_PROPAGATION_SECONDS)


def resolve_storage_account(ctx: RunContext, stage: str, exit_code: int) -> str:
    storage = az_json(
        stage,
        ["storage", "account", "list", "-g", ctx.env.resource_group, "--query", ctx.env.storage_account_query],
        ctx.dry_run,
    )
    if not storage:
        fail(stage, "could not resolve storage account", exit_code)
    return str(storage)


def _prepare_build_context(build_root: Path, paths: list[Path]) -> Path:
    for relative_path in paths:
        source = REPO_ROOT / relative_path
        destination = build_root / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        if source.is_dir():
            shutil.copytree(
                source,
                destination,
                ignore=shutil.ignore_patterns(
                    "__pycache__",
                    "*.pyc",
                    "*.pyo",
                    "*.egg-info",
                    ".pytest_cache",
                    "node_modules",
                    ".next",
                ),
            )
        elif source.exists():
            shutil.copy2(source, destination)
    return build_root


def prepare_eval_runner_build_context(build_root: Path) -> Path:
    return _prepare_build_context(build_root, EVAL_RUNNER_BUILD_CONTEXT_PATHS)


def prepare_api_build_context(build_root: Path) -> Path:
    return _prepare_build_context(build_root, API_BUILD_CONTEXT_PATHS)


def _run_acr_build(
    ctx: RunContext,
    stage: str,
    container_registry_name: str,
    image: str,
    dockerfile_relative: Path,
    build_context: Path,
) -> None:
    result = run_cmd(
        stage,
        [
            "az",
            "acr",
            "build",
            "--registry",
            container_registry_name,
            "--image",
            image,
            "--file",
            str(build_context / dockerfile_relative),
            str(build_context),
        ],
        dry_run=ctx.dry_run,
        capture=True,
        check=False,
    )
    if result.returncode != 0:
        # ACR streaming output may have UnicodeEncodeError'd in the az CLI
        # subprocess even though the underlying ACR run succeeded server-side.
        # Verify by polling task status before failing.
        if not ctx.dry_run and _last_acr_run_succeeded(stage, container_registry_name):
            log_event(
                stage,
                "warn",
                f"az acr build wrapper exited {result.returncode} but ACR task succeeded; continuing",
            )
            return
        fail(
            stage,
            f"az acr build failed (exit={result.returncode})",
            EXIT_PROVISION,
            stdout=result.stdout,
            stderr=result.stderr,
        )


_ACR_TASK_STATUS_QUERY = [
    "az",
    "acr",
    "task",
    "list-runs",
    "--registry",
    "{registry}",
    "--top",
    "1",
    "--query",
    "[0].status",
    "-o",
    "tsv",
]


def _acr_task_status_cmd(registry: str) -> list[str]:
    return [arg.replace("{registry}", registry) for arg in _ACR_TASK_STATUS_QUERY]


def _last_acr_run_succeeded(stage: str, registry: str) -> bool:
    res = run_cmd(stage, _acr_task_status_cmd(registry), dry_run=False, capture=True, check=False)
    status = (res.stdout or "").strip()
    if status in {"Running", "Queued"}:
        log_event(stage, "info", f"waiting for ACR task to finish (status={status})...")
        for _ in range(60):
            time.sleep(15)
            res = run_cmd(stage, _acr_task_status_cmd(registry), dry_run=False, capture=True, check=False)
            status = (res.stdout or "").strip()
            if status not in {"Running", "Queued"}:
                break
    log_event(stage, "info", f"ACR task final status: {status}")
    return status == "Succeeded"


def run_eval_runner_acr_build(
    ctx: RunContext,
    stage: str,
    container_registry_name: str,
    build_context: Path,
) -> None:
    _run_acr_build(
        ctx,
        stage,
        container_registry_name,
        f"{EVAL_RUNNER_IMAGE_REPOSITORY}:{ctx.env.name}",
        EVAL_RUNNER_DOCKERFILE_RELATIVE,
        build_context,
    )


def build_eval_runner_image(ctx: RunContext, stage: str, container_registry_name: str) -> None:
    if ctx.dry_run:
        run_eval_runner_acr_build(ctx, stage, container_registry_name, Path("<minimal-eval-runner-context>"))
        return

    with tempfile.TemporaryDirectory(prefix="ama-eval-acr-build-") as build_dir:
        build_context = prepare_eval_runner_build_context(Path(build_dir))
        run_eval_runner_acr_build(ctx, stage, container_registry_name, build_context)


def build_api_image(ctx: RunContext, stage: str, container_registry_name: str) -> None:
    image = f"{API_IMAGE_REPOSITORY}:{ctx.env.name}"
    if ctx.dry_run:
        _run_acr_build(
            ctx,
            stage,
            container_registry_name,
            image,
            API_DOCKERFILE_RELATIVE,
            Path("<minimal-api-context>"),
        )
        return

    with tempfile.TemporaryDirectory(prefix="ama-api-acr-build-") as build_dir:
        build_context = prepare_api_build_context(Path(build_dir))
        _run_acr_build(ctx, stage, container_registry_name, image, API_DOCKERFILE_RELATIVE, build_context)


def _is_existing_blob_error(result: subprocess.CompletedProcess[str]) -> bool:
    output = f"{result.stdout}\n{result.stderr}".lower()
    return "blobalreadyexists" in output or "already exists" in output


def handle_blob_upload_result(
    stage: str,
    result: subprocess.CompletedProcess[str],
    blob_name: str,
    exit_code: int,
) -> None:
    if result.returncode == 0:
        return
    if _is_existing_blob_error(result):
        log_event(stage, "warn", "blob already exists; immutable artefact left unchanged", blob=blob_name)
        return
    fail(
        stage,
        f"blob upload failed: {blob_name}",
        exit_code,
        stdout=result.stdout,
        stderr=result.stderr,
    )


# ---------------------------------------------------------------------------
# Stage 1 — preflight
# ---------------------------------------------------------------------------


def stage_preflight(ctx: RunContext) -> None:
    stage = "preflight"
    log_event(stage, "info", "starting preflight checks")

    for tool, version_arg in [("python", "--version"), ("az", "version"), ("git", "--version")]:
        try:
            run_cmd(stage, [tool, version_arg], dry_run=ctx.dry_run, capture=True)
        except FileNotFoundError:
            fail(stage, required_tool_missing_message(tool), EXIT_PREFLIGHT, tool=tool)

    if not ctx.dry_run:
        acct = az_json(stage, ["account", "show"], ctx.dry_run)
        if not acct or "id" not in acct:
            fail(stage, "az login required", EXIT_PREFLIGHT)
        log_event(stage, "info", f"azure subscription: {acct['name']} ({acct['id']})")

    if ctx.args.skip_baseline:
        log_event(stage, "warn", "--skip-baseline set; not running pytest/ruff/bicep")
    else:
        run_cmd(
            stage,
            [
                "python",
                "-m",
                "pytest",
                "tests/unit/eval/",
                "packages/eval-core/tests/",
                "packages/eval-dataset/tests/",
                "-q",
            ],
            dry_run=ctx.dry_run,
            capture=True,
        )
        run_cmd(
            stage,
            [
                "ruff",
                "check",
                "packages/eval-core/",
                "packages/eval-dataset/",
                "apps/eval-runner/",
                "tests/unit/eval/",
            ],
            dry_run=ctx.dry_run,
            capture=True,
        )
        run_cmd(
            stage,
            ["az", "bicep", "build", "--file", str(ctx.env.bicep_template)],
            dry_run=ctx.dry_run,
            capture=True,
        )

    log_event(stage, "ok", "preflight passed")


# ---------------------------------------------------------------------------
# Stage 2 — provision
# ---------------------------------------------------------------------------


def stage_provision(ctx: RunContext) -> None:
    stage = "provision"
    if not ctx.env.bicep_template.exists() and not ctx.dry_run:
        fail(stage, f"bicep template missing: {ctx.env.bicep_template}", EXIT_PROVISION)
    if not ctx.env.bicep_parameters.exists() and not ctx.dry_run:
        fail(stage, f"bicep parameters missing: {ctx.env.bicep_parameters}", EXIT_PROVISION)
    if not EVAL_RUNNER_DOCKERFILE.exists() and not ctx.dry_run:
        fail(stage, f"eval runner Dockerfile missing: {EVAL_RUNNER_DOCKERFILE}", EXIT_PROVISION)
    if not API_DOCKERFILE.exists() and not ctx.dry_run:
        fail(stage, f"AMA api Dockerfile missing: {API_DOCKERFILE}", EXIT_PROVISION)

    run_cmd(
        stage,
        [
            "az",
            "group",
            "create",
            "--name",
            ctx.env.resource_group,
            "--location",
            ctx.env.location,
            "--tags",
            *resource_group_tags(ctx.env),
            "--output",
            "none",
        ],
        dry_run=ctx.dry_run,
    )
    base_deployment = deploy_eval_platform(ctx, stage, deploy_container_jobs=False, deploy_api=False)
    container_registry_name = (
        "<containerRegistryName>" if ctx.dry_run else deployment_output(base_deployment, "containerRegistryName", stage)
    )
    build_eval_runner_image(ctx, stage, container_registry_name)
    build_api_image(ctx, stage, container_registry_name)

    api_extra_params: list[str] = []
    if getattr(ctx.args, "api_entra_audience", None):
        api_extra_params.append(f"entraAudience={ctx.args.api_entra_audience}")
    api_deployment = deploy_eval_platform(
        ctx,
        stage,
        deploy_container_jobs=True,
        deploy_api=True,
        extra_parameters=api_extra_params,
    )
    api_fqdn = "<apiFqdn>" if ctx.dry_run else deployment_output(api_deployment, "apiFqdn", stage)
    if not ctx.dry_run and api_fqdn:
        ctx.state["api_fqdn"] = api_fqdn
        _persist_api_base_url(ctx, api_fqdn)
        log_event(stage, "ok", f"API ingress: https://{api_fqdn}")

    if ctx.env.name == "dev":
        storage_account_name = (
            "<storageAccountName>" if ctx.dry_run else resolve_storage_account(ctx, stage, EXIT_PROVISION)
        )
        granted = grant_dev_storage_access(ctx, stage, storage_account_name)
        wait_for_rbac_propagation(stage, granted)

    if not ctx.dry_run:
        provisioning = az_json(
            stage,
            [
                "containerapp",
                "job",
                "show",
                "-n",
                ctx.env.runner_job,
                "-g",
                ctx.env.resource_group,
                "--query",
                "properties.provisioningState",
            ],
            ctx.dry_run,
        )
        if provisioning != "Succeeded":
            fail(stage, f"runner job not ready: {provisioning}", EXIT_PROVISION)

        if api_fqdn:
            wait_for_api_health(ctx, stage, api_fqdn)

        verify_foundry_deployments(ctx, stage)

    log_event(stage, "ok", "platform provisioned")


def resolve_foundry_account(ctx: RunContext, stage: str) -> str | None:
    """Look up the eval Foundry account name from the Bicep deployment outputs.

    All eval Foundry resources live in ``ctx.env.resource_group`` (same RG as the
    rest of the eval platform). Returns ``None`` when the deployment hasn't run
    yet or in dry-run mode.
    """
    cached = ctx.state.get("foundry_account")
    if cached:
        return str(cached)
    if ctx.dry_run:
        return None
    name = az_json(
        stage,
        [
            "deployment",
            "group",
            "show",
            "--resource-group",
            ctx.env.resource_group,
            "--name",
            "eval-platform",
            "--query",
            "properties.outputs.foundryAccountName.value",
        ],
        ctx.dry_run,
    )
    if isinstance(name, str) and name:
        ctx.state["foundry_account"] = name
        return name
    return None


def verify_foundry_deployments(ctx: RunContext, stage: str) -> None:
    """Confirm the eval Foundry account exists and the expected model deployments are present.

    Pulls the deployment list from the eval-platform deployment outputs (``foundryAccountName`` +
    ``foundryDeploymentNames``) and uses ``az cognitiveservices account deployment list`` to
    assert each one is in the ``Succeeded`` provisioning state.
    """
    foundry_account = resolve_foundry_account(ctx, stage)
    expected_csv = az_json(
        stage,
        [
            "deployment",
            "group",
            "show",
            "--resource-group",
            ctx.env.resource_group,
            "--name",
            "eval-platform",
            "--query",
            "properties.outputs.foundryDeploymentNames.value",
        ],
        ctx.dry_run,
    )
    if not foundry_account or not isinstance(expected_csv, str):
        log_event(stage, "warn", "foundry deployment outputs unavailable; skipping verification")
        return
    expected = [n for n in expected_csv.split(",") if n]
    actual = az_json(
        stage,
        [
            "cognitiveservices",
            "account",
            "deployment",
            "list",
            "-g",
            ctx.env.resource_group,
            "-n",
            str(foundry_account),
            "--query",
            "[].{name:name,state:properties.provisioningState}",
        ],
        ctx.dry_run,
    )
    actual_map = {item["name"]: item["state"] for item in (actual or []) if isinstance(item, dict)}
    missing = [n for n in expected if n not in actual_map]
    failed = [n for n, s in actual_map.items() if s != "Succeeded"]
    if missing or failed:
        fail(
            stage,
            "foundry deployments not all ready",
            EXIT_PROVISION,
            missing=missing,
            failed=failed,
            actual=actual_map,
        )
    log_event(stage, "ok", f"foundry deployments ready: {sorted(actual_map)}")


def wait_for_api_health(ctx: RunContext, stage: str, fqdn: str, *, timeout_seconds: int = 300) -> None:
    url = f"https://{fqdn}/api/health"
    deadline = time.monotonic() + timeout_seconds
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code < 500:
                log_event(stage, "ok", f"API healthy ({resp.status_code}) at {url}")
                return
            last_error = RuntimeError(f"status={resp.status_code}")
        except requests.exceptions.RequestException as exc:
            last_error = exc
        time.sleep(10)
    fail(stage, f"API health check timed out: {url}", EXIT_PROVISION, last_error=str(last_error))


# ---------------------------------------------------------------------------
# Stage 3 — publish dataset
# ---------------------------------------------------------------------------


def detect_anonymous_mode(ctx: RunContext, stage: str) -> bool:
    """Probe ``GET /api/eval/health`` to discover whether the API has
    FR-022a dev-only anonymous access enabled.

    The API exposes ``anonymousAccess: bool`` on its eval health endpoint
    when ``ENVIRONMENT=dev`` and ``EVAL_ALLOW_ANONYMOUS=1``. When that flag
    is true, callers MUST omit the ``Authorization`` header so the role
    guard takes the synthetic anonymous principal path. Outside dev (or if
    the probe fails) we fall back to the dev bearer token / Entra token
    flow — behaviour is unchanged.
    """

    if ctx.env.name != "dev":
        return False
    cached = ctx.state.get("eval_anonymous_mode")
    if cached is not None:
        return bool(cached)
    base = ctx.env.api_base_url
    if not base:
        return False
    url = f"{base.rstrip('/')}/api/eval/health"
    try:
        resp = requests.get(url, timeout=10)
    except requests.exceptions.RequestException as exc:
        log_event(
            stage,
            "warn",
            "anonymous-mode probe failed; will fall back to dev bearer token",
            url=url,
            error=str(exc),
        )
        ctx.state["eval_anonymous_mode"] = False
        return False
    if resp.status_code != 200:
        log_event(
            stage,
            "warn",
            f"anonymous-mode probe returned {resp.status_code}; falling back to dev bearer token",
            url=url,
        )
        ctx.state["eval_anonymous_mode"] = False
        return False
    try:
        body = resp.json()
    except ValueError:
        ctx.state["eval_anonymous_mode"] = False
        return False
    enabled = bool(body.get("anonymousAccess"))
    ctx.state["eval_anonymous_mode"] = enabled
    if enabled:
        log_event(
            stage,
            "info",
            "AMA API has anonymous mode ON (FR-022a) — Authorization header will be omitted",
            api_base_url=base,
        )
    return enabled


def get_eval_token(ctx: RunContext, stage: str) -> str | None:
    """Return a bearer token for the AMA eval API, or ``None`` when the API
    has FR-022a dev-only anonymous mode enabled.

    Behaviour:

    * **dev with anonymous mode on**: return ``None`` so callers omit the
      ``Authorization`` header. The API's role guard returns a synthetic
      anonymous principal scoped to the synthetic dev dataset.
    * **dev with anonymous mode off / probe failed**: mint the
      deterministic ``dev:<sub>:<roles>`` token the API's role guard
      accepts when ``EVAL_ALLOW_DEV_TOKENS=1``.
    * **staging / production**: acquire a real Entra ID JWT for the
      configured ``api_resource_uri`` — unchanged.
    """

    if ctx.env.name == "dev":
        if detect_anonymous_mode(ctx, stage):
            return None
        sub = os.environ.get("USERNAME") or os.environ.get("USER") or "cli"
        return f"dev:{sub}:Eval.Operator,Eval.Viewer,Eval.Auditor"
    token = get_access_token(stage, ctx.env.api_resource_uri, ctx.dry_run)
    if token is None:
        fail(stage, "could not acquire AMA API access token", EXIT_EXECUTE)
    return token


def _eval_request_headers(token: str | None, *, content_type: str | None = None) -> dict[str, str]:
    """Build HTTP headers for AMA eval API calls.

    Omits ``Authorization`` when ``token is None`` so FR-022a anonymous mode
    stays anonymous (the API role guard requires the absence of the header
    to take the anonymous-principal branch).
    """

    headers: dict[str, str] = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if content_type:
        headers["Content-Type"] = content_type
    return headers


def _publish_dataset_payload() -> dict[str, Any]:
    return json.loads(DATASET_MANIFEST.read_text(encoding="utf-8"))


def stage_publish(ctx: RunContext) -> None:
    stage = "publish"
    _resolve_api_base_url(ctx, stage)
    if not DATASET_CASES.exists():
        fail(stage, f"dataset cases missing: {DATASET_CASES}", EXIT_PUBLISH)
    if not DATASET_MANIFEST.exists():
        fail(stage, f"dataset manifest missing: {DATASET_MANIFEST}", EXIT_PUBLISH)

    run_cmd(
        stage,
        ["python", "-m", "pytest", "packages/eval-dataset/tests/", "-q"],
        dry_run=ctx.dry_run,
        capture=True,
    )

    if ctx.dry_run:
        log_event(stage, "info", "[dry-run] skipping blob upload + API register")
        return

    storage = resolve_storage_account(ctx, stage, EXIT_PUBLISH)
    log_event(stage, "info", f"storage account: {storage}")
    granted = grant_dev_storage_access(ctx, stage, storage)
    wait_for_rbac_propagation(stage, granted)

    for src, blob_name in [
        (DATASET_CASES, "disaster-response-core/1.0.0/cases.jsonl"),
        (DATASET_MANIFEST, "disaster-response-core/1.0.0/manifest.json"),
    ]:
        upload = run_cmd(
            stage,
            [
                "az",
                "storage",
                "blob",
                "upload",
                "--account-name",
                str(storage),
                "--container-name",
                "datasets",
                "--name",
                blob_name,
                "--file",
                str(src),
                "--auth-mode",
                "login",
                "--overwrite",
                "false",
            ],
            dry_run=ctx.dry_run,
            check=False,
            capture=True,
        )
        handle_blob_upload_result(stage, upload, blob_name, EXIT_PUBLISH)

    if ctx.args.skip_api_register:
        log_event(stage, "warn", "--skip-api-register set; dataset uploaded but API registration skipped")
        return

    token = get_eval_token(ctx, stage)

    manifest = _publish_dataset_payload()
    dataset_id = manifest.get("datasetId", "disaster-response-core")
    try:
        resp = requests.post(
            f"{ctx.env.api_base_url}/api/eval/datasets/{dataset_id}/versions",
            headers=_eval_request_headers(token, content_type="application/json"),
            json=manifest,
            timeout=60,
        )
    except requests.exceptions.ConnectionError as exc:
        if ctx.env.name == "dev":
            log_event(
                stage,
                "warn",
                "AMA API unreachable; dataset uploaded but registration skipped",
                api_base_url=ctx.env.api_base_url,
                error=str(exc),
            )
            return
        fail(stage, f"AMA API unreachable: {exc}", EXIT_PUBLISH, api_base_url=ctx.env.api_base_url)
    if resp.status_code not in (200, 201, 409):
        fail(
            stage,
            f"dataset register failed: {resp.status_code}",
            EXIT_PUBLISH,
            body=resp.text,
        )
    log_event(stage, "ok", "dataset registered", status_code=resp.status_code)


# ---------------------------------------------------------------------------
# Stage 4 — execute run
# ---------------------------------------------------------------------------


def _parse_models(spec: str) -> list[dict[str, str]]:
    refs: list[dict[str, str]] = []
    for raw in (s.strip() for s in spec.split(",") if s.strip()):
        if ":" not in raw:
            raise ValueError(f"model ref must be 'modelId:version' (got '{raw}')")
        model_id, version = raw.rsplit(":", 1)
        refs.append({"modelId": model_id, "version": version})
    if not refs:
        raise ValueError("no models supplied")
    return refs


def stage_execute(ctx: RunContext) -> None:
    stage = "execute"
    _resolve_api_base_url(ctx, stage)
    model_refs = _parse_models(ctx.args.models or ",".join(DEFAULT_MODELS))
    manifest = _publish_dataset_payload()
    dataset_id = manifest.get("datasetId", "disaster-response-core")
    dataset_version = manifest.get("version", "1.0.0")

    body = {
        "datasetId": dataset_id,
        "datasetVersion": dataset_version,
        "models": model_refs,
        "metricSetVersion": ctx.args.metric_set,
        "policyVersion": "1.0.0",
        "mode": ctx.args.mode,
        "estimatedCostAud": 0.0,
        "estimatedDurationMinutes": 60,
    }
    max_cases = getattr(ctx.args, "max_cases", None)
    if max_cases:
        body["datasetSubset"] = {"maxCases": int(max_cases)}

    if ctx.dry_run:
        log_event(stage, "info", "[dry-run] would POST /api/eval/runs", body=body)
        ctx.state["run_id"] = "dry-run-runid"
        return

    token = get_eval_token(ctx, stage)
    resp = requests.post(
        f"{ctx.env.api_base_url}/api/eval/runs",
        headers=_eval_request_headers(token, content_type="application/json"),
        json=body,
        timeout=60,
    )
    if resp.status_code >= 400:
        fail(stage, f"run submission failed: {resp.status_code}", EXIT_EXECUTE, body=resp.text)
    run = resp.json()
    run_id = run["runId"]
    ctx.state["run_id"] = run_id
    log_event(
        stage,
        "info",
        "run submitted",
        run_id=run_id,
        status=run.get("status"),
    )

    poll_status(ctx, stage, token, run_id)
    fetch_scorecard(ctx, stage, token, run_id)


def poll_status(ctx: RunContext, stage: str, token: str | None, run_id: str) -> None:
    deadline = time.monotonic() + ctx.args.timeout_minutes * 60
    interval = ctx.args.poll_seconds
    while time.monotonic() < deadline:
        resp = requests.get(
            f"{ctx.env.api_base_url}/api/eval/runs/{run_id}",
            headers=_eval_request_headers(token),
            timeout=30,
        )
        if resp.status_code >= 400:
            log_event(stage, "warn", f"poll status {resp.status_code}, retrying")
            time.sleep(interval)
            continue
        run = resp.json()
        status = run.get("status")
        progress = run.get("progressPercent")
        log_event(stage, "info", f"run {run_id} status={status} progress={progress}%")
        if status in ("succeeded", "failed", "cancelled"):
            ctx.state["run_final_status"] = status
            ctx.state["run_terminal"] = run.get("infrastructureLifecycle", {}).get(
                "terminalState",
            )
            if status != "succeeded":
                fail(stage, f"run terminated as '{status}'", EXIT_EXECUTE, run=run)
            return
        time.sleep(interval)
    fail(stage, f"timeout waiting for run {run_id}", EXIT_EXECUTE)


def fetch_scorecard(ctx: RunContext, stage: str, token: str | None, run_id: str) -> None:
    resp = requests.get(
        f"{ctx.env.api_base_url}/api/eval/runs/{run_id}/scorecard",
        headers=_eval_request_headers(token),
        timeout=60,
    )
    if resp.status_code >= 400:
        fail(stage, f"scorecard fetch failed: {resp.status_code}", EXIT_EXECUTE, body=resp.text)
    scorecard = resp.json()

    out_dir = Path(ctx.args.output_dir) / run_id
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "scorecard.json").write_text(
        json.dumps(scorecard, indent=2),
        encoding="utf-8",
    )

    verdicts = scorecard.get("modelVerdicts", [])
    log_event(stage, "info", "scorecard fetched", model_verdicts=verdicts)
    blocked = [v for v in verdicts if v.get("overallVerdict") not in (None, "pass", "allow")]
    if blocked and not ctx.args.continue_on_gate_block:
        log_event(stage, "error", "gate blocked one or more models", blocked=blocked)
        sys.exit(EXIT_GATE_BLOCK)
    log_event(stage, "ok", f"scorecard saved to {out_dir / 'scorecard.json'}")


# ---------------------------------------------------------------------------
# Stage 5 — archive evidence
# ---------------------------------------------------------------------------


def stage_archive(ctx: RunContext) -> None:
    stage = "archive"
    _resolve_api_base_url(ctx, stage)
    run_id = ctx.args.run_id or ctx.state.get("run_id")
    if not run_id:
        fail(stage, "no run id available; pass --run-id", EXIT_ARCHIVE)

    out_dir = Path(ctx.args.output_dir) / run_id
    out_dir.mkdir(parents=True, exist_ok=True)
    bundle_path = out_dir / "evidence.tar"

    run_cmd(
        stage,
        [
            "python",
            "-m",
            "ama_eval.evidence",
            "--run-id",
            run_id,
            "--output",
            str(bundle_path),
            "--sign-with-keyvault",
            f"{ctx.env.keyvault_name}/{ctx.env.signing_key}",
        ],
        dry_run=ctx.dry_run,
        check=False,
    )

    if ctx.dry_run:
        return

    storage = resolve_storage_account(ctx, stage, EXIT_ARCHIVE)
    granted = grant_dev_storage_access(ctx, stage, storage)
    wait_for_rbac_propagation(stage, granted)

    upload = run_cmd(
        stage,
        [
            "az",
            "storage",
            "blob",
            "upload",
            "--account-name",
            str(storage),
            "--container-name",
            "audit-archive",
            "--name",
            f"runs/{run_id}/evidence.tar",
            "--file",
            str(bundle_path),
            "--auth-mode",
            "login",
            "--overwrite",
            "false",
        ],
        dry_run=ctx.dry_run,
        check=False,
        capture=True,
    )
    handle_blob_upload_result(stage, upload, f"runs/{run_id}/evidence.tar", EXIT_ARCHIVE)
    log_event(stage, "ok", f"evidence archived for {run_id}")


# ---------------------------------------------------------------------------
# Stage 6 — deprovision
# ---------------------------------------------------------------------------


def stage_deprovision(ctx: RunContext) -> None:
    stage = "deprovision"
    run_id = ctx.args.run_id or ctx.state.get("run_id")
    foundry_account = resolve_foundry_account(ctx, stage)
    if run_id and foundry_account:
        deps = (
            az_json(
                stage,
                [
                    "cognitiveservices",
                    "account",
                    "deployment",
                    "list",
                    "-n",
                    foundry_account,
                    "-g",
                    ctx.env.resource_group,
                    "--query",
                    f"[?tags.runId=='{run_id}'].name",
                ],
                ctx.dry_run,
            )
            or []
        )
        for dep in deps:
            run_cmd(
                stage,
                [
                    "az",
                    "cognitiveservices",
                    "account",
                    "deployment",
                    "delete",
                    "-n",
                    foundry_account,
                    "-g",
                    ctx.env.resource_group,
                    "--deployment-name",
                    dep,
                ],
                dry_run=ctx.dry_run,
                check=False,
            )
            log_event(stage, "info", f"deleted run-scoped deployment {dep}")
    elif not run_id:
        log_event(stage, "warn", "no run id; skipping run-scoped cleanup")
    elif not foundry_account:
        log_event(
            stage,
            "warn",
            "could not resolve eval Foundry account from deployment outputs; skipping run-scoped cleanup",
        )

    run_cmd(
        stage,
        [
            "az",
            "containerapp",
            "job",
            "start",
            "-n",
            ctx.env.reconciler_job,
            "-g",
            ctx.env.resource_group,
        ],
        dry_run=ctx.dry_run,
        check=False,
    )

    if not ctx.dry_run and foundry_account:
        orphans = (
            az_json(
                stage,
                [
                    "cognitiveservices",
                    "account",
                    "deployment",
                    "list",
                    "-n",
                    foundry_account,
                    "-g",
                    ctx.env.resource_group,
                    "--query",
                    "[?tags.purpose=='ama-eval' && properties.provisioningState!='Succeeded']",
                ],
                ctx.dry_run,
            )
            or []
        )
        if orphans:
            fail(
                stage,
                f"{len(orphans)} orphans remain after reconciler",
                EXIT_DEPROVISION,
                orphans=orphans,
            )

    log_event(stage, "ok", "deprovision complete")


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------


STAGES = {
    "preflight": stage_preflight,
    "provision": stage_provision,
    "publish": stage_publish,
    "execute": stage_execute,
    "archive": stage_archive,
    "deprovision": stage_deprovision,
}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="run_llm_evaluation",
        description="Automate the AMA LLM evaluation manual workflow.",
    )
    p.add_argument(
        "--stage",
        default="all",
        help="Comma-separated stages to run (preflight,provision,publish,execute,archive,deprovision) "
        "or 'all'. Default: all",
    )
    p.add_argument("--env", default="dev", choices=sorted(ENVIRONMENTS), help="target environment")
    p.add_argument(
        "--mode",
        default="ad-hoc",
        choices=["pr-fast-subset", "ad-hoc", "progressive-delivery-full"],
    )
    p.add_argument("--models", help="comma-separated 'modelId:version' refs")
    p.add_argument(
        "--max-cases",
        type=int,
        default=int(os.environ.get("AMA_EVAL_MAX_CASES", "25")),
        help="cap the dataset subset for this run (default 25 to bound dev cost; pass 0 for no cap)",
    )
    p.add_argument("--metric-set", default="disaster-core-v1")
    p.add_argument("--judge-set", default="judge-gpt4o-v1")
    p.add_argument("--notes", default=None)
    p.add_argument("--run-id", help="reuse an existing run id (archive/deprovision)")
    p.add_argument("--output-dir", default=".eval-out")
    p.add_argument("--poll-seconds", type=int, default=30)
    p.add_argument("--timeout-minutes", type=int, default=540)  # 9 h cap
    p.add_argument("--skip-baseline", action="store_true", help="skip pytest/ruff/bicep checks")
    p.add_argument(
        "--skip-api-register",
        action="store_true",
        help="upload dataset artefacts but skip API dataset registration",
    )
    p.add_argument(
        "--continue-on-gate-block",
        action="store_true",
        help="archive + deprovision even if gate verdict is block",
    )
    p.add_argument("--dry-run", action="store_true", help="print commands but do not execute")
    p.add_argument(
        "--api-base-url",
        default=os.environ.get("AMA_API_BASE_URL"),
        help="override AMA API base URL (defaults to env AMA_API_BASE_URL or environment config)",
    )
    p.add_argument(
        "--api-entra-audience",
        default=os.environ.get("AMA_API_ENTRA_AUDIENCE"),
        help="Entra audience the AMA API expects on inbound JWTs (passed to Bicep as entraAudience)",
    )
    return p.parse_args(argv)


def _persist_api_base_url(ctx: RunContext, fqdn: str) -> None:
    """Update the in-memory env config so subsequent stages reach the deployed API."""
    if getattr(ctx.args, "api_base_url", None):
        return
    ctx.env = replace(ctx.env, api_base_url=f"https://{fqdn}")  # type: ignore[misc]


def _resolve_api_base_url(ctx: RunContext, stage: str) -> None:
    """If api_base_url still points at a placeholder, look up the deployed apiFqdn."""
    cli_override = getattr(ctx.args, "api_base_url", None)
    if cli_override:
        return
    if ctx.env.api_base_url and not ctx.env.api_base_url.endswith(".example"):
        return
    if ctx.dry_run:
        return
    fqdn = az_json(
        stage,
        [
            "deployment",
            "group",
            "show",
            "--resource-group",
            ctx.env.resource_group,
            "--name",
            "eval-platform",
            "--query",
            "properties.outputs.apiFqdn.value",
        ],
        ctx.dry_run,
    )
    if isinstance(fqdn, str) and fqdn:
        _persist_api_base_url(ctx, fqdn)
        log_event(stage, "info", f"resolved API base URL: {ctx.env.api_base_url}")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    env = ENVIRONMENTS[args.env]
    if args.api_base_url:
        env = replace(env, api_base_url=args.api_base_url.rstrip("/"))

    if args.stage == "all":
        stage_names = list(STAGES)
    else:
        stage_names = [s.strip() for s in args.stage.split(",") if s.strip()]
        unknown = [s for s in stage_names if s not in STAGES]
        if unknown:
            sys.stderr.write(f"unknown stage(s): {', '.join(unknown)}\n")
            return EXIT_USAGE

    ctx = RunContext(env=env, args=args)
    log_event(
        "driver",
        "info",
        "starting evaluation pipeline",
        env=env.name,
        stages=stage_names,
        dry_run=args.dry_run,
    )
    started = time.monotonic()
    for stage_name in stage_names:
        log_event("driver", "info", f"→ entering stage '{stage_name}'")
        STAGES[stage_name](ctx)
    elapsed = round(time.monotonic() - started, 1)
    log_event(
        "driver",
        "ok",
        f"pipeline complete in {elapsed}s",
        run_id=ctx.state.get("run_id"),
        final_status=ctx.state.get("run_final_status"),
    )
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
