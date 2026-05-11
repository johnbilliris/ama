import uuid
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.middleware.spec_036_routes import is_problem_json_route

_ERROR_CATEGORY_BY_STATUS = {
    400: "validation_error",
    401: "authorization_error",
    403: "authorization_error",
    404: "not_found",
    422: "validation_error",
    429: "rate_limited",
}


def _error_category(status_code: int) -> str:
    if status_code >= 500:
        return "internal_error"
    return _ERROR_CATEGORY_BY_STATUS.get(status_code, "dependency_failure")


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
    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(request: Request, error: RequestValidationError) -> JSONResponse:
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
        details = [
            {"field": ".".join(str(item) for item in issue["loc"]), "reason": issue["msg"]} for issue in error.errors()
        ]
        return _error_response(
            status_code=422,
            message="Request validation failed",
            correlation_id=correlation_id,
            details=details,
            request=request,
        )

    @app.exception_handler(HTTPException)
    async def handle_http_error(request: Request, error: HTTPException) -> JSONResponse:
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
        return _error_response(
            status_code=error.status_code,
            message=str(error.detail),
            correlation_id=correlation_id,
            request=request,
        )

    @app.exception_handler(PermissionError)
    async def handle_permission_error(request: Request, error: PermissionError) -> JSONResponse:
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
        return _error_response(
            status_code=403,
            message=str(error),
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
    async def handle_sequence_exhausted(
        request: Request, error: SequenceAllocationExhausted
    ) -> JSONResponse:
        correlation_id = request.headers.get(
            "X-Correlation-ID", str(uuid.uuid4())
        )
        body: dict[str, Any] = {
            "type": "https://aidr.gov.au/problems/sequence-allocator-unavailable",
            "title": "Sequence allocator unavailable",
            "status": 503,
            "detail": str(error),
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
    async def handle_unexpected_error(request: Request, _: Exception) -> JSONResponse:
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
        return _error_response(
            status_code=500,
            message="Unexpected internal error occurred",
            correlation_id=correlation_id,
            request=request,
        )
