import uuid
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

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


def _error_response(
    *,
    status_code: int,
    message: str,
    correlation_id: str,
    details: list[dict[str, Any]] | None = None,
) -> JSONResponse:
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
    async def handle_validation_error(
        request: Request, error: RequestValidationError
    ) -> JSONResponse:
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
        details = [
            {"field": ".".join(str(item) for item in issue["loc"]), "reason": issue["msg"]}
            for issue in error.errors()
        ]
        return _error_response(
            status_code=422,
            message="Request validation failed",
            correlation_id=correlation_id,
            details=details,
        )

    @app.exception_handler(HTTPException)
    async def handle_http_error(request: Request, error: HTTPException) -> JSONResponse:
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
        return _error_response(
            status_code=error.status_code,
            message=str(error.detail),
            correlation_id=correlation_id,
        )

    @app.exception_handler(PermissionError)
    async def handle_permission_error(request: Request, error: PermissionError) -> JSONResponse:
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
        return _error_response(
            status_code=403,
            message=str(error),
            correlation_id=correlation_id,
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, _: Exception) -> JSONResponse:
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
        return _error_response(
            status_code=500,
            message="Unexpected internal error occurred",
            correlation_id=correlation_id,
        )
