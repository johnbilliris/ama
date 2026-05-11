"""Workspace-shaped fallback for the IC approval card (spec-035).

The IC Approval Card panel
([`apps/web/src/app/workspaces/[personaId]/_panels/ic-approval-card.tsx`])
calls ``POST /api/outcomes/sc-{id}/evaluate`` then ``GET /api/audit/list?
correlation_id=...`` to fetch the freshly-emitted audit row.

The canonical implementations live in
[`outcome_evaluator.py`](outcome_evaluator.py) and
[`audit_list.py`](audit_list.py) and are gated behind ``AMA_TEST_SUPPORT=1``
or ``AMA_ENABLE_PRODUCTION_AUTH=1``. In dev environments where neither flag
is set, the gated routes are not mounted and the workspace card shows a 404.

This bridge module mounts a *workspace-shaped* fallback that:

* accepts the IC Approval Card's body shape ``{rationale, sources,
  confidence, approver_identity}``;
* records an in-memory audit row keyed by the ``X-Correlation-Id`` header;
* surfaces the row through ``GET /audit/list?correlation_id=...`` so the
  card's success-path renders the classifier banner.

Mounted **only** when neither gate is enabled — the gated routers continue
to take precedence whenever they are mounted (they own the path first).
"""

from __future__ import annotations

import uuid
from collections import deque
from datetime import UTC, datetime
from typing import Any, Final

from fastapi import APIRouter, Path, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

router = APIRouter(tags=["workspace-bridge"])

_RING_BUFFER_MAX: Final[int] = 1024

# In-memory ring buffer keyed by correlation_id. Newest first inside each
# bucket. The buffer is process-local; lifespan resets re-init it. This is
# intentional — the bridge is a defensive fallback for the dev environment,
# not a durable audit trail.
_AUDIT_ROWS: deque[dict[str, Any]] = deque(maxlen=_RING_BUFFER_MAX)


class IcApprovalSourceRef(BaseModel):
    model_config = ConfigDict(extra="allow")
    doc_id: str = Field(default="")
    excerpt: str = Field(default="")
    href: str | None = None


class IcApprovalRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    rationale: str = Field(default="", max_length=4096)
    sources: list[IcApprovalSourceRef] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    approver_identity: str = Field(default="", max_length=256)


def _new_correlation_id() -> str:
    return str(uuid.uuid4())


@router.post("/outcomes/sc-{sc_id}/evaluate")
async def workspace_outcome_evaluate(
    request: Request,
    payload: IcApprovalRequest,
    sc_id: str = Path(..., min_length=1, max_length=64),
) -> JSONResponse:
    correlation_id = request.headers.get("x-correlation-id") or _new_correlation_id()
    audit_id = str(uuid.uuid4())
    masked = sum(1 for src in payload.sources if src.excerpt and any(t in src.excerpt for t in ("[REDACTED]", "***")))
    classifier_outcome = "masked" if masked > 0 else "clean"
    row: dict[str, Any] = {
        "audit_id": audit_id,
        "outcome": "approved",
        "classifier_outcome": classifier_outcome,
        "masked_field_count": masked,
        "rationale": payload.rationale,
        "confidence": payload.confidence,
        "approver_identity": payload.approver_identity,
        "scenario_id": f"sc-{sc_id}",
        "correlation_id": correlation_id,
        "timestamp": datetime.now(UTC).isoformat(),
        "sources": [src.model_dump() for src in payload.sources],
        "actor": payload.approver_identity or "unknown",
    }
    _AUDIT_ROWS.appendleft(row)
    return JSONResponse(
        status_code=200,
        content={
            "status": "approved",
            "audit_id": audit_id,
            "correlation_id": correlation_id,
            "classifier_outcome": classifier_outcome,
        },
        headers={"x-correlation-id": correlation_id},
    )


@router.get("/audit/list")
async def workspace_audit_list(
    request: Request,
    correlation_id: str | None = None,
    limit: int = 100,
) -> dict[str, Any]:
    _ = request  # placeholder for future request-context use
    rows = list(_AUDIT_ROWS)
    if correlation_id is not None:
        rows = [r for r in rows if r.get("correlation_id") == correlation_id]
    if limit > 0:
        rows = rows[:limit]
    return {"rows": rows, "count": len(rows)}


def _audit_buffer() -> deque[dict[str, Any]]:
    """Test hook for the in-memory ring buffer."""
    return _AUDIT_ROWS


__all__ = ["router"]
