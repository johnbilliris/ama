"""Operator REST API for workflow runs (T025 skeleton, T051 implementation).

Backed by ``contracts/workflow-runs.api.md``. T025 ships the six endpoints as
501 Not Implemented placeholders so the OpenAPI surface and CI test scaffolding
can be wired immediately. T051 (Phase 4) replaces each placeholder with a real
implementation backed by the WorkflowRunRepository, audit_entries container,
and Application Insights.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/workflow_runs", tags=["workflow_runs"])


# ---------- Response models (light-weight; full schemas in contracts/) -------


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


# ---------- Endpoints (501 placeholders for T025) --------------------------


_NOT_IMPLEMENTED = HTTPException(
    status_code=status.HTTP_501_NOT_IMPLEMENTED,
    detail={"error": "not_implemented", "message": "T025 placeholder; see T051 for implementation."},
)


@router.get("", response_model=WorkflowRunsListResponse)
async def list_runs(  # noqa: D401
    incident_id: str | None = Query(default=None),
    status_filter: list[str] | None = Query(default=None, alias="status"),
    tenant_id: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    continuation: str | None = Query(default=None),
) -> WorkflowRunsListResponse:
    """List workflow runs with optional filters (T025 placeholder)."""
    raise _NOT_IMPLEMENTED


@router.get("/{run_id}", response_model=dict[str, Any])
async def get_run(run_id: str) -> dict[str, Any]:
    """Retrieve a single workflow run (T025 placeholder)."""
    raise _NOT_IMPLEMENTED


@router.get("/{run_id}/checkpoints", response_model=CheckpointsListResponse)
async def list_checkpoints(run_id: str) -> CheckpointsListResponse:
    """List checkpoints for a workflow run in sequence order (T025 placeholder)."""
    raise _NOT_IMPLEMENTED


@router.get("/{run_id}/audit", response_model=AuditEntriesListResponse)
async def list_audit_entries(  # noqa: D401
    run_id: str,
    agent: str | None = Query(default=None),
    outcome: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
) -> AuditEntriesListResponse:
    """List audit entries linked to a workflow run (T025 placeholder)."""
    raise _NOT_IMPLEMENTED


@router.post("/{run_id}/cancel", response_model=dict[str, Any])
async def cancel_run(run_id: str, body: CancelRequest) -> dict[str, Any]:
    """Operator-initiated cancel; requires EmergencyCommander group (T025 placeholder)."""
    raise _NOT_IMPLEMENTED


@router.get("/metrics/approval-gate", response_model=ApprovalGateMetricsResponse)
async def approval_gate_metrics(window: str = Query(default="24h")) -> ApprovalGateMetricsResponse:
    """SC-008 first-class approval-gate operator metrics (T025 placeholder)."""
    raise _NOT_IMPLEMENTED


__all__ = ["router"]
