"""Pillar A — KPI ladder router (T-A07, FR-004, contracts: getKpiLadder)."""

from __future__ import annotations

import os
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, ConfigDict, Field

from .._correlation import correlation_id_dep
from .._problem_details import ProblemDetails
from ..models.kpi import IndicatorDefinition, KpiLadderView
from .manager import (
    CapstoneCoverageError,
    EdgeCase5Error,
    assemble_ladder_view,
    candidate_snapshot_metadata,
    record_auditor_signoff,
)
from .seed import seed_default_ladder, seed_public_information_ladder

router = APIRouter(tags=["evidence-kpi-ladder"])

_SEEDED = False


class AuditorSignoffRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    indicators: list[IndicatorDefinition] = Field(min_length=1)
    approval_id: str = Field(min_length=1, max_length=128)
    basis: str = Field(min_length=8, max_length=2000)


class AuditorSignoffResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    artefact_id: Literal["kpi_ladder"] = "kpi_ladder"
    artifact_version: str
    artifact_hash: str
    auditor_id: str


def _ensure_seed() -> None:
    global _SEEDED
    if _SEEDED:
        return
    if os.environ.get("AMA_TEST_MODE") != "1":
        return
    from .repository import latest_version_for, publish

    for ind in (*seed_default_ladder(), *seed_public_information_ladder()):
        if latest_version_for(ind.kpi_id) == 0:
            publish(ind)
    _SEEDED = True


@router.post(
    "/kpi-ladder/signoffs",
    response_model=AuditorSignoffResponse,
    status_code=status.HTTP_201_CREATED,
    operation_id="recordKpiLadderAuditorSignoff",
)
def create_kpi_ladder_signoff(
    request: Request,
    body: AuditorSignoffRequest,
    correlation_id: str = Depends(correlation_id_dep),
) -> AuditorSignoffResponse:
    claims = getattr(request.state, "claims", {}) or {}
    roles = {str(role) for role in (claims.get("roles") or [claims.get("app_role") or claims.get("appRole")]) if role}
    auditor_id = str(claims.get("oid") or claims.get("sub") or "")
    if not roles.intersection({"observer-auditor", "system-administrator"}):
        raise HTTPException(
            status_code=403,
            detail=ProblemDetails.of(
                status=403,
                title="auditor-role-required",
                detail="Observer-auditor or system-administrator role is required.",
                type="https://ama.example/errors/auditor-role-required",
            ).model_dump(),
        )
    record_auditor_signoff(
        artefact_id="kpi_ladder",
        indicators=body.indicators,
        auditor_id=auditor_id,
        approval_id=body.approval_id,
        basis=body.basis,
        correlation_id=correlation_id,
    )
    artifact_version, artifact_hash = candidate_snapshot_metadata(body.indicators)
    return AuditorSignoffResponse(
        artifact_version=artifact_version,
        artifact_hash=artifact_hash,
        auditor_id=auditor_id,
    )


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
