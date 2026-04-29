"""Tier-2 trace endpoints — auditor / operator only.

Per FR-021 these endpoints emit `scorecard.trace.read` audit events.
"""

from __future__ import annotations

import os
from typing import Annotated, Any

from ama_eval_core.audit import AuditAction
from app.middleware.eval_role_guard import EvalPrincipal, require_tier2
from app.repositories.eval.repositories import AuditRepository
from fastapi import APIRouter, Depends, HTTPException, status

router = APIRouter()
_audit = AuditRepository()


@router.get("/runs/{run_id}/scorecard/traces/{case_id}")
async def get_trace(
    run_id: str,
    case_id: str,
    p: Annotated[EvalPrincipal, Depends(require_tier2)],
) -> dict[str, Any]:
    """Fetch a SampleTrace from blob storage (or from in-memory dev cache)."""
    _audit.emit_action(
        action=AuditAction.scorecard_trace_read,
        principal=p.sub,
        subject_type="trace",
        subject_id=f"{run_id}:{case_id}",
        run_id=run_id,
        metadata={"caseId": case_id},
    )

    # Prod: load from blob storage
    if os.environ.get("EVAL_TRACES_CONTAINER"):
        try:
            from azure.identity import DefaultAzureCredential
            from azure.storage.blob import BlobServiceClient

            account = os.environ["EVAL_STORAGE_ACCOUNT"]
            container = os.environ["EVAL_TRACES_CONTAINER"]
            cred = DefaultAzureCredential()
            svc = BlobServiceClient(account_url=f"https://{account}.blob.core.windows.net", credential=cred)
            blob = svc.get_container_client(container).get_blob_client(f"runs/{run_id}/traces/{case_id}.json")
            data = blob.download_blob().readall()
            import json

            return json.loads(data)
        except Exception as exc:
            raise HTTPException(status.HTTP_404_NOT_FOUND, f"trace not found: {exc}") from exc

    raise HTTPException(status.HTTP_404_NOT_FOUND, "no trace store configured")


@router.get("/runs/{run_id}/audit-events")
async def get_audit_events(
    run_id: str,
    p: Annotated[EvalPrincipal, Depends(require_tier2)],
) -> list[dict[str, Any]]:
    events = _audit.list_for_run(run_id)
    _audit.emit_action(
        action=AuditAction.scorecard_export,
        principal=p.sub,
        subject_type="run",
        subject_id=run_id,
        run_id=run_id,
        metadata={"eventCount": len(events)},
    )
    return [e.model_dump(by_alias=True, exclude_none=True) for e in events]


__all__ = ["router"]
