"""Trigger Azure Container Apps Job executions to start eval runs.

The AMA API queues a run document in Cosmos and then asks Azure to start the
``caj-eval-runner-${env}`` job with per-execution environment variables that
identify the run + dataset to process. This module wraps the ARM REST call so
the route handler stays small and so we can no-op cleanly in unit tests / when
the surrounding infrastructure is not configured (``EVAL_RUNNER_JOB_*`` env
vars unset).
"""

from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

_JOB_API_VERSION = "2024-03-01"


def _runner_image() -> str | None:
    return os.environ.get("EVAL_RUNNER_JOB_IMAGE")


def _runner_target() -> tuple[str | None, str | None, str | None]:
    return (
        os.environ.get("AZURE_SUBSCRIPTION_ID"),
        os.environ.get("EVAL_RUNNER_JOB_RESOURCE_GROUP"),
        os.environ.get("EVAL_RUNNER_JOB_NAME"),
    )


def is_configured() -> bool:
    sub, rg, job = _runner_target()
    return all((sub, rg, job, _runner_image()))


def start_run_execution(
    *,
    run_id: str,
    dataset_id: str,
    dataset_version: str,
    mode: str,
    max_cases: int | None = None,
) -> dict[str, Any] | None:
    """Start a Container Apps Job execution for ``run_id``. Returns the ARM
    response payload, or ``None`` when the runner job is not configured (e.g.
    local dev or test). Failures are logged and swallowed so the API still
    returns the queued run; the reconciler picks up stuck queued runs."""

    if not is_configured():
        logger.info("eval runner job not configured; skipping execution start for run %s", run_id)
        return None

    subscription_id, resource_group, job_name = _runner_target()
    try:
        from azure.identity import DefaultAzureCredential
        from azure.mgmt.appcontainers import ContainerAppsAPIClient
    except ImportError as exc:  # pragma: no cover - exercised via dependency check
        logger.warning("azure-mgmt-appcontainers not installed; cannot start runner job: %s", exc)
        return None

    cred = DefaultAzureCredential()
    client = ContainerAppsAPIClient(credential=cred, subscription_id=subscription_id, api_version=_JOB_API_VERSION)

    # Container Apps Job execution overrides REPLACE rather than merge container fields.
    # Fetch the existing container template so we can preserve env / image / resources
    # while overriding only the args for this execution.
    try:
        job_resource = client.jobs.get(resource_group, job_name)
        existing_containers = list(job_resource.template.containers)
    except Exception as exc:  # noqa: BLE001
        logger.exception("could not read job %s template: %s", job_name, exc)
        return None

    runner_container = next(
        (c for c in existing_containers if getattr(c, "name", None) == "runner"),
        existing_containers[0] if existing_containers else None,
    )
    if runner_container is None:
        logger.error("job %s has no containers", job_name)
        return None

    env_list: list[dict[str, Any]] = []
    for ev in runner_container.env or []:
        env_list.append(
            {
                "name": ev.name,
                "value": getattr(ev, "value", None),
                "secretRef": getattr(ev, "secret_ref", None),
            }
        )

    resources = runner_container.resources
    cpu_value = float(resources.cpu) if resources and resources.cpu is not None else 1.0
    memory_value = resources.memory if resources and resources.memory else "2Gi"
    args_list = [
        "--run-id",
        run_id,
        "--dataset-id",
        dataset_id,
        "--dataset-version",
        dataset_version,
        "--mode",
        mode,
    ]
    if max_cases is not None and max_cases > 0:
        args_list.extend(["--max-cases", str(max_cases)])
    template = {
        "containers": [
            {
                "name": runner_container.name,
                "image": runner_container.image,
                "resources": {"cpu": cpu_value, "memory": memory_value},
                "env": env_list,
                "args": args_list,
            }
        ],
    }
    try:
        poller = client.jobs.begin_start(resource_group, job_name, template=template)
        result = poller.result()
        execution_name = getattr(result, "name", None)
        logger.info("started runner job execution %s for run %s", execution_name, run_id)
        return {"executionName": execution_name, "runId": run_id}
    except Exception as exc:  # noqa: BLE001 — explicit logging + graceful degrade
        logger.exception("failed to start runner job for run %s: %s", run_id, exc)
        return None


__all__ = ["is_configured", "start_run_execution"]
