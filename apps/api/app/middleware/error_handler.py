import logging
import uuid
from typing import Any

from app.middleware.spec_036_routes import is_problem_json_route
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)

_ERROR_CATEGORY_BY_STATUS = {
    400: "validation_error",
    401: "authorization_error",
    403: "authorization_error",
    404: "not_found",
    405: "validation_error",
    422: "validation_error",
    429: "rate_limited",
}


def _error_category(status_code: int) -> str:
    if status_code >= 500:
        return "internal_error"
    return _ERROR_CATEGORY_BY_STATUS.get(status_code, "dependency_failure")


def _correlation_id(request: Request) -> str:
    existing = getattr(request.state, "correlation_id", None)
    if existing:
        return str(existing)
    evidence_correlation_id = request.headers.get("x-ama-correlation-id", "").strip()
    if evidence_correlation_id:
        return evidence_correlation_id[:128]
    try:
        return str(uuid.UUID(request.headers.get("X-Correlation-ID", "")))
    except (ValueError, TypeError, AttributeError):
        return str(uuid.uuid4())


def _safe_message(status_code: int) -> str:
    if status_code == 400:
        return "Request could not be processed"
    if status_code == 401:
        return "Authentication is required"
    if status_code == 403:
        return "You are not authorized to perform this action"
    if status_code == 404:
        return "Requested resource was not found"
    if status_code == 405:
        return "HTTP method is not allowed for this endpoint"
    if status_code == 409:
        return "Request conflicts with current resource state"
    if status_code == 422:
        return "Request validation failed"
    if status_code == 429:
        return "Too many requests; please retry later"
    if status_code >= 500:
        return "Unexpected internal error occurred"
    return "Request failed"


def _matched_route_template(request: Request) -> str | None:
    """Return the FastAPI route template (e.g. ``/api/simulations/{sim_id}/abort``).

    Falls back to ``None`` when FastAPI has not yet resolved a route match
    (e.g. during 404 dispatch). Used by Cycle 2 / Amendment A2-05 to decide
    between RFC 9457 ``application/problem+json`` and the legacy envelope.
    """

    route = request.scope.get("route") if request.scope else None
    if route is None:
        return None
    return getattr(route, "path", None)


def _problem_type_for(status_code: int, message: str) -> tuple[str, str]:
    """Return (type_uri, title) for a generic spec-036 problem detail.

    Specific problem types (lifecycle-state-conflict, idempotency-key-conflict,
    sequence-allocator-unavailable, etc.) are emitted by their own dedicated
    handlers; this fallback covers generic 4xx / 5xx within the allow-list.
    """

    if status_code == 401 or status_code == 403:
        return (
            "https://aidr.gov.au/problems/authorization-error",
            "Authorisation error",
        )
    if status_code == 404:
        return (
            "https://aidr.gov.au/problems/not-found",
            "Resource not found",
        )
    if status_code == 422:
        return (
            "https://aidr.gov.au/problems/validation-error",
            "Validation error",
        )
    if status_code == 429:
        return (
            "https://aidr.gov.au/problems/rate-limited",
            "Rate limited",
        )
    if status_code >= 500:
        return (
            "https://aidr.gov.au/problems/internal-error",
            "Internal error",
        )
    return (
        "https://aidr.gov.au/problems/spec-036-error",
        message or "Request error",
    )


def _problem_response(
    *,
    status_code: int,
    message: str,
    correlation_id: str,
    details: list[dict[str, Any]] | None = None,
) -> JSONResponse:
    """Cycle 2 / Amendment A2-05 / FR-066 — RFC 9457 problem details.

    Used for 4xx **and** 5xx responses on routes enumerated in
    :data:`apps.api.app.middleware.spec_036_routes.SPEC_036_PROBLEM_JSON_ROUTES`
    per pass-2 Q5 (split scope rejected because ADR-036-007's
    ``sequence-uncertainty`` problem-detail is HTTP 503 5xx and is already
    enumerated as RFC 9457).
    """

    problem_type, title = _problem_type_for(status_code, message)
    body: dict[str, Any] = {
        "type": problem_type,
        "title": title,
        "status": status_code,
        "detail": message,
        "correlationId": correlation_id,
    }
    if details:
        body["errors"] = details
    return JSONResponse(
        status_code=status_code,
        content=body,
        media_type="application/problem+json",
    )


def _is_evidence_request(request: Request) -> bool:
    return request.url.path.startswith(("/api/v1/evidence", "/api/healthz/evidence"))


def _evidence_problem_response(
    *,
    request: Request,
    status_code: int,
    correlation_id: str,
    title: str,
    detail: str,
    type_uri: str,
    errors: list[dict[str, Any]] | None = None,
) -> JSONResponse:
    body: dict[str, Any] = {
        "type": type_uri,
        "title": title,
        "status": status_code,
        "detail": detail,
        "instance": request.url.path,
        "ama_advisory_only": True,
    }
    if errors:
        body["errors"] = errors
    return JSONResponse(
        status_code=status_code,
        content=body,
        media_type="application/problem+json",
        headers={"x-ama-correlation-id": correlation_id},
    )


def _error_response(
    *,
    status_code: int,
    message: str,
    correlation_id: str,
    details: list[dict[str, Any]] | None = None,
    request: Request | None = None,
) -> JSONResponse:
    """Dispatch to RFC 9457 or the legacy envelope per the allow-list.

    The allow-list (Cycle 2 Amendment A2-05) is checked AFTER FastAPI path
    parameter normalisation so the comparison is between the route template
    (e.g. ``/api/simulations/{sim_id}/abort``) and the frozenset literals.
    Non-matches and route-less paths fall back to the legacy envelope so
    spec 024 / healthchecks / scaffolding endpoints remain unchanged
    (constitution Principle V).
    """

    if request is not None and is_problem_json_route(_matched_route_template(request)):
        return _problem_response(
            status_code=status_code,
            message=message,
            correlation_id=correlation_id,
            details=details,
        )
    payload: dict[str, Any] = {
        "correlationId": correlation_id,
        "statusCode": status_code,
        "errorCategory": _error_category(status_code),
        "message": message,
    }
    if details:
        payload["details"] = details
    return JSONResponse(status_code=status_code, content=payload)


def add_error_handler_middleware(app: FastAPI) -> None:
    from app.services.evidence.audit_writer import AuditWriteUnavailableError

    @app.exception_handler(AuditWriteUnavailableError)
    async def handle_audit_write_unavailable(
        request: Request,
        error: AuditWriteUnavailableError,
    ) -> JSONResponse:
        correlation_id = _correlation_id(request)
        problem = error.to_problem_details()
        return _evidence_problem_response(
            request=request,
            status_code=503,
            correlation_id=correlation_id,
            title=problem.title,
            detail=problem.detail or _safe_message(503),
            type_uri=problem.type,
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(request: Request, error: RequestValidationError) -> JSONResponse:
        correlation_id = _correlation_id(request)
        details = [
            {"field": ".".join(str(item) for item in issue["loc"]), "reason": issue["msg"]} for issue in error.errors()
        ]
        if _is_evidence_request(request):
            has_extra = any(issue.get("type") == "extra_forbidden" for issue in error.errors())
            title = "request-body-extra-fields" if has_extra else "request-validation-failed"
            return _evidence_problem_response(
                request=request,
                status_code=422,
                correlation_id=correlation_id,
                title=title,
                detail="Request validation failed.",
                type_uri=f"https://ama.example/errors/{title}",
                errors=details,
            )
        return _error_response(
            status_code=422,
            message="Request validation failed",
            correlation_id=correlation_id,
            details=details,
            request=request,
        )

    @app.exception_handler(HTTPException)
    @app.exception_handler(StarletteHTTPException)
    async def handle_http_error(request: Request, error: StarletteHTTPException) -> JSONResponse:
        correlation_id = _correlation_id(request)
        logger.warning(
            "http_exception_handled",
            extra={
                "correlation_id": correlation_id,
                "status_code": error.status_code,
                "raw_detail": str(error.detail),
            },
        )
        if _is_evidence_request(request):
            if isinstance(error.detail, dict):
                payload = error.detail
                title = str(payload.get("title") or "request-failed")
                detail = str(payload.get("detail") or _safe_message(error.status_code))
                type_uri = str(payload.get("type") or f"https://ama.example/errors/{title}")
            else:
                title = "resource-not-found" if error.status_code == 404 else "request-failed"
                detail = _safe_message(error.status_code)
                type_uri = f"https://ama.example/errors/{title}"
            return _evidence_problem_response(
                request=request,
                status_code=error.status_code,
                correlation_id=correlation_id,
                title=title,
                detail=detail,
                type_uri=type_uri,
            )
        return _error_response(
            status_code=error.status_code,
            message=_safe_message(error.status_code),
            correlation_id=correlation_id,
            request=request,
        )

    @app.exception_handler(PermissionError)
    async def handle_permission_error(request: Request, error: PermissionError) -> JSONResponse:
        correlation_id = _correlation_id(request)
        logger.warning(
            "permission_error_handled",
            extra={
                "correlation_id": correlation_id,
                "raw_detail": str(error),
            },
        )
        if _is_evidence_request(request):
            return _evidence_problem_response(
                request=request,
                status_code=403,
                correlation_id=correlation_id,
                title="forbidden",
                detail=_safe_message(403),
                type_uri="https://ama.example/errors/forbidden",
            )
        return _error_response(
            status_code=403,
            message=_safe_message(403),
            correlation_id=correlation_id,
            request=request,
        )

    # FR-048 fail-closed surface for sequence-allocator exhaustion (T-N04).
    # Surfaced as RFC 9457 ``application/problem+json`` with HTTP 503 +
    # ``Retry-After: 5``. The DLQ envelope (``sequence_number=-1``) is
    # already buffered by ``audit_writer.AuditWriter`` before the
    # exception is raised; this handler is purely the HTTP boundary.
    from app.repositories.simulation_sequence_repository import (
        SequenceAllocationExhausted,
    )

    @app.exception_handler(SequenceAllocationExhausted)
    async def handle_sequence_exhausted(request: Request, error: SequenceAllocationExhausted) -> JSONResponse:
        correlation_id = _correlation_id(request)
        logger.warning(
            "sequence_allocator_exhausted",
            extra={
                "correlation_id": correlation_id,
                "raw_detail": str(error),
            },
        )
        body: dict[str, Any] = {
            "type": "https://aidr.gov.au/problems/sequence-allocator-unavailable",
            "title": "Sequence allocator unavailable",
            "status": 503,
            "detail": _safe_message(503),
            "correlationId": correlation_id,
            "retry_after_seconds": 5,
        }
        return JSONResponse(
            status_code=503,
            content=body,
            media_type="application/problem+json",
            headers={"Retry-After": "5"},
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, error: Exception) -> JSONResponse:
        correlation_id = _correlation_id(request)
        logger.exception(
            "unexpected_error_handled",
            extra={"correlation_id": correlation_id, "error_type": type(error).__name__},
        )
        if _is_evidence_request(request):
            return _evidence_problem_response(
                request=request,
                status_code=500,
                correlation_id=correlation_id,
                title="internal-error",
                detail=_safe_message(500),
                type_uri="https://ama.example/errors/internal-error",
            )
        return _error_response(
            status_code=500,
            message=_safe_message(500),
            correlation_id=correlation_id,
            request=request,
        )
