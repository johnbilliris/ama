"""Metric / judge / baseline registry endpoints."""

from __future__ import annotations

from typing import Annotated, Any

from app.middleware.eval_role_guard import EvalPrincipal, require_scorecard_viewer
from app.repositories.eval.repositories import MetricRepository
from fastapi import APIRouter, Depends, HTTPException, status

router = APIRouter()
_repo = MetricRepository()


@router.get("/metrics")
async def list_metrics(
    p: Annotated[EvalPrincipal, Depends(require_scorecard_viewer)],
) -> list[dict[str, Any]]:
    return [m.model_dump(by_alias=True, exclude_none=True) for m in _repo.list_metrics()]


@router.get("/baselines/{dataset_id}/{model_tier}/{environment}")
async def get_baseline(
    dataset_id: str,
    model_tier: str,
    environment: str,
    p: Annotated[EvalPrincipal, Depends(require_scorecard_viewer)],
) -> dict[str, Any]:
    b = _repo.get_baseline(dataset_id, model_tier, environment)
    if not b:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "baseline not found")
    return b.model_dump(by_alias=True, exclude_none=True)


__all__ = ["router"]
