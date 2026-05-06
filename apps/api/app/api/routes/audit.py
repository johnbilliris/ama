"""Audit append-only enforcement bridge (spec-035 FR-003 follow-up).

The Observer-Auditor timeline panel
([`apps/web/src/app/workspaces/[personaId]/_panels/observer-auditor-timeline.tsx`])
is required to reject any client-side mutation attempt by emitting a synthetic
``outcome=denied`` row to ``POST /api/audit/denied-mutation``. The route
records the denial in an in-memory ring buffer so the same correlation_id can
be cross-referenced from the workspace bridge if needed.

This is intentionally additive and unguarded: it is a non-mutating record of
a *rejected* mutation. The append-only enforcement is the application of the
``DENY`` outcome itself; this endpoint is the audit trail, not the policy.
"""

from __future__ import annotations

import uuid
from collections import deque
from datetime import UTC, datetime
from typing import Any, Final

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

router = APIRouter(prefix="/audit", tags=["audit"])

_RING_BUFFER_MAX: Final[int] = 1024

# In-memory ring buffer of recent denials. Bound is intentionally small: the
# canonical persistent audit chain lives in Cosmos via the Q10 audit
# repository when AMA_ENABLE_PRODUCTION_AUTH=1; this is a best-effort
# fallback so the workspace UI always has *something* to render.
_DENIED_MUTATIONS: deque[dict[str, Any]] = deque(maxlen=_RING_BUFFER_MAX)


class DeniedMutationRequest(BaseModel):
    attempted_action: str = Field(..., min_length=1, max_length=64)
    target_audit_id: str = Field(..., min_length=1, max_length=128)
    rationale: str = Field(default="append-only-policy", max_length=256)


@router.post("/denied-mutation", status_code=202)
async def record_denied_mutation(payload: DeniedMutationRequest, request: Request) -> dict[str, Any]:
    correlation_id = request.headers.get("x-correlation-id") or str(uuid.uuid4())
    row = {
        "audit_id": str(uuid.uuid4()),
        "outcome": "denied",
        "classifier_outcome": "clean",
        "masked_field_count": 0,
        "attempted_action": payload.attempted_action,
        "target_audit_id": payload.target_audit_id,
        "rationale": payload.rationale,
        "correlation_id": correlation_id,
        "timestamp": datetime.now(UTC).isoformat(),
        "actor": "ui-policy-enforcer",
    }
    _DENIED_MUTATIONS.append(row)
    return {"recorded": True, "audit_id": row["audit_id"], "outcome": "denied"}


def _denied_mutations_buffer() -> deque[dict[str, Any]]:
    """Test hook + cross-module accessor for the in-memory ring buffer."""
    return _DENIED_MUTATIONS


__all__ = ["router"]
