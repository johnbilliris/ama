"""Resilience middleware for the FastAPI orchestration API.

Provides:
- Structured request/response logging with correlation IDs
- Circuit breaker tracking for external dependencies
- Graceful degradation headers
- Request timeout enforcement
"""

import asyncio
import time
import uuid
from collections import defaultdict
from collections.abc import Callable
from importlib import import_module
from typing import Any, cast

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

# ── Circuit breaker state ──

_circuit_state: dict[str, dict[str, Any]] = defaultdict(lambda: {"failures": 0, "state": "closed", "last_failure": 0.0})

FAILURE_THRESHOLD = 5
RECOVERY_TIMEOUT_SECONDS = 30.0
REQUEST_TIMEOUT_SECONDS = 10.0


def _resolve_correlation_id(raw_value: str | None) -> str:
    if raw_value:
        try:
            return str(uuid.UUID(raw_value))
        except (ValueError, AttributeError, TypeError):
            pass
    return str(uuid.uuid4())


def check_circuit(dependency: str) -> bool:
    """Return True if the circuit for *dependency* is closed (healthy)."""
    entry = _circuit_state[dependency]
    if entry["state"] == "closed":
        return True
    if entry["state"] == "open":
        if time.monotonic() - entry["last_failure"] > RECOVERY_TIMEOUT_SECONDS:
            entry["state"] = "half_open"
            return True
        return False
    # half_open — allow one probe
    return True


def record_success(dependency: str) -> None:
    entry = _circuit_state[dependency]
    entry["failures"] = 0
    entry["state"] = "closed"


def record_failure(dependency: str) -> None:
    entry = _circuit_state[dependency]
    entry["failures"] += 1
    entry["last_failure"] = time.monotonic()
    if entry["failures"] >= FAILURE_THRESHOLD:
        entry["state"] = "open"


# ── Middleware ──


class ResilienceMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        correlation_id = _resolve_correlation_id(request.headers.get("X-Correlation-ID"))
        request.state.correlation_id = correlation_id
        start = time.monotonic()

        try:
            response = await asyncio.wait_for(call_next(request), timeout=REQUEST_TIMEOUT_SECONDS)
        except TimeoutError:
            elapsed_ms = round((time.monotonic() - start) * 1000, 1)
            timeout_response = JSONResponse(
                status_code=504,
                content={
                    "correlationId": correlation_id,
                    "statusCode": 504,
                    "errorCategory": "dependency_failure",
                    "message": "Request timed out",
                    "timeoutSeconds": REQUEST_TIMEOUT_SECONDS,
                },
            )
            timeout_response.headers["X-Correlation-ID"] = correlation_id
            timeout_response.headers["X-Response-Time-Ms"] = str(elapsed_ms)
            return timeout_response

        elapsed_ms = round((time.monotonic() - start) * 1000, 1)
        response.headers["X-Correlation-ID"] = correlation_id
        response.headers["X-Response-Time-Ms"] = str(elapsed_ms)

        # Surface degraded-mode hint when any circuit is open
        if any(entry["state"] == "open" for entry in _circuit_state.values()):
            response.headers["X-Degraded-Mode"] = "true"

        return response


def add_resilience_middleware(app: FastAPI) -> None:
    """Wire all resilience middleware onto *app*."""
    app.add_middleware(ResilienceMiddleware)


class TransientDependencyError(Exception):
    """Explicit marker for dependency failures that should be retried."""


_RETRYABLE_STATUS_CODES = {408, 409, 425, 429, 500, 502, 503, 504}


def _is_retryable_dependency_exception(error: BaseException) -> bool:
    if isinstance(error, TransientDependencyError):
        return True

    status_code = getattr(error, "status_code", None)
    if isinstance(status_code, int) and status_code in _RETRYABLE_STATUS_CODES:
        return True

    status = getattr(error, "status", None)
    if isinstance(status, int) and status in _RETRYABLE_STATUS_CODES:
        return True

    type_name = type(error).__name__
    retryable_type_names = {
        "ServiceRequestError",
        "ServiceResponseError",
        "AzureError",
        "CosmosHttpResponseError",
        "CosmosClientTimeoutError",
        "ConnectionError",
        "TimeoutError",
        "BusyLoadingError",
    }
    return type_name in retryable_type_names


def retry_transient_dependency_call[**P, R](func: Callable[P, R]) -> Callable[P, R]:
    tenacity = import_module("tenacity")
    retry = tenacity.retry(
        retry=tenacity.retry_if_exception(_is_retryable_dependency_exception),
        wait=tenacity.wait_exponential_jitter(initial=0.5, max=5),
        stop=tenacity.stop_after_attempt(3),
        reraise=True,
    )
    return cast(Callable[P, R], retry(func))
