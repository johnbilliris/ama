"""Scorecard endpoints — Tier-1 access (broader role)."""

from __future__ import annotations

from typing import Annotated, Any

from ama_eval_core.audit import AuditAction
from app.middleware.eval_role_guard import EvalPrincipal, require_scorecard_viewer
from app.repositories.eval.repositories import AuditRepository, RunRepository
from fastapi import APIRouter, Depends, HTTPException, status

router = APIRouter()
_repo = RunRepository()
_audit = AuditRepository()


@router.get("/runs/{run_id}/scorecard")
async def get_scorecard(
    run_id: str,
    p: Annotated[EvalPrincipal, Depends(require_scorecard_viewer)],
) -> dict[str, Any]:
    sc = _repo.get_scorecard(run_id)
    if not sc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "scorecard not found")
    _audit.emit_action(
        action=AuditAction.scorecard_read,
        principal=p.sub,
        subject_type="scorecard",
        subject_id=run_id,
        run_id=run_id,
    )
    return sc.model_dump(by_alias=True, exclude_none=True)


@router.get("/runs/{run_id}/scorecard/winners")
async def get_winners(
    run_id: str,
    p: Annotated[EvalPrincipal, Depends(require_scorecard_viewer)],
) -> dict[str, Any]:
    sc = _repo.get_scorecard(run_id)
    if not sc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "scorecard not found")
    return {"runId": sc.runId, "winner": sc.winner.model_dump()}


__all__ = ["router"]
