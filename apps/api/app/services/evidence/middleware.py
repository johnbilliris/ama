from __future__ import annotations

import uuid

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from ._correlation import HEADER_NAME

_EVIDENCE_PREFIXES = ("/api/v1/evidence", "/api/healthz/evidence")


class EvidenceContractMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if not request.url.path.startswith(_EVIDENCE_PREFIXES):
            return await call_next(request)

        incoming = request.headers.get(HEADER_NAME, "").strip()
        correlation_id = incoming[:128] if incoming else uuid.uuid4().hex
        request.state.correlation_id = correlation_id
        response = await call_next(request)
        response.headers[HEADER_NAME] = correlation_id
        return response


def add_evidence_contract_middleware(app: FastAPI) -> None:
    app.add_middleware(EvidenceContractMiddleware)
