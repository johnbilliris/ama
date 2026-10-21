from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class TimelineEvent(BaseModel):
    model_config = ConfigDict(frozen=True)

    event_id: str
    incident_id: str
    event_type: Literal[
        "signal",
        "recommendation",
        "approval",
        "alert",
        "ingestion",
        "publication",
        "supersession",
        "delivery",
        "task_status",
        "task",
        "system",
        "handoff",
        "dead_letter",
        "llm_call",
    ]
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    summary: str
    actor: str
    verified_actor: str | None = None
    tenant_id: str | None = None
    mode: Literal["live", "rehearsal"] | None = None
    content_version: str | None = None
    supporting_signal_ids: list[str] = Field(default_factory=list)
    rationale: str | None = None
    correlation_id: str | None = None
    payload: dict[str, object] = Field(default_factory=dict)
