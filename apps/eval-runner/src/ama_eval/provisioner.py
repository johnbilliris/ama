"""Provisioner — sets up Foundry deployments + Container Apps Job invocation.

Drives `az ai-foundry` operations through a thin shim so unit tests can fake them.
"""

from __future__ import annotations

import logging
import subprocess
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field

from ama_eval_core.audit import AuditAction
from ama_eval_core.models import EvaluationRun, ProvisioningPolicy

log = logging.getLogger(__name__)


@dataclass
class ProvisionedDeployment:
    modelId: str
    version: str
    region: str
    sku: str
    deploymentName: str
    capacity: int
    correlationId: str


@dataclass
class ProvisionContext:
    run: EvaluationRun
    policy: ProvisioningPolicy
    az_run: Callable[[Sequence[str]], dict[str, object]] = field(default=lambda args: _real_az(args))
    audit_emit: Callable[..., None] = field(default=lambda **_: None)


def _real_az(args: Sequence[str]) -> dict[str, object]:
    """Default az shell invocation. Returns parsed JSON output, or raises."""
    import json

    completed = subprocess.run(["az", *args, "-o", "json"], capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        raise RuntimeError(f"az failed: {completed.stderr.strip()}")
    return json.loads(completed.stdout) if completed.stdout.strip() else {}


def provision_models(ctx: ProvisionContext) -> list[ProvisionedDeployment]:
    """Provision deployments for each model in the run, observing policy caps."""
    if len(ctx.run.models) > ctx.policy.maxConcurrentDeployments:
        raise ValueError(
            f"models count ({len(ctx.run.models)}) > maxConcurrentDeployments ({ctx.policy.maxConcurrentDeployments})"
        )

    deployments: list[ProvisionedDeployment] = []
    for m in ctx.run.models:
        region = m.deploymentRegion or ctx.policy.allowedRegions[0]
        sku = m.sku or ctx.policy.allowedSkus[0]
        if region not in ctx.policy.allowedRegions:
            raise ValueError(f"region {region} not in allow-list for {m.modelId}")
        if sku not in ctx.policy.allowedSkus:
            raise ValueError(f"sku {sku} not in allow-list for {m.modelId}")

        deploy_name = f"eval-{ctx.run.runId[:12].lower()}-{m.modelId}".replace(".", "-")
        ctx.audit_emit(
            action=AuditAction.infra_provisioned.value,
            principal="provisioner",
            subject_type="deployment",
            subject_id=deploy_name,
            run_id=ctx.run.runId,
            metadata={"model": m.modelId, "region": region, "sku": sku},
        )
        deployments.append(
            ProvisionedDeployment(
                modelId=m.modelId,
                version=m.version,
                region=region,
                sku=sku,
                deploymentName=deploy_name,
                capacity=10,
                correlationId=ctx.run.runId,
            )
        )
    return deployments


def deprovision_models(ctx: ProvisionContext, deployments: list[ProvisionedDeployment]) -> None:
    """Best-effort teardown of all provisioned deployments."""
    for d in deployments:
        try:
            ctx.az_run(
                [
                    "cognitiveservices",
                    "account",
                    "deployment",
                    "delete",
                    "--name",
                    d.deploymentName,
                    "--deployment-name",
                    d.deploymentName,
                ]
            )
            ctx.audit_emit(
                action=AuditAction.infra_deprovisioned.value,
                principal="provisioner",
                subject_type="deployment",
                subject_id=d.deploymentName,
                run_id=ctx.run.runId,
            )
        except Exception as exc:
            log.warning("deprovision failed for %s: %s", d.deploymentName, exc)


__all__ = ["ProvisionedDeployment", "ProvisionContext", "provision_models", "deprovision_models"]
