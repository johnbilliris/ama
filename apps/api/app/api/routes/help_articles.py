"""spec-038 T-AA073 — GET /help/articles + GET /help/articles/{slug}."""

from __future__ import annotations

import hashlib
from typing import Annotated, Literal

from app.api.routes.help_deps import CallerDep
from app.repositories.help_repositories import HelpRepositories, get_help_repositories
from fastapi import APIRouter, Depends, Header, HTTPException, Query, Response

router = APIRouter(prefix="/help", tags=["help-articles"])


@router.get("/articles")
async def list_articles(
    caller: CallerDep,
    repos: Annotated[HelpRepositories, Depends(get_help_repositories)],
    persona: str | None = Query(default=None),
    surface: str | None = Query(default=None),
    kind: Literal["article", "playbook", "faq", "glossary", "persona"] | None = Query(default=None),
    limit: int = Query(default=50, le=200, ge=1),
    continuation: str | None = Query(default=None),
):
    items = repos.list_articles(
        tenant_id=caller.tenant_id,
        persona=persona or caller.persona_id,
        surface=surface,
        kind=kind,
        limit=limit,
    )
    return {"items": items, "continuation": None}


@router.get("/articles/{slug}")
async def get_article(
    slug: str,
    caller: CallerDep,
    response: Response,
    repos: Annotated[HelpRepositories, Depends(get_help_repositories)],
    if_none_match: Annotated[str | None, Header(alias="If-None-Match")] = None,
):
    article = repos.get_article(tenant_id=caller.tenant_id, slug=slug)
    if not article:
        raise HTTPException(status_code=404, detail={"code": "article.not_found", "message": "not found"})
    etag = (
        '"'
        + hashlib.sha256(f"{article.get('id', slug)}|{article.get('updated_at', '')}".encode()).hexdigest()[:16]
        + '"'
    )
    if if_none_match == etag:
        response.status_code = 304
        return None
    response.headers["ETag"] = etag
    return article


__all__ = ["router"]
