from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SourcePollOutcome:
    source_id: str
    state: str
    reason: str
    retry_after_seconds: int | None = None


class SourceUnavailable(Exception):
    def __init__(
        self,
        source_id: str,
        reason: str,
        *,
        blocked: bool = False,
        retry_after_seconds: int | None = None,
    ) -> None:
        super().__init__(reason)
        self.source_id = source_id
        self.reason = reason
        self.blocked = blocked
        self.retry_after_seconds = retry_after_seconds
