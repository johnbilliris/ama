"""Simulation chat turn — records every user / assistant / tool / system utterance.

See specs/024-simulation-control-chat/data-model.md#simchatturn.
"""

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field


class SimChatTurn(BaseModel):
    id: str
    tenant_id: str
    simulation_id: str
    sequence: int
    role: Literal["user", "assistant", "tool", "system"]
    content: str
    tool_call_id: str | None = None
    model: str | None = None
    prompt_hash: str | None = None
    actor_oid: str | None = None
    content_hash: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    document_type: str = "sim_chat_turn"
