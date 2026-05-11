"""spec-038 T-AA076 — GET /help/search (full-text + glossary-first)."""

from __future__ import annotations

from typing import Annotated

from app.api.routes.help_deps import CallerDep
from app.repositories.help_repositories import HelpRepositories, get_help_repositories
from fastapi import APIRouter, Depends, Query

router = APIRouter(prefix="/help", tags=["help-search"])


@router.get("/search")
async def search(
    caller: CallerDep,
    repos: Annotated[HelpRepositories, Depends(get_help_repositories)],
    q: str = Query(min_length=1),
    persona: str | None = Query(default=None),
    limit: int = Query(default=20, le=100, ge=1),
):
    items = repos.list_articles(tenant_id=caller.tenant_id, persona=persona or caller.persona_id, limit=200)
    q_lower = q.lower()

    def score(article: dict) -> int:
        s = 0
        if article.get("kind") == "glossary" and q_lower in (article.get("term") or "").lower():
            s += 100
        if q_lower in (article.get("title") or "").lower():
            s += 50
        if q_lower in (article.get("summary") or "").lower():
            s += 25
        return s

    ranked = sorted((a for a in items if score(a) > 0), key=score, reverse=True)[:limit]
    return {"items": ranked, "query": q, "total": len(ranked)}


__all__ = ["router"]
