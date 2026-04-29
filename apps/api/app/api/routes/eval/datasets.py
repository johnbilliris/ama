"""Dataset endpoints."""

from __future__ import annotations

from typing import Annotated, Any

from ama_eval_core.audit import AuditAction
from ama_eval_core.models import EvaluationDatasetVersion
from app.middleware.eval_role_guard import (
    EvalPrincipal,
    audit_metadata,
    enforce_anonymous_dataset_scope,
    require_run_operator,
    require_scorecard_viewer,
)
from app.repositories.eval.repositories import AuditRepository, DatasetRepository
from fastapi import APIRouter, Depends, HTTPException, status

router = APIRouter()
_repo = DatasetRepository()
_audit = AuditRepository()


@router.post(
    "/datasets/{dataset_id}/versions",
    status_code=status.HTTP_201_CREATED,
    response_model=EvaluationDatasetVersion,
)
async def create_dataset_version(
    dataset_id: str,
    body: EvaluationDatasetVersion,
    p: Annotated[EvalPrincipal, Depends(require_run_operator)],
) -> EvaluationDatasetVersion:
    enforce_anonymous_dataset_scope(p, dataset_id)
    if body.datasetId != dataset_id:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"datasetId mismatch: path={dataset_id} body={body.datasetId}",
        )
    existing = _repo.get_version(dataset_id, body.version)
    if existing is not None:
        if existing.contentHash != body.contentHash:
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                f"version {body.version} already published with a different contentHash",
            )
        return existing
    saved = _repo.save_version(body)
    _audit.emit_action(
        action=AuditAction.dataset_published,
        principal=p.sub,
        subject_type="dataset",
        subject_id=f"{dataset_id}:{body.version}",
        metadata=audit_metadata(p, caseCount=body.caseCount, contentHash=body.contentHash),
    )
    return saved


@router.get("/datasets/{dataset_id}/versions/{version}")
async def get_dataset_version(
    dataset_id: str,
    version: str,
    p: Annotated[EvalPrincipal, Depends(require_scorecard_viewer)],
) -> dict[str, Any]:
    enforce_anonymous_dataset_scope(p, dataset_id)
    dv = _repo.get_version(dataset_id, version)
    if not dv:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "dataset version not found")
    return dv.model_dump(by_alias=True, exclude_none=True)


@router.get("/datasets/{dataset_id}/versions/{version}/cases")
async def list_dataset_cases(
    dataset_id: str,
    version: str,
    p: Annotated[EvalPrincipal, Depends(require_scorecard_viewer)],
    limit: int = 50,
) -> list[dict[str, Any]]:
    enforce_anonymous_dataset_scope(p, dataset_id)
    cases = _repo.list_cases(dataset_id, version=version)
    _audit.emit_action(
        action=AuditAction.dataset_cases_read,
        principal=p.sub,
        subject_type="dataset",
        subject_id=f"{dataset_id}:{version}",
        metadata=audit_metadata(p, limit=limit, returned=min(limit, len(cases))),
    )
    return [c.model_dump(by_alias=True, exclude_none=True) for c in cases[:limit]]


__all__ = ["router"]
