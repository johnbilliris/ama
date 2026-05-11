"""spec-038 entity — HelpArticle.

Pydantic v2 source-of-truth shape for the metadata record stored in Cosmos
container ``help_articles`` (partition key ``/tenant_id``). Body is MDX in
``apps/web/src/content/help/**``; full text is mirrored into AI Search by the
snapshot publisher.

See ``specs/038-help-docs-chat/data-model.md §1`` and FR-002 / FR-003.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

ArticleKind = Literal["article", "playbook", "faq", "glossary", "persona"]
ArticleStatus = Literal["draft", "published", "withdrawn"]
ArticleDomain = Literal[
    "getting-started",
    "persona-workflow",
    "screen-by-screen",
    "simulation-playbook",
    "agent-playbook",
    "audit-observer",
    "accessibility",
    "troubleshooting",
    "glossary",
]


class HelpArticle(BaseModel):
    """Published Help-article metadata."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., description="ULID; matches MDX file slug")
    tenant_id: str = Field(..., description="`__global__` for cross-tenant articles")
    kind: ArticleKind
    title: str
    slug: str
    persona_tags: list[str] = Field(default_factory=list)
    sector_tags: list[str] = Field(default_factory=list)
    surface_tags: list[str] = Field(default_factory=list)
    jurisdiction_tags: list[str] = Field(default_factory=list)
    domain: ArticleDomain
    body_uri: str = Field(..., description="repo-relative MDX path or signed URL")
    screenshot_ids: list[str] = Field(default_factory=list)
    snapshot_id: str
    version: int = Field(default=1, ge=1)
    status: ArticleStatus = "published"
    staleness_flag_id: str | None = None
    last_reviewed_at: datetime
    created_at: datetime
    updated_at: datetime
    etag: str | None = None
    glossary_term_links: list[str] = Field(default_factory=list)

    @field_validator("slug")
    @classmethod
    def _slug_kebab(cls, v: str) -> str:
        if not v or v != v.lower() or " " in v:
            raise ValueError("slug must be lowercase kebab-case")
        return v


__all__ = ["HelpArticle", "ArticleKind", "ArticleStatus", "ArticleDomain"]
