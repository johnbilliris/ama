import base64
import json
import logging
import os
from typing import Any

from app.core.dev_access import dev_access_claims, dev_access_enabled
from app.middleware.envelope_response import error_to_envelope_response
from app.schemas.envelope_errors import ExtensionEnvelopeError
from app.schemas.extension_envelope import ExtensionErrorCode
from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

logger = logging.getLogger(__name__)

DEFAULT_CLAIMS: dict[str, Any] = {
    "sub": "anonymous",
    "agency_id": "unknown-agency",
    "jurisdiction_ids": [],
    "roles": ["SimulationUser"],
}

_AUTHENTICATED_PREFIXES = ("/api/simulations", "/api/incidents", "/api/personas")
_INCIDENT_MAP_PATH = "/api/incidents/map"
_ANONYMOUS_INCIDENT_MAP_METHODS = frozenset({"GET", "HEAD"})
_NON_PRODUCTION_ENVIRONMENTS = frozenset({"dev", "development", "test"})


class AuthMiddleware(BaseHTTPMiddleware):
    """Populate request claims from identity or an explicitly enabled dev principal."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if dev_access_enabled():
            request.state.claims = dev_access_claims()
            return await call_next(request)

        existing_claims = getattr(request.state, "claims", None) or {}
        claims = _extract_claims_from_headers(request)
        if existing_claims:
            if claims:
                request.state.claims = {**claims, **existing_claims}
            else:
                request.state.claims = existing_claims
        elif claims:
            request.state.claims = claims
        elif _anonymous_simulation_enabled() and request.url.path.startswith("/api/simulations"):
            request.state.claims = dict(DEFAULT_CLAIMS)
        elif _anonymous_incident_map_enabled(request):
            request.state.claims = dict(DEFAULT_CLAIMS)
        elif request.url.path.startswith(_AUTHENTICATED_PREFIXES):
            return error_to_envelope_response(
                request,
                ExtensionEnvelopeError(
                    ExtensionErrorCode.UNAUTHORIZED,
                    detail="authenticated principal is required",
                ),
            )
        else:
            request.state.claims = {}
        return await call_next(request)


def _extract_claims_from_headers(request: Request) -> dict[str, Any] | None:
    trusted_test_identity = _trusted_test_identity_enabled()
    principal_header = request.headers.get("X-MS-CLIENT-PRINCIPAL")
    if principal_header:
        if not trusted_test_identity:
            logger.warning("Ignoring forwarded principal header because trusted test support is not enabled")
            return None
        try:
            decoded = base64.b64decode(principal_header)
            return json.loads(decoded)
        except Exception:
            logger.warning("Failed to decode X-MS-CLIENT-PRINCIPAL header")
            return None

    claims_header = request.headers.get("X-MS-CLIENT-PRINCIPAL-ID")
    if claims_header:
        if not trusted_test_identity:
            logger.warning("Ignoring forwarded principal ID because trusted test support is not enabled")
            return None
        return {
            "oid": claims_header,
            "agency_id": request.headers.get("X-MS-CLIENT-PRINCIPAL-NAME", "unknown-agency"),
            "jurisdiction_ids": [],
            "roles": [],
        }

    return None


def _trusted_test_identity_enabled() -> bool:
    if (
        os.environ.get("AMA_ENABLE_PRODUCTION_AUTH", "0") == "1"
        or os.environ.get("AMA_ENABLE_INCIDENT_MAP_AUTH", "0") == "1"
    ):
        return False
    trust_forwarded = os.environ.get("AMA_TRUST_FORWARDED_PRINCIPAL", "0") == "1"
    test_support_enabled = os.environ.get("AMA_TEST_SUPPORT", "0") == "1"
    test_environment = os.environ.get("AMA_ENVIRONMENT", "").lower() == "test"
    return trust_forwarded and (test_support_enabled or test_environment)


def _anonymous_simulation_enabled() -> bool:
    environment = os.environ.get("AMA_ENVIRONMENT", "development").lower()
    return (
        os.environ.get("AMA_ENABLE_PRODUCTION_AUTH", "0") != "1"
        and environment in {"dev", "development", "test"}
        and os.environ.get("AMA_ALLOW_ANONYMOUS_SIMULATION", "0") == "1"
    )


def _anonymous_incident_map_enabled(request: Request) -> bool:
    environment = os.environ.get("AMA_ENVIRONMENT", "development").lower()
    return (
        os.environ.get("AMA_ALLOW_ANONYMOUS_INCIDENT_MAP", "0") == "1"
        and os.environ.get("AMA_ENABLE_PRODUCTION_AUTH", "0") != "1"
        and environment in _NON_PRODUCTION_ENVIRONMENTS
        and request.method in _ANONYMOUS_INCIDENT_MAP_METHODS
        and request.url.path == _INCIDENT_MAP_PATH
    )


def add_auth_middleware(app: FastAPI) -> None:
    app.add_middleware(AuthMiddleware)
