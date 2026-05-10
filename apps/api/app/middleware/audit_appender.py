"""Audit-row emission middleware (spec-035 T016, Clarifications Q9).

Emits exactly **one** audit row per state-changing call (POST/PUT/PATCH/DELETE),
or a **paired** row pair when ``X-Impersonate-Persona`` is present.

Outcome attribution is opportunistic: route handlers may set
``request.state.audit_outcome`` to override the default ``approved`` /
``denied`` mapping. The middleware reads ``request.state.audit_outcome``,
``request.state.audit_extension_envelope``, ``request.state.audit_sc_id``
and ``request.state.audit_route`` if present, otherwise defaults are used.

The middleware NEVER blocks the response on audit-write failure: write errors
are logged and the response is returned untouched, since the upstream
``error_handler`` middleware already owns user-facing error mapping.
"""

from __future__ import annotations

import hashlib
import logging
import uuid
from typing import Any

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

logger = logging.getLogger(__name__)


_STATE_CHANGING_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


def _sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _claim(claims: dict[str, Any] | None, *keys: str, default: Any = None) -> Any:
    if not claims:
        return default
    for key in keys:
        if key in claims:
            return claims[key]
    return default


def _default_outcome(status_code: int) -> str:
    if 200 <= status_code < 300:
        return "approved"
    if status_code == 401:
        return "auth_unauthorized"
    if status_code == 403:
        return "auth_forbidden"
    if status_code == 422:
        return "schema_invalid"
    if status_code == 429:
        return "rate_limited"
    if status_code == 503:
        return "seed_not_ready"
    return "denied"


class AuditAppenderMiddleware(BaseHTTPMiddleware):
    """Emit one audit row per state-changing call; emit paired rows on impersonation."""

    def __init__(self, app: FastAPI, repository: Any | None = None) -> None:
        super().__init__(app)
        self._repository = repository

    def _get_repo(self) -> Any:
        if self._repository is None:
            from app.repositories.audit_repository import AuditRepository

            self._repository = AuditRepository()
        return self._repository

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.method not in _STATE_CHANGING_METHODS:
            return await call_next(request)

        body = await request.body()

        request_received = False

        async def _receive() -> dict[str, Any]:
            # F-A11/T240 — Starlette's BaseHTTPMiddleware framework re-invokes
            # ``receive`` for client-disconnect detection on streaming
            # responses (e.g. SSE). If we keep returning the original
            # ``http.request`` payload, the ASGI router raises
            # ``RuntimeError: Unexpected message received: http.request`` and
            # truncates the response. Return the buffered body once, then
            # signal disconnect on subsequent calls.
            nonlocal request_received
            if request_received:
                return {"type": "http.disconnect"}
            request_received = True
            return {"type": "http.request", "body": body, "more_body": False}

        request._receive = _receive  # type: ignore[attr-defined]

        request_hash = _sha256_hex(body) if body else "n/a"
        correlation_id = (
            request.headers.get("X-Correlation-Id") or request.headers.get("X-Request-Id") or str(uuid.uuid4())
        )
        request.state.correlation_id = correlation_id

        response = await call_next(request)

        try:
            await self._emit(request, response, request_hash, correlation_id)
        except Exception:  # noqa: BLE001
            logger.exception("audit_appender: failed to emit audit row(s)")

        return response

    async def _emit(
        self,
        request: Request,
        response: Response,
        request_hash: str,
        correlation_id: str,
    ) -> None:
        claims: dict[str, Any] = getattr(request.state, "claims", {}) or {}
        operator_identity = _claim(claims, "oid", "sub", default="anonymous")
        app_role = _claim(claims, "app_role", "appRole", default="observer-auditor")
        persona_id = _claim(claims, "persona_id", "personaId", default="anonymous")
        impersonate_target = request.headers.get("X-Impersonate-Persona")

        outcome = getattr(
            request.state,
            "audit_outcome",
            _default_outcome(response.status_code),
        )
        extension_envelope = getattr(request.state, "audit_extension_envelope", None)
        sc_id = getattr(request.state, "audit_sc_id", None)
        route = getattr(request.state, "audit_route", None) or request.url.path

        base_row: dict[str, Any] = {
            "outcome": outcome,
            "appRole": app_role,
            "operatorIdentity": operator_identity,
            "route": route,
            "scId": sc_id,
            "requestHash": request_hash,
            "responseHash": None,
            "extensionEnvelope": extension_envelope,
        }

        repo = self._get_repo()

        if impersonate_target:
            operator_row = {
                **base_row,
                "outcome": "admin_override",
                "personaId": "*",
                "impersonatedPersonaId": impersonate_target,
                "impersonatedBy": None,
            }
            target_row = {
                **base_row,
                "personaId": impersonate_target,
                "impersonatedPersonaId": None,
                "impersonatedBy": operator_identity,
            }
            await repo.append_paired(operator_row, target_row, correlation_id=correlation_id)
            return

        single_row = {
            **base_row,
            "personaId": "*" if app_role == "system-administrator" else persona_id,
            "impersonatedPersonaId": None,
            "impersonatedBy": None,
        }
        if app_role == "system-administrator":
            single_row["outcome"] = "admin_override"

        await repo.append(single_row, correlation_id=correlation_id)


def add_audit_appender_middleware(app: FastAPI, repository: Any | None = None) -> None:
    app.add_middleware(AuditAppenderMiddleware, repository=repository)


__all__ = [
    "AuditAppenderMiddleware",
    "add_audit_appender_middleware",
]
