"""FR-029 audit-list route (cycle-1 amendment, spec 034 — T179).

``GET /api/audit/list?correlation_id={uuid}&cycle={current|all}&limit={1..500}&cursor={opaque}``

Cycle semantics (Pass 5 Q22):

  • ``cycle=current`` (default) — rows with
    ``audit_timestamp >= bootstrap_seed_data().current_cycle_start``;
  • ``cycle=all`` — opt-in cross-cycle read for FR-005 / FR-027.

Activation is dual-guarded by ``app.middleware.test_support_guard.is_enabled``;
the router is only mounted when the canonical ``AMA_TEST_SUPPORT == "1"``
env var is set AND ``settings.environment in {"dev", "test"}``.

Contract: ``specs/034-webapp-capstone-coverage/contracts/outcome-evaluator.contract.md``
§"Server-side contract — audit-list".
"""

from __future__ import annotations

from typing import Any

from app.services.outcome_evaluator_service import (
    EvaluatorError,
)
from app.services.outcome_evaluator_service import (
    list_audit as list_audit_service,
)
from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/audit", tags=["audit-list"])


@router.get("/list")
def list_audit_rows(
    correlation_id: str | None = Query(  # noqa: B008
        default=None,
        description="Optional UUID v4 filter; matches a single audit chain",
    ),
    cycle: str = Query(  # noqa: B008
        default="current",
        pattern=r"^(current|all)$",
        description="'current' restricts to bootstrap_seed_data().current_cycle_start window",
    ),
    limit: int = Query(  # noqa: B008
        default=100,
        ge=1,
        le=500,
        description="Page size (FR-029: capped at 500 to bound CI runtime)",
    ),
    cursor: str | None = Query(  # noqa: B008
        default=None,
        description="Opaque pagination cursor from prior response",
    ),
) -> JSONResponse:
    try:
        body: dict[str, Any] = list_audit_service(
            correlation_id=correlation_id,
            cycle=cycle,
            limit=limit,
            cursor=cursor,
        )
    except EvaluatorError as exc:
        return JSONResponse(status_code=exc.status_code, content=exc.payload)
    return JSONResponse(status_code=200, content=body)
