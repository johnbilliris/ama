"""Deterministic classifier gateway middleware (spec-035 T025).

Implements ADR-033 Layer 2 — deterministic regex+dictionary scan for PSPF
markings + AU-format PII patterns. PSPF wins over PII (deny outranks mask).

Branch outcomes:

- ``pspf`` or ``pspf+pii`` ⇒ deny with `403 sovereignty_denied`.
- ``pii`` (no PSPF) ⇒ mask in place (request body rewritten) + 200 path.
- classifier failure / timeout ⇒ fail-closed 503 ``sovereignty_denied``.
- ``clean`` ⇒ pass-through.

Position in stack: BEFORE entra_auth, so we never leak that an unauthenticated
caller reached a regulated route. Rate-limit applies AFTER auth.
"""

from __future__ import annotations

import json
import logging
import os
import re
from typing import Any

from app.middleware.envelope_response import error_to_envelope_response
from app.schemas.envelope_errors import ExtensionEnvelopeError
from app.schemas.extension_envelope import ExtensionErrorCode
from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

logger = logging.getLogger(__name__)


_PROTECTED_PREFIXES = (
    "/api/outcomes/",
    "/api/audit/list",
    "/api/auth/whoami",
    "/api/offline/replay",
    "/api/recovery/handover",
)


_PSPF_RE = re.compile(
    r"\b(OFFICIAL:\s*Sensitive|PROTECTED|SECRET|TOP\s*SECRET|IN-CONFIDENCE)\b",
    flags=re.IGNORECASE,
)


_PII_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("tfn", re.compile(r"\b\d{3}[ -]?\d{3}[ -]?\d{3}\b")),
    ("medicare", re.compile(r"\b[2-6]\d{3}[ -]?\d{5}[ -]?\d\b")),
    ("phone-au-mobile", re.compile(r"(?:\+?61\s?|0)4\d{2}[ -]?\d{3}[ -]?\d{3}")),
    ("email", re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")),
    ("dob", re.compile(r"\b\d{1,2}/\d{1,2}/\d{4}\b")),
    (
        "address",
        re.compile(r"\b\d+\s+[A-Z][a-z]+\s+(St|Street|Rd|Road|Ave|Avenue|Cres|Crescent|Pl|Place)\b"),
    ),
)


def _is_protected(path: str) -> bool:
    return any(path.startswith(prefix) for prefix in _PROTECTED_PREFIXES)


def _has_pspf(text: str) -> bool:
    return bool(_PSPF_RE.search(text))


def _mask_pii(text: str) -> tuple[str, int]:
    masked_text = text
    count = 0
    for label, pattern in _PII_PATTERNS:
        masked_text, replacements = pattern.subn(f"[MASKED:{label}]", masked_text)
        count += replacements
    return masked_text, count


class ClassifierGatewayMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if not _is_protected(request.url.path):
            return await call_next(request)

        if request.method.upper() not in {"POST", "PUT", "PATCH"}:
            return await call_next(request)

        try:
            body = await request.body()
        except Exception:
            logger.exception("classifier_gateway: failed to read body")
            return error_to_envelope_response(
                request,
                ExtensionEnvelopeError(
                    ExtensionErrorCode.SOVEREIGNTY_DENIED,
                    detail="classifier_failed: body unreadable",
                ),
            )

        text = body.decode("utf-8", errors="replace") if body else ""

        if text and _has_pspf(text):
            request.state.audit_extension_envelope = {
                "classifier_layer": 2,
                "content_class": "pspf",
            }
            request.state.audit_outcome = "classifier_deny"
            return error_to_envelope_response(
                request,
                ExtensionEnvelopeError(
                    ExtensionErrorCode.SOVEREIGNTY_DENIED,
                    detail="PSPF marking detected",
                ),
            )

        if text:
            masked, count = _mask_pii(text)
            if count > 0:
                request.state.audit_extension_envelope = {
                    "classifier_layer": 2,
                    "content_class": "pii",
                    "masked_field_count": count,
                }
                request.state.audit_outcome = "classifier_mask"
                request.state.classifier_masked_count = count
                rewritten = masked.encode("utf-8")
                request._body = rewritten  # type: ignore[attr-defined]

                async def _replay() -> dict[str, Any]:
                    return {"type": "http.request", "body": rewritten, "more_body": False}

                request._receive = _replay  # type: ignore[attr-defined]

        return await call_next(request)


def add_classifier_gateway_middleware(app: FastAPI) -> None:
    if os.environ.get("AMA_ENABLE_PRODUCTION_AUTH", "0") != "1":
        return
    app.add_middleware(ClassifierGatewayMiddleware)


# Re-exported for tests.
def classify_text(text: str) -> dict[str, Any]:
    if _has_pspf(text):
        return {"branch": "deny", "content_class": "pspf"}
    masked, count = _mask_pii(text)
    if count > 0:
        return {"branch": "mask", "content_class": "pii", "count": count, "masked": masked}
    return {"branch": "clean"}


__all__ = [
    "ClassifierGatewayMiddleware",
    "add_classifier_gateway_middleware",
    "classify_text",
]


_ = json  # pragma: no cover — explicit dependency marker for future structured payloads
