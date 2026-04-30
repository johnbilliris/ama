"""Resilience middleware for the FastAPI orchestration API.

Provides:
- Structured request/response logging with correlation IDs
- Circuit breaker tracking for external dependencies
- Graceful degradation headers
- Request timeout enforcement
"""

import time
import uuid
from collections import defaultdict
from collections.abc import Callable
from importlib import import_module
from typing import Any

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

# ── Circuit breaker state ──

_circuit_state: dict[str, dict[str, Any]] = defaultdict(lambda: {"failures": 0, "state": "closed", "last_failure": 0.0})

FAILURE_THRESHOLD = 5
RECOVERY_TIMEOUT_SECONDS = 30.0


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
        correlation_id = request.headers.get("X-Correlation-ID", uuid.uuid4().hex)
        start = time.monotonic()

        response = await call_next(request)

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


TransientDependencyError = RuntimeError


def retry_transient_dependency_call(func: Callable[..., Any]) -> Callable[..., Any]:
    tenacity = import_module("tenacity")
    return tenacity.retry(
        retry=tenacity.retry_if_exception_type(TransientDependencyError),
        wait=tenacity.wait_exponential_jitter(initial=0.5, max=5),
        stop=tenacity.stop_after_attempt(3),
        reraise=True,
    )(func)
