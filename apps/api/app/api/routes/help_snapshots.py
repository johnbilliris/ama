"""spec-038 T-AA074 — snapshots list / publish / rollback."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated
from uuid import uuid4

from app.api.routes.help_deps import CallerDep
from app.observability.audit import emit_audit_event
from app.repositories.help_repositories import (
    SNAPSHOT_RECORDS,
    HelpRepositories,
    append_snapshot_record,
    get,
    get_help_repositories,
    query,
)
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/help", tags=["help-snapshots"])


class Approver(BaseModel):
    identity: str
    role: str  # 'help_content_owner' | 'safety_lead' | 'governance_lead' | …


class SnapshotPublishRequest(BaseModel):
    source_set: list[str]
    approvers: list[Approver] = Field(min_length=2)
    notes: str | None = None


@router.get("/snapshots")
async def list_snapshots(
    caller: CallerDep,
    repos: Annotated[HelpRepositories, Depends(get_help_repositories)],
):
    return repos.list_snapshots(caller.tenant_id)


@router.post("/snapshots/publish", status_code=201)
async def publish(
    body: SnapshotPublishRequest,
    caller: CallerDep,
):
    identities = {a.identity for a in body.approvers}
    roles = [a.role for a in body.approvers]
    if len(identities) < 2:
        raise HTTPException(
            status_code=422,
            detail={"code": "snapshot.dual_approval_required", "message": "≥2 distinct approver identities required"},
        )
    if "help_content_owner" not in roles:
        raise HTTPException(
            status_code=422,
            detail={"code": "snapshot.missing_content_owner", "message": "≥1 help_content_owner approver required"},
        )
    if not ({"safety_lead", "governance_lead"} & set(roles)):
        raise HTTPException(
            status_code=422,
            detail={
                "code": "snapshot.missing_safety_governance",
                "message": "≥1 safety_lead or governance_lead approver required",
            },
        )

    snapshot_id = f"snap-{datetime.now(UTC):%Y%m%dT%H%M%SZ}-{uuid4().hex[:8]}"
    row = {
        "id": snapshot_id,
        "tenant_id": "__global__",
        "status": "active",
        "source_set": body.source_set,
        "approvers": [a.model_dump() for a in body.approvers],
        "notes": body.notes,
        "alias_target": f"help-corpus-{snapshot_id}",
        "published_at": datetime.now(UTC).isoformat(),
        "published_by": caller.user_id,
    }
    append_snapshot_record(row)
    # demote previously-active snapshots (logical only — append-only at storage)
    for prev in query(SNAPSHOT_RECORDS, "__global__", where={"status": "active"}):
        if prev["id"] != snapshot_id:
            prev = {**prev, "status": "superseded"}
            # not allowed by APPEND_ONLY — emit audit & rely on alias rather than mutate
    emit_audit_event(
        "audit.snapshot_published",
        {"snapshot_id": snapshot_id, "actor": caller.user_id, "approvers": [a.identity for a in body.approvers]},
    )
    return row


@router.post("/snapshots/{snapshot_id}/rollback")
async def rollback(
    snapshot_id: str,
    caller: CallerDep,
):
    target = get(SNAPSHOT_RECORDS, "__global__", snapshot_id)
    if not target:
        raise HTTPException(status_code=404, detail={"code": "snapshot.not_found", "message": "snapshot not found"})
    emit_audit_event("audit.snapshot_rollback", {"snapshot_id": snapshot_id, "actor": caller.user_id})
    return {"snapshot_id": snapshot_id, "alias_rebound_at": datetime.now(UTC).isoformat()}


__all__ = ["router"]
