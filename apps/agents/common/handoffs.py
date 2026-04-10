import time
from collections.abc import Callable
from datetime import UTC, datetime
from uuid import uuid4

from pydantic import BaseModel, Field


class AgentHandoffEvent(BaseModel):
    handoff_id: str
    incident_id: str
    source_agent: str
    target_agent: str
    scope_key: str
    confidence: float
    payload: dict[str, object]
    tenant_id: str = "live"
    status: str = "pending"
    retry_count: int = 0
    max_retries: int = 3
    retry_window_seconds: int = 300
    next_retry_at: datetime | None = None
    timeline_event_id: str | None = None
    dead_letter_entry_id: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    delivered_at: datetime | None = None
    failed_at: datetime | None = None
    failure_reason: str | None = None


def build_handoff(
    *,
    incident_id: str,
    source_agent: str,
    target_agent: str,
    scope_key: str,
    payload: dict[str, object],
    confidence: float,
    tenant_id: str = "live",
) -> AgentHandoffEvent:
    return AgentHandoffEvent(
        handoff_id=f"handoff-{uuid4().hex}",
        incident_id=incident_id,
        source_agent=source_agent,
        target_agent=target_agent,
        scope_key=scope_key,
        payload=payload,
        confidence=confidence,
        tenant_id=tenant_id,
    )


def deliver_handoff_with_retry(
    *,
    handoff: AgentHandoffEvent,
    deliver: Callable[[AgentHandoffEvent], None],
    on_dead_letter: Callable[[AgentHandoffEvent], str],
    max_retries: int = 3,
    retry_window_seconds: int = 300,
) -> AgentHandoffEvent:
    handoff.max_retries = max_retries
    handoff.retry_window_seconds = retry_window_seconds
    retry_sleep = max(1, retry_window_seconds // max(1, max_retries))

    for attempt in range(1, max_retries + 1):
        try:
            deliver(handoff)
            handoff.status = "delivered"
            handoff.retry_count = attempt - 1
            handoff.delivered_at = datetime.now(UTC)
            return handoff
        except Exception as error:
            handoff.status = "retrying" if attempt < max_retries else "failed"
            handoff.retry_count = attempt
            handoff.failure_reason = str(error)
            handoff.next_retry_at = datetime.now(UTC)
            if attempt < max_retries:
                time.sleep(retry_sleep)

    handoff.status = "dead_lettered"
    handoff.failed_at = datetime.now(UTC)
    handoff.dead_letter_entry_id = on_dead_letter(handoff)
    return handoff
