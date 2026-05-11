"""Production-auth Q10 extension envelope helpers.

Single source of truth for:
- ``ExtensionEnvelopeError`` — the typed error raised by middleware/services.
- ``error_to_response()`` — converts an error to a ``JSONResponse`` with the
  HTTP status from ``ERROR_CODE_TO_HTTP_STATUS``, mirrored ``Retry-After``
  header on 429/503, and the byte-equal envelope body.
- ``build_envelope()`` — convenience constructor that fills in correlation_id /
  audit_id from request state when omitted.

See
[`contracts/production-auth-extension.contract.md`](../../../../specs/035-webapp-capstone-closure/contracts/production-auth-extension.contract.md).
"""

from __future__ import annotations

import uuid
from typing import Any

from app.schemas.extension_envelope import (
    ERROR_CODE_TO_HTTP_STATUS,
    ExtensionEnvelope,
    ExtensionErrorCode,
)
from fastapi import Request, Response
from fastapi.responses import JSONResponse


class ExtensionEnvelopeError(Exception):
    """Raised by middleware / services to short-circuit with a Q10 envelope."""

    def __init__(
        self,
        code: ExtensionErrorCode,
        *,
        retry_after_seconds: int | None = None,
        audit_id: str | None = None,
        correlation_id: str | None = None,
        detail: str | None = None,
    ) -> None:
        self.code = code
        self.retry_after_seconds = retry_after_seconds
        self.audit_id = audit_id
        self.correlation_id = correlation_id
        self.detail = detail
        super().__init__(detail or code.value)


def build_envelope(
    request: Request,
    error: ExtensionEnvelopeError,
) -> tuple[dict[str, Any], int, dict[str, str]]:
    """Build the ``(body, status_code, headers)`` triple for a Q10 envelope."""
    correlation_id = (
        error.correlation_id
        or getattr(request.state, "correlation_id", None)
        or request.headers.get("X-Correlation-Id")
        or str(uuid.uuid4())
    )
    audit_id = error.audit_id or str(uuid.uuid4())

    envelope = ExtensionEnvelope(
        error_code=error.code,
        retry_after_seconds=error.retry_after_seconds,
        audit_id=audit_id,
        correlation_id=correlation_id,
    )
    body = envelope.model_dump(mode="json")
    status = ERROR_CODE_TO_HTTP_STATUS[error.code]
    headers: dict[str, str] = {"X-Correlation-Id": correlation_id}
    if error.retry_after_seconds is not None:
        headers["Retry-After"] = str(error.retry_after_seconds)

    return body, status, headers


def error_to_response(request: Request, error: ExtensionEnvelopeError) -> Response:
    body, status, headers = build_envelope(request, error)
    return JSONResponse(content=body, status_code=status, headers=headers)


__all__ = ["ExtensionEnvelopeError", "build_envelope", "error_to_response"]
