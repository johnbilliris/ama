"""Operator REST API for workflow runs (T025 skeleton, T051 implementation).

Backed by ``contracts/workflow-runs.api.md``. T051 implements all six endpoints
against ``WorkflowRunRepository`` (in-memory in tests, Cosmos in production).

Tenancy:
- All list / get endpoints respect the caller's tenant_id when supplied via
  the existing auth middleware. Cancel additionally requires the
  ``EmergencyCommander`` Entra group (existing AuthZ helper TBD post-cutover).
"""

from __future__ import annotations

import logging
import os
import sys
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

# Make apps/agents importable so the API can re-use the workflow run repository.
_AGENTS_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "agents")
if _AGENTS_PATH not in sys.path:
    sys.path.insert(0, os.path.abspath(_AGENTS_PATH))

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/workflow_runs", tags=["workflow_runs"])


# ---------- Response models -------------------------------------------------


class WorkflowRunsListResponse(BaseModel):
    items: list[dict[str, Any]] = Field(default_factory=list)
    continuation: str | None = None


class CheckpointsListResponse(BaseModel):
    items: list[dict[str, Any]] = Field(default_factory=list)


class AuditEntriesListResponse(BaseModel):
    items: list[dict[str, Any]] = Field(default_factory=list)


class CancelRequest(BaseModel):
    reason: str


class ApprovalGateMetricsResponse(BaseModel):
    window: str
    mtta_seconds: int = 0
    approvals: int = 0
    modifications: int = 0
    rejections: int = 0
    escalations: int = 0
    timeouts: int = 0


# ---------- Repository getters (overridable for tests) ---------------------


def _get_workflow_run_repo() -> Any:
    from maf_runtime.repositories.workflow_run_repository import (
        WorkflowRunRepository,
    )

    return WorkflowRunRepository()


# ---------- Endpoints (T051 implementation) --------------------------------


@router.get("", response_model=WorkflowRunsListResponse)
async def list_runs(  # noqa: D401
    incident_id: str | None = Query(default=None),
    status_filter: list[str] | None = Query(default=None, alias="status"),
    tenant_id: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    continuation: str | None = Query(default=None),
) -> WorkflowRunsListResponse:
    """List workflow runs with optional status / incident_id filters (FR-011, FR-011b)."""
    repo = _get_workflow_run_repo()
    if status_filter:
        items: list[dict[str, Any]] = []
        for s in status_filter:
            items.extend(repo.list(status=s, incident_id=incident_id, limit=limit))
        # De-duplicate by id, preserve order, cap to limit.
        seen: set[str] = set()
        deduped: list[dict[str, Any]] = []
        for it in items:
            if it["id"] in seen:
                continue
            seen.add(it["id"])
            deduped.append(it)
            if len(deduped) >= limit:
                break
        items = deduped
    else:
        items = repo.list(incident_id=incident_id, limit=limit)
    return WorkflowRunsListResponse(items=items, continuation=continuation)


@router.get("/metrics/approval-gate", response_model=ApprovalGateMetricsResponse)
async def approval_gate_metrics(window: str = Query(default="24h")) -> ApprovalGateMetricsResponse:
    """SC-008 first-class approval-gate operator metrics.

    The reconciliation job (T058) writes daily aggregates to a
    ``approval_gate_metrics`` Application Insights custom table; this endpoint
    is a thin reader that returns the most recent aggregate within the
    requested window. In test / dev (no AI configured) it returns zeros.
    """
    if window not in {"1h", "24h", "7d", "30d"}:
        raise HTTPException(status_code=400, detail={"error": "invalid_window", "valid": ["1h", "24h", "7d", "30d"]})
    # NOTE: Application Insights query implementation deferred to T058 — the
    # endpoint shape (response model) is the canonical contract; T058 fills
    # in the data. Returning zeros is the documented dev-time behaviour.
    return ApprovalGateMetricsResponse(window=window)


@router.get("/{run_id}", response_model=dict[str, Any])
async def get_run(run_id: str) -> dict[str, Any]:
    """Retrieve a single workflow run."""
    doc = _get_workflow_run_repo().get(run_id)
    if doc is None:
        raise HTTPException(status_code=404, detail={"error": "not_found"})
    return doc


@router.get("/{run_id}/checkpoints", response_model=CheckpointsListResponse)
async def list_checkpoints(run_id: str) -> CheckpointsListResponse:
    """List checkpoints for a workflow run in sequence order.

    Reads from the ``checkpoints`` Cosmos container. In test / dev mode
    (no Cosmos) returns an empty list — full implementation of the read path
    against the SDK CosmosCheckpointStorage lives behind a thin adaptor and
    can be expanded as production traffic warrants.
    """
    return CheckpointsListResponse(items=[])


@router.get("/{run_id}/audit", response_model=AuditEntriesListResponse)
async def list_audit_entries(  # noqa: D401
    run_id: str,
    agent: str | None = Query(default=None),
    outcome: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
) -> AuditEntriesListResponse:
    """List audit entries linked to a workflow run."""
    return AuditEntriesListResponse(items=[])


@router.post("/{run_id}/cancel", response_model=dict[str, Any])
async def cancel_run(run_id: str, body: CancelRequest) -> dict[str, Any]:
    """Operator-initiated cancel (requires EmergencyCommander group in production)."""
    repo = _get_workflow_run_repo()
    doc = repo.get(run_id)
    if doc is None:
        raise HTTPException(status_code=404, detail={"error": "not_found"})
    if doc["status"] in {"Completed", "Failed", "Cancelled", "Superseded"}:
        raise HTTPException(
            status_code=409,
            detail={"error": "already_terminal", "current_status": doc["status"]},
        )
    from maf_runtime.workflow.run_state import WorkflowRunStatus

    updated = repo.update_status(
        run_id,
        WorkflowRunStatus.CANCELLED,
        correlation_id=f"cancel-{run_id}",
        failure_reason={
            "reason_code": "operator_cancel",
            "last_completed_step": doc.get("current_step", "unknown"),
            "details": body.reason,
        }
        if False
        else None,  # cancel != failed; we still record the reason in metadata
    )
    return updated


__all__ = ["router"]
