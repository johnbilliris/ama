"""Pillar F — Audit Trace router (T-F07, contracts: getAuditTraceForValue)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Path
from fastapi.responses import JSONResponse

from .._correlation import correlation_id_dep
from .._problem_details import ProblemDetails
from ..models.audit import AuditTrace
from .audit_repository import build_trace

router = APIRouter(tags=["evidence-audit"])


@router.get(
    "/audit/{value_id}",
    response_model=AuditTrace,
    operation_id="getAuditTraceForValue",
)
def get_audit_trace(
    value_id: str = Path(...),
    correlation_id: str = Depends(correlation_id_dep),
) -> AuditTrace:
    trace = build_trace(value_id)
    if trace is None:
        raise HTTPException(
            status_code=404,
            detail=ProblemDetails.of(
                title="audit trace not found",
                status=404,
                detail=f"no entries for value_id={value_id}",
            ).model_dump(),
        )
    return trace


@router.patch(
    "/audit/{value_id}",
    operation_id="rejectAuditPatch",
    include_in_schema=True,
)
def reject_audit_patch(value_id: str = Path(...)) -> JSONResponse:
    """Reject PATCH on audit endpoints (T-AMD-06, FR-040: audit immutability)."""
    return JSONResponse(
        status_code=409,
        content=ProblemDetails.of(
            status=409,
            title="audit-record-immutable",
            detail="Audit records cannot be modified or deleted (FR-040).",
            type="https://ama.example/errors/audit-record-immutable",
        ).model_dump(),
    )


@router.delete(
    "/audit/{value_id}",
    operation_id="rejectAuditDelete",
    include_in_schema=True,
)
def reject_audit_delete(value_id: str = Path(...)) -> JSONResponse:
    """Reject DELETE on audit endpoints (T-AMD-06, FR-040: audit immutability)."""
    return JSONResponse(
        status_code=409,
        content=ProblemDetails.of(
            status=409,
            title="audit-record-immutable",
            detail="Audit records cannot be modified or deleted (FR-040).",
            type="https://ama.example/errors/audit-record-immutable",
        ).model_dump(),
    )

