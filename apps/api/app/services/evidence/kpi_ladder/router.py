"""Pillar A — KPI ladder router (T-A07, FR-004, contracts: getKpiLadder)."""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query

from .._correlation import correlation_id_dep
from .._problem_details import ProblemDetails
from ..models.kpi import KpiLadderView
from .manager import (
    CapstoneCoverageError,
    EdgeCase5Error,
    assemble_ladder_view,
)
from .seed import seed_default_ladder, seed_public_information_ladder

router = APIRouter(tags=["evidence-kpi-ladder"])

_SEEDED = False


def _ensure_seed() -> None:
    global _SEEDED
    if _SEEDED:
        return
    from .repository import latest_version_for, publish

    for ind in (*seed_default_ladder(), *seed_public_information_ladder()):
        if latest_version_for(ind.kpi_id) == 0:
            try:
                publish(ind)
            except Exception:  # pragma: no cover
                pass
    _SEEDED = True


@router.get("/kpi-ladder", response_model=KpiLadderView, operation_id="getKpiLadder")
def get_kpi_ladder(
    include_risk_adjusted: bool = Query(default=True),
    capstone_sc_id: Literal[
        "SC-CAP-015-001",
        "SC-CAP-015-002",
        "SC-CAP-015-003",
        "SC-CAP-015-004",
        "SC-CAP-015-005",
    ]
    | None = Query(default=None),
    correlation_id: str = Depends(correlation_id_dep),
) -> KpiLadderView:
    _ensure_seed()
    try:
        return assemble_ladder_view(
            capstone_sc_id=capstone_sc_id,
            include_risk_adjusted=include_risk_adjusted,
        )
    except EdgeCase5Error as exc:
        raise HTTPException(
            status_code=409,
            detail=ProblemDetails.of(
                title="risk-adjusted variant unavailable",
                status=409,
                detail=str(exc),
            ).model_dump(),
        )
    except CapstoneCoverageError as exc:
        raise HTTPException(
            status_code=500,
            detail=ProblemDetails.of(
                title="ladder coverage gap",
                status=500,
                detail=str(exc),
            ).model_dump(),
        )
