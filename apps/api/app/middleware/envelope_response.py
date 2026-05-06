"""Shared helper to convert ``ExtensionEnvelopeError`` to a ``Response``.

Lives in ``app.middleware`` (not ``app.schemas``) to avoid a circular-import
chain between ``schemas`` and ``starlette``-aware code.
"""

from __future__ import annotations

from app.schemas.envelope_errors import ExtensionEnvelopeError, error_to_response
from fastapi import Request, Response


def error_to_envelope_response(request: Request, error: ExtensionEnvelopeError) -> Response:
    return error_to_response(request, error)


__all__ = ["error_to_envelope_response"]
