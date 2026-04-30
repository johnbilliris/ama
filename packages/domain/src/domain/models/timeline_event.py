from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class TimelineEvent(BaseModel):
    event_id: str
    incident_id: str
    event_type: Literal[
        "signal",
        "recommendation",
        "approval",
        "alert",
        "task",
        "system",
        "handoff",
        "dead_letter",
        "llm_call",
    ]
    created_at: datetime = Field(default_factory=datetime.utcnow)
    summary: str
    actor: str
    payload: dict[str, object] = Field(default_factory=dict)
