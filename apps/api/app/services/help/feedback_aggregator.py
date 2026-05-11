"""spec-038 T-AA056 — feedback aggregator (FR-022a).

Auto-promotes a ContentReviewBacklogItem to ``needs_review`` when the target
accumulates ≥3 negative feedbacks within 30 days. NEVER auto-disables (Constitution Principle I).
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import UTC, datetime, timedelta

from ama_domain import (
    AUTO_PROMOTE_THRESHOLD,
    AUTO_PROMOTE_WINDOW_DAYS,
    ContentReviewBacklogItem,
    HelpFeedback,
)


def _negative_window(feedbacks: Iterable[HelpFeedback], now: datetime) -> list[HelpFeedback]:
    threshold = now - timedelta(days=AUTO_PROMOTE_WINDOW_DAYS)
    return [fb for fb in feedbacks if fb.rating == "not_helpful" and fb.created_at >= threshold]


def record_feedback(
    feedback: HelpFeedback,
    existing_item: ContentReviewBacklogItem | None,
    related_feedbacks: list[HelpFeedback],
) -> ContentReviewBacklogItem:
    """Upsert the backlog item for ``feedback``; auto-promote on threshold."""
    now = datetime.now(UTC)
    all_fb = list(related_feedbacks) + [feedback]
    neg_count = len(_negative_window(all_fb, now))
    target_kind = "article" if feedback.target_kind == "article" else "chat_pattern"
    target_id = feedback.target_id if feedback.target_kind == "article" else (feedback.pattern_id or feedback.target_id)
    if existing_item is None:
        item = ContentReviewBacklogItem(
            id=f"crbi-{target_kind}-{target_id}",
            tenant_id=feedback.tenant_id,
            target_kind=target_kind,
            target_id=target_id,
            feedback_ids=[fb.id for fb in all_fb],
            negative_count_30d=neg_count,
            status="needs_review" if neg_count >= AUTO_PROMOTE_THRESHOLD else "new",
            auto_promoted_at=now if neg_count >= AUTO_PROMOTE_THRESHOLD else None,
            created_at=now,
            updated_at=now,
        )
    else:
        promote = existing_item.status == "new" and neg_count >= AUTO_PROMOTE_THRESHOLD
        item = existing_item.model_copy(
            update={
                "feedback_ids": list({*existing_item.feedback_ids, feedback.id}),
                "negative_count_30d": neg_count,
                "status": "needs_review" if promote else existing_item.status,
                "auto_promoted_at": now if promote else existing_item.auto_promoted_at,
                "updated_at": now,
            }
        )
    # Constitution Principle I — never auto-disable content.
    assert item.status != "wont_change" or existing_item is not None
    return item


__all__ = ["record_feedback"]
