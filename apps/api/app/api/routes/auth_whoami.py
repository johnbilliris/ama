"""``GET /api/auth/whoami`` route (spec-035 T029).

Reads ``request.state.claims`` populated by ``EntraAuthMiddleware`` and surfaces
the typed Principal shape per
[`contracts/auth-rbac.openapi.yaml`](../../../../specs/035-webapp-capstone-closure/contracts/auth-rbac.openapi.yaml).
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

router = APIRouter(prefix="/auth", tags=["auth"])


class ImpersonationBlock(BaseModel):
    model_config = ConfigDict(extra="forbid")
    impersonating: bool
    target_persona_id: str | None = Field(default=None)


class Principal(BaseModel):
    model_config = ConfigDict(extra="forbid")
    operator_identity: str
    app_role: str
    persona_id: str | None = None
    impersonation: ImpersonationBlock


@router.get("/whoami")
async def whoami(request: Request) -> JSONResponse:
    claims: dict[str, Any] = getattr(request.state, "claims", None) or {}
    operator = claims.get("oid") or claims.get("sub") or "anonymous"
    role = claims.get("app_role") or claims.get("appRole") or (claims.get("roles") or [None])[0]
    persona_id = claims.get("persona_id") or claims.get("personaId")
    impersonated = request.headers.get("X-Impersonate-Persona")

    body = Principal(
        operator_identity=str(operator),
        app_role=str(role) if role else "unknown",
        persona_id=persona_id if persona_id else None,
        impersonation=ImpersonationBlock(
            impersonating=bool(impersonated),
            target_persona_id=impersonated,
        ),
    ).model_dump()

    return JSONResponse(content=body, status_code=200)
