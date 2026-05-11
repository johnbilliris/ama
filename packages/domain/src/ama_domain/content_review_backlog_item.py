"""spec-038 entity — ContentReviewBacklogItem. FR-022a.

Auto-promotion threshold: ≥3 negative feedbacks within 30 days on the same
target (article_id or chat pattern_id). NEVER auto-disables — Constitution
Principle I forbids silencing safety-relevant guidance.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

AUTO_PROMOTE_THRESHOLD = 3
AUTO_PROMOTE_WINDOW_DAYS = 30


class ContentReviewBacklogItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    tenant_id: str
    target_kind: Literal["article", "chat_pattern"]
    target_id: str
    feedback_ids: list[str] = Field(default_factory=list)
    negative_count_30d: int = Field(default=0, ge=0)
    status: Literal["new", "needs_review", "in_review", "resolved", "wont_change"] = "new"
    auto_promoted_at: datetime | None = None
    resolved_by: str | None = None
    resolved_snapshot_id: str | None = None
    created_at: datetime
    updated_at: datetime


__all__ = ["ContentReviewBacklogItem", "AUTO_PROMOTE_THRESHOLD", "AUTO_PROMOTE_WINDOW_DAYS"]
