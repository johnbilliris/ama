"""spec-038 entity — ChatAuditEntry (append-only, 7-year TTL).

FR-017 / FR-020 / FR-029. Frozen Pydantic model; the only input form is the
redacted variant (raw user input never persisted). Cosmos container
``chat_audit_log`` is configured with default-TTL = AUDIT_TTL_SECONDS and the
managed identity used by ``help_chat.py`` has insert-only permission.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

# 7 years — Privacy Act APP 11 / spec-001 NFR-012.
AUDIT_TTL_SECONDS = 7 * 365 * 24 * 3600


class ChatAuditEntry(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    tenant_id: str
    chat_session_id: str
    turn_index: int = Field(..., ge=0)
    user_id: str
    persona_id: str
    persona_source: Literal["idp_default", "user_override"]
    jurisdiction_codes: list[str] = Field(default_factory=list)
    snapshot_id: str
    foundry_agent_name: Literal["help_assistant"] = "help_assistant"
    user_input_redacted: str
    redaction_occurred: bool = False
    retrieved_citation_ids: list[str] = Field(default_factory=list)
    response_text: str = ""
    refusal_reason: str | None = None
    pattern_id: str
    gateway_decision: Literal["allow", "deny", "redact"]
    created_at: datetime


__all__ = ["ChatAuditEntry", "AUDIT_TTL_SECONDS"]
