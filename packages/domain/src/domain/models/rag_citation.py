"""RagCitation domain model (spec-032 data-model.md E-02).

Embedded value type used in Recommendation.rag_sources to record the
handbook + chapter/page + chunk that grounded an LLM call.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class RagCitation(BaseModel):
    """Immutable citation record for a retrieved RAG chunk."""

    model_config = ConfigDict(extra="forbid")

    handbook_id: str = Field(min_length=3)
    chapter: str | None = None
    page: int | None = Field(default=None, ge=1)
    chunk_id: str = Field(min_length=1)
    score: float = Field(ge=0.0)
    quote: str = Field(max_length=500)

    def short_label(self) -> str:
        """Render a short human-readable citation (used in operator UI)."""
        if self.page is not None:
            return f"{self.handbook_id} §{self.chapter or '?'} p.{self.page}"
        if self.chapter:
            return f"{self.handbook_id} §{self.chapter}"
        return self.handbook_id
