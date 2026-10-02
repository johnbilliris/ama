from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Path, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from .._correlation import correlation_id_dep
from .._guards import NonAuRegionError
from .._problem_details import ProblemDetails
from ..models.audit import AuditTrace
from ..models.signal import Signal, SignalIngressRequest
from . import audit_manager
from .audit_repository import build_trace
from .signal_ingest import ingest_signal

router = APIRouter(tags=["evidence-audit"])


@router.post(
    "/signals",
    response_model=Signal,
    status_code=status.HTTP_201_CREATED,
    operation_id="ingestEvidenceSignal",
)
def post_signal(
    request: Request,
    body: SignalIngressRequest,
    correlation_id: str = Depends(correlation_id_dep),
) -> Signal:
    claims = getattr(request.state, "claims", {}) or {}
    actor = str(claims.get("oid") or claims.get("sub") or body.actor or "system")
    trusted_region = claims.get("region") or body.region
    request_body = body.model_copy(update={"correlation_id": correlation_id})
    try:
        return ingest_signal(
            request_body,
            actor=actor,
            trusted_region=str(trusted_region) if trusted_region is not None else None,
        )
    except NonAuRegionError as exc:
        raise HTTPException(
            status_code=422,
            detail=ProblemDetails.of(
                status=422,
                title="non-au-region-refused",
                detail="The signal source region is not approved for evidence storage.",
                type="https://ama.example/errors/non-au-region-refused",
            ).model_dump(),
        ) from exc
    except ValidationError as exc:
        raise RequestValidationError(exc.errors()) from exc


@router.get(
    "/audit/{value_id}",
    response_model=AuditTrace,
    operation_id="getAuditTraceForValue",
)
def get_audit_trace(
    value_id: str = Path(..., min_length=1, max_length=128),
    correlation_id: str = Depends(correlation_id_dep),
) -> AuditTrace:
    del correlation_id
    trace = build_trace(value_id)
    if trace is None:
        raise HTTPException(
            status_code=404,
            detail=ProblemDetails.of(
                title="audit-trace-not-found",
                status=404,
                detail=f"no entries for value_id={value_id}",
                type="https://ama.example/errors/audit-trace-not-found",
            ).model_dump(),
        )
    return trace


def _reject_mutation(
    request: Request,
    value_id: str,
    correlation_id: str,
) -> JSONResponse:
    if build_trace(value_id) is None:
        raise HTTPException(
            status_code=404,
            detail=ProblemDetails.of(
                status=404,
                title="audit-trace-not-found",
                detail=f"no entries for value_id={value_id}",
                type="https://ama.example/errors/audit-trace-not-found",
            ).model_dump(),
        )
    claims = getattr(request.state, "claims", {}) or {}
    actor = str(claims.get("oid") or claims.get("sub") or "anonymous")
    audit_manager.record_mutation_attempt(
        value_id=value_id,
        method=request.method,
        actor=actor,
        correlation_id=correlation_id,
    )
    return JSONResponse(
        status_code=409,
        content=ProblemDetails.of(
            status=409,
            title="audit-record-immutable",
            detail="Audit records cannot be modified or deleted (FR-040).",
            type="https://ama.example/errors/fr-040/audit-record-immutable",
        ).model_dump(),
        media_type="application/problem+json",
    )


@router.patch("/audit/{value_id}", operation_id="rejectAuditPatch")
def reject_audit_patch(
    request: Request,
    value_id: str = Path(..., min_length=1, max_length=128),
    correlation_id: str = Depends(correlation_id_dep),
) -> JSONResponse:
    return _reject_mutation(request, value_id, correlation_id)


@router.put("/audit/{value_id}", operation_id="rejectAuditPut")
def reject_audit_put(
    request: Request,
    value_id: str = Path(..., min_length=1, max_length=128),
    correlation_id: str = Depends(correlation_id_dep),
) -> JSONResponse:
    return _reject_mutation(request, value_id, correlation_id)


@router.delete("/audit/{value_id}", operation_id="rejectAuditDelete")
def reject_audit_delete(
    request: Request,
    value_id: str = Path(..., min_length=1, max_length=128),
    correlation_id: str = Depends(correlation_id_dep),
) -> JSONResponse:
    return _reject_mutation(request, value_id, correlation_id)
