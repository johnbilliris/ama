"""spec-038 T-AA077 — support-handoff configuration."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated

from app.api.routes.help_deps import CallerDep
from app.repositories.help_repositories import HelpRepositories, get_help_repositories
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/help", tags=["help-support-handoff"])


class SupportHandoffRecord(BaseModel):
    id: str | None = None
    tenant_id: str | None = None
    label: str = Field(min_length=1, max_length=200)
    destination_url: str | None = None
    email: str | None = None
    phone: str | None = None
    hours_local: str | None = None
    updated_at: str | None = None


@router.get("/support-handoff")
async def get_handoff(
    caller: CallerDep,
    repos: Annotated[HelpRepositories, Depends(get_help_repositories)],
) -> dict[str, object]:
    row = repos.get_support_handoff(caller.tenant_id)
    if not row:
        raise HTTPException(
            status_code=404, detail={"code": "handoff.not_configured", "message": "no handoff configured"}
        )
    return row


@router.put("/support-handoff")
async def put_handoff(
    body: SupportHandoffRecord,
    caller: CallerDep,
    repos: Annotated[HelpRepositories, Depends(get_help_repositories)],
) -> dict[str, object]:
    row = body.model_dump()
    row["tenant_id"] = caller.tenant_id
    row["id"] = row.get("id") or caller.tenant_id
    row["updated_at"] = datetime.now(UTC).isoformat()
    repos.put_support_handoff(row)
    return row


__all__ = ["router"]
