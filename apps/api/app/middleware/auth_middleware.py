import base64
import json
import logging
from typing import Any

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

logger = logging.getLogger(__name__)

DEFAULT_CLAIMS: dict[str, Any] = {
    "sub": "anonymous",
    "agency_id": "unknown-agency",
    "jurisdiction_ids": [],
    "roles": ["SimulationUser"],
}


class AuthMiddleware(BaseHTTPMiddleware):
    """Populate request.state.claims from Container Apps EasyAuth headers or defaults."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        claims = _extract_claims_from_headers(request)
        request.state.claims = claims if claims else dict(DEFAULT_CLAIMS)
        return await call_next(request)


def _extract_claims_from_headers(request: Request) -> dict[str, Any] | None:
    principal_header = request.headers.get("X-MS-CLIENT-PRINCIPAL")
    if principal_header:
        try:
            decoded = base64.b64decode(principal_header)
            return json.loads(decoded)
        except Exception:
            logger.warning("Failed to decode X-MS-CLIENT-PRINCIPAL header")
            return None

    claims_header = request.headers.get("X-MS-CLIENT-PRINCIPAL-ID")
    if claims_header:
        return {
            "sub": claims_header,
            "agency_id": request.headers.get("X-MS-CLIENT-PRINCIPAL-NAME", "unknown-agency"),
            "jurisdiction_ids": [],
            "roles": [],
        }

    return None


def add_auth_middleware(app: FastAPI) -> None:
    app.add_middleware(AuthMiddleware)
