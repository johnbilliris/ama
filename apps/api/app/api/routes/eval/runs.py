"""Run endpoints: POST /api/eval/runs, GET /api/eval/runs, GET /api/eval/runs/{id}, POST cancel."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated, Any, Literal

from ama_eval_core.audit import AuditAction
from ama_eval_core.models import EvaluationRun, ModelUnderTest, RunMode, RunStatus
from ama_eval_core.policy import RunRequest, check_run_against_policy
from app.middleware.eval_role_guard import (
    EvalPrincipal,
    audit_metadata,
    enforce_anonymous_dataset_scope,
    require_run_operator,
    require_scorecard_viewer,
)
from app.repositories.eval.repositories import (
    AuditRepository,
    DatasetRepository,
    MetricRepository,
    RunRepository,
)
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

router = APIRouter()

_dataset_repo = DatasetRepository()
_run_repo = RunRepository()
_metric_repo = MetricRepository()
_audit = AuditRepository()


class CreateRunRequest(BaseModel):
    datasetId: str
    datasetVersion: str
    models: list[dict[str, Any]] = Field(min_length=1)
    metricSetVersion: str = "1.0.0"
    policyVersion: str = "1.0.0"
    mode: Literal["ad-hoc", "scheduled-baseline", "pr-fast-subset", "progressive-delivery-full"] = "ad-hoc"
    estimatedCostAud: float = 0.0
    estimatedDurationMinutes: int = 60
    changeRef: str | None = None
    baselineRunId: str | None = None
    datasetSubset: dict[str, Any] | None = None


class RunSummary(BaseModel):
    runId: str
    status: str
    mode: str
    datasetId: str
    datasetVersion: str
    createdAt: datetime
    createdBy: str
    completedAt: datetime | None = None
    exitCode: int | None = None


def _new_run_id() -> str:
    # Crockford-base32 ULID-ish; keep simple for in-memory dev
    import secrets

    alpha = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
    return "01" + "".join(secrets.choice(alpha) for _ in range(24))


@router.post("/runs", status_code=status.HTTP_201_CREATED, response_model=RunSummary)
async def create_run(
    body: CreateRunRequest,
    p: Annotated[EvalPrincipal, Depends(require_run_operator)],
) -> RunSummary:
    enforce_anonymous_dataset_scope(p, body.datasetId)
    in_flight = sum(1 for r in _run_repo.list_runs(limit=200) if r.status in {"queued", "provisioning", "running"})

    # Build a stub policy for in-process gating (real policy comes from repo in prod)
    from ama_eval_core.models import ProvisioningPolicy

    policy = ProvisioningPolicy(
        policyVersion=body.policyVersion,
        env="dev",
        allowedRegions=["australiaeast", "eastus2", "westus3", "swedencentral"],
        allowedSkus=["Standard", "GlobalStandard"],
        maxConcurrentDeployments=6,
        maxRunCostAud=250.0,
        maxRunDurationMinutes=480,
        prFastSubsetMaxMinutes=30,
        secondaryJudgeSamplingRate=0.05,
        evaluatorRoles={"viewer": "Eval.Viewer"},
    )
    req = RunRequest(
        models=tuple((m["modelId"], m.get("deploymentRegion"), m.get("sku")) for m in body.models),
        estimated_cost_aud=body.estimatedCostAud,
        estimated_duration_minutes=body.estimatedDurationMinutes,
        mode=body.mode,
        in_flight_runs=in_flight,
    )
    verdict = check_run_against_policy(req, policy)
    if not verdict.allowed:
        _audit.emit_action(
            action=AuditAction.infra_policy_violated,
            principal=p.sub,
            subject_type="run",
            subject_id="pending",
            metadata=audit_metadata(p, violations=[v.code for v in verdict.violations]),
        )
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail={
                "violations": [{"code": v.code, "message": v.message, "field": v.field} for v in verdict.violations]
            },
        )

    run_id = _new_run_id()
    run = EvaluationRun(
        runId=run_id,
        status=RunStatus.queued,
        mode=RunMode(body.mode),
        datasetId=body.datasetId,
        datasetVersion=body.datasetVersion,
        models=[ModelUnderTest(**m) for m in body.models],
        metricSetVersion=body.metricSetVersion,
        policyVersion=body.policyVersion,
        estimatedCostAud=body.estimatedCostAud,
        createdAt=datetime.now(UTC),
        createdBy=p.sub,
        changeRef=body.changeRef,
        baselineRunId=body.baselineRunId,
    )
    _run_repo.save_run(run)
    _audit.emit_action(
        action=AuditAction.run_queued,
        principal=p.sub,
        subject_type="run",
        subject_id=run_id,
        run_id=run_id,
        metadata=audit_metadata(p, mode=body.mode, models=[m.modelId for m in run.models]),
    )

    from app.services import eval_job_trigger

    subset = body.datasetSubset or {}
    raw_max_cases = subset.get("maxCases")
    eval_job_trigger.start_run_execution(
        run_id=run_id,
        dataset_id=body.datasetId,
        dataset_version=body.datasetVersion,
        mode=body.mode,
        max_cases=int(raw_max_cases) if raw_max_cases else None,
    )

    return RunSummary(
        runId=run.runId,
        status=run.status,
        mode=run.mode,
        datasetId=run.datasetId,
        datasetVersion=run.datasetVersion,
        createdAt=run.createdAt,
        createdBy=run.createdBy,
    )


@router.get("/runs", response_model=list[RunSummary])
async def list_runs(
    p: Annotated[EvalPrincipal, Depends(require_scorecard_viewer)],
    status_filter: str | None = None,
    mode: str | None = None,
    limit: int = 50,
) -> list[RunSummary]:
    runs = _run_repo.list_runs(status=status_filter, mode=mode, limit=limit)
    return [
        RunSummary(
            runId=r.runId,
            status=r.status,
            mode=r.mode,
            datasetId=r.datasetId,
            datasetVersion=r.datasetVersion,
            createdAt=r.createdAt,
            createdBy=r.createdBy,
            completedAt=r.completedAt,
            exitCode=r.exitCode,
        )
        for r in runs
    ]


@router.get("/runs/{run_id}")
async def get_run(
    run_id: str,
    p: Annotated[EvalPrincipal, Depends(require_scorecard_viewer)],
) -> dict[str, Any]:
    run = _run_repo.get_run(run_id)
    if not run:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "run not found")
    enforce_anonymous_dataset_scope(p, run.datasetId)
    return run.model_dump(by_alias=True, exclude_none=True)


@router.post("/runs/{run_id}/cancel", status_code=status.HTTP_202_ACCEPTED)
async def cancel_run(
    run_id: str,
    p: Annotated[EvalPrincipal, Depends(require_run_operator)],
) -> dict[str, str]:
    run = _run_repo.get_run(run_id)
    if not run:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "run not found")
    if run.status in {"succeeded", "failed", "cancelled"}:
        raise HTTPException(status.HTTP_409_CONFLICT, f"run already terminal: {run.status}")
    updated = run.model_copy(update={"status": "cancelling"})
    _run_repo.save_run(updated)
    _audit.emit_action(
        action=AuditAction.run_cancelled,
        principal=p.sub,
        subject_type="run",
        subject_id=run_id,
        run_id=run_id,
        metadata=audit_metadata(p, reason="user-requested"),
    )
    return {"runId": run_id, "status": "cancelling"}


__all__ = ["router"]
