"""spec-038 — shared dependencies for help routes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Header, HTTPException, Request


@dataclass(frozen=True)
class HelpCallerContext:
    tenant_id: str
    user_id: str
    persona_id: str
    persona_source: str
    jurisdiction_codes: list[str]
    accept_language: str


async def get_caller(
    request: Request,
    x_tenant_id: Annotated[str | None, Header(alias="X-Tenant-Id")] = None,
    x_user_id: Annotated[str | None, Header(alias="X-User-Id")] = None,
    x_persona_id: Annotated[str | None, Header(alias="X-Persona-Id")] = None,
    x_persona_source: Annotated[str | None, Header(alias="X-Persona-Source")] = None,
    x_jurisdictions: Annotated[str | None, Header(alias="X-Jurisdictions")] = None,
    accept_language: Annotated[str, Header(alias="Accept-Language")] = "en-AU",
) -> HelpCallerContext:
    """Decode tenant + persona claims from upstream IdP middleware headers.

    In tests these headers are set directly. In prod they're stamped by the
    Entra ID JWT middleware in :mod:`app.middleware`. When the explicit
    headers are absent we fall back to ``request.state.tenant_context`` and
    ``request.state.claims`` populated by the shared
    :class:`TenantMiddleware` / :class:`AuthMiddleware`, mirroring how every
    other API route resolves identity.
    """
    tenant_id = x_tenant_id
    user_id = x_user_id
    persona_id = x_persona_id
    persona_source = x_persona_source

    ctx = getattr(request.state, "tenant_context", None)
    if ctx is not None:
        tenant_id = tenant_id or getattr(ctx, "tenant_id", None)
        persona_id = persona_id or getattr(ctx, "persona_id", None)

    claims = getattr(request.state, "claims", None) or {}
    if not user_id:
        user_id = claims.get("sub") or claims.get("oid")
    if not persona_id:
        persona_id = claims.get("persona_id")

    if not tenant_id or not user_id:
        raise HTTPException(
            status_code=401, detail={"code": "auth.missing_tenant", "message": "tenant/user claim missing"}
        )
    return HelpCallerContext(
        tenant_id=tenant_id,
        user_id=user_id,
        persona_id=persona_id or "operational-default",
        persona_source=persona_source or "idp_default",
        jurisdiction_codes=[c for c in (x_jurisdictions or "").split(",") if c.strip()],
        accept_language=accept_language,
    )


CallerDep = Annotated[HelpCallerContext, Depends(get_caller)]
