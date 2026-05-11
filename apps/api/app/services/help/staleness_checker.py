"""spec-038 T-AA055 — screenshot staleness checker (FR-010a / FR-010b)."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import UTC, datetime

from ama_domain import AnnotatedScreenshot, Callout, StalenessFlag, compute_screen_id_hash


def recompute_screenshot_hash(route_id: str, callouts: Iterable[Callout]) -> str:
    return compute_screen_id_hash(route_id, callouts)


def raise_or_clear_flag(
    screenshot: AnnotatedScreenshot,
    live_callouts: list[Callout],
    *,
    grace_release_id: str,
    existing_flag: StalenessFlag | None = None,
) -> StalenessFlag | None:
    """Return a staleness flag if the live hash diverges, or clear it.

    - returns the existing or newly-raised :class:`StalenessFlag` on mismatch
    - returns ``None`` when hashes match (clears prior flag implicitly)
    """
    live_hash = recompute_screenshot_hash(screenshot.route_id, live_callouts)
    if live_hash == screenshot.screen_id_hash:
        return None
    now = datetime.now(UTC)
    if existing_flag is None:
        return StalenessFlag(
            id=f"sf-{screenshot.id}-{int(now.timestamp())}",
            tenant_id=screenshot.tenant_id,
            target_kind="screenshot",
            target_id=screenshot.id,
            raised_reason="screen_id_hash_mismatch",
            raised_at=now,
            grace_release_id=grace_release_id,
        )
    return existing_flag


__all__ = ["recompute_screenshot_hash", "raise_or_clear_flag"]
