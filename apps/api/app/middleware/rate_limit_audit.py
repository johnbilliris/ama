"""Rate-limit audit middleware (spec-035 T026).

APIM emits 429s for routes hitting per-(persona_id, route) or global ceilings.
APIM signals this via the internal ``X-Rate-Limit-Triggered: 1`` header on the
**response** path (set by the APIM rate-limit-by-key policy from
[`infra/modules/apim-rate-limit.bicep`](../../../../infra/modules/apim-rate-limit.bicep)).

When this middleware sees that header on a downstream response it:

1. Strips the internal header.
2. Replaces the body with the Q10 envelope `rate_limited`.
3. Sets the `Retry-After` header equal to `retry_after_seconds`.
4. Marks the request so audit_appender emits ``outcome=rate_limited``.

In addition, FastAPI-level testing fixtures can short-circuit the rate-limit by
setting ``request.state.fastapi_rate_limit_trigger`` (used by contract tests
that don't have APIM in front of them).
"""

from __future__ import annotations

import os
from typing import Any

from app.middleware.envelope_response import error_to_envelope_response
from app.schemas.envelope_errors import ExtensionEnvelopeError
from app.schemas.extension_envelope import ExtensionErrorCode
from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

_INTERNAL_HEADER = "X-Rate-Limit-Triggered"
_RETRY_AFTER_HEADER = "Retry-After"
_DEFAULT_RETRY_AFTER = 30


class RateLimitAuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        try:
            response: Response = await call_next(request)
        except ExtensionEnvelopeError as exc:
            return error_to_envelope_response(request, exc)

        triggered = response.headers.get(_INTERNAL_HEADER)
        forced = getattr(request.state, "fastapi_rate_limit_trigger", None)
        if triggered or forced:
            retry_after = _parse_retry_after(response.headers.get(_RETRY_AFTER_HEADER))
            if forced and isinstance(forced, dict):
                retry_after = int(forced.get("retry_after_seconds", retry_after))

            request.state.audit_outcome = "rate_limited"
            error = ExtensionEnvelopeError(
                ExtensionErrorCode.RATE_LIMITED,
                retry_after_seconds=retry_after,
            )
            return error_to_envelope_response(request, error)

        return response


def _parse_retry_after(value: str | None) -> int:
    try:
        return int(value) if value is not None else _DEFAULT_RETRY_AFTER
    except (TypeError, ValueError):
        return _DEFAULT_RETRY_AFTER


def add_rate_limit_audit_middleware(app: FastAPI) -> None:
    if os.environ.get("AMA_ENABLE_PRODUCTION_AUTH", "0") != "1":
        return
    app.add_middleware(RateLimitAuditMiddleware)


__all__ = ["RateLimitAuditMiddleware", "add_rate_limit_audit_middleware"]


_ = Any
