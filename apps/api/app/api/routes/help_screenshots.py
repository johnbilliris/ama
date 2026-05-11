"""spec-038 T-AA075 — screenshots staleness + signed URL routes."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Annotated, Literal
from uuid import uuid4

from app.api.routes.help_deps import CallerDep
from app.repositories.help_repositories import HelpRepositories, get_help_repositories
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

router = APIRouter(prefix="/help/screenshots", tags=["help-screenshots"])


class StalenessFlagWriteRequest(BaseModel):
    screen_id: str
    reason: str
    action: Literal["raise", "clear"] = "raise"


@router.get("/staleness")
async def list_staleness(
    caller: CallerDep,
    repos: Annotated[HelpRepositories, Depends(get_help_repositories)],
):
    return repos.list_staleness_flags(caller.tenant_id)


@router.post("/staleness", status_code=202)
async def write_staleness(
    body: StalenessFlagWriteRequest,
    caller: CallerDep,
    repos: Annotated[HelpRepositories, Depends(get_help_repositories)],
):
    row = {
        "id": str(uuid4()),
        "tenant_id": caller.tenant_id,
        "screen_id": body.screen_id,
        "reason": body.reason,
        "status": "open" if body.action == "raise" else "cleared",
        "raised_at": datetime.now(UTC).isoformat(),
        "raised_by": caller.user_id,
    }
    repos.upsert_staleness_flag(row)
    return {"status": "accepted", "flag_id": row["id"]}


@router.post("/staleness/{flag_id}/clear", status_code=202)
async def clear_staleness(
    flag_id: str,
    caller: CallerDep,
    repos: Annotated[HelpRepositories, Depends(get_help_repositories)],
):
    for f in repos.list_staleness_flags(caller.tenant_id):
        if f["id"] == flag_id:
            f["status"] = "cleared"
            repos.upsert_staleness_flag(f)
            return {"status": "cleared"}
    raise HTTPException(status_code=404, detail={"code": "flag.not_found", "message": "flag not found"})


@router.get("/{screen_id}/url")
async def signed_url(
    screen_id: str,
    caller: CallerDep,
    theme: Literal["light", "dark"] = Query(...),
):
    expires = datetime.now(UTC) + timedelta(minutes=5)
    return {
        "url": f"https://helpscreenshots.blob.core.windows.net/{screen_id}_{theme}.png?sig=placeholder&se={expires.isoformat()}",
        "expires_at": expires.isoformat(),
        "theme": theme,
    }


__all__ = ["router"]
