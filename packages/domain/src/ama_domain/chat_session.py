"""spec-038 entity — ChatSession + ChatTurn. FR-029 (Cosmos default TTL 30 d).

The ``DEFAULT_TTL_SECONDS`` constant is also imported by
``infra/bicep/modules/cosmos-help-containers.bicep`` (via parameter file).
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

RefusalReason = Literal[
    "out_of_scope",
    "cross_tenant",
    "no_corpus_match",
    "pii_blocked",
    "above_official_classification",
    "deprecated_no_replacement",
]

# 30 days — FR-029 transcript retention ceiling.
DEFAULT_TTL_SECONDS = 30 * 24 * 3600


class ChatTurn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    turn_index: int = Field(..., ge=0)
    user_input_redacted: str
    redaction_occurred: bool = False
    answer_text: str
    citations: list[str] = Field(default_factory=list)
    refusal_reason: RefusalReason | None = None
    pattern_id: str
    feedback_id: str | None = None
    audit_entry_id: str
    created_at: datetime


class ChatSession(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    tenant_id: str
    user_id: str
    persona_id: str
    persona_source: Literal["idp_default", "user_override"]
    jurisdiction_codes: list[str] = Field(default_factory=list)
    snapshot_id_at_open: str
    turns: list[ChatTurn] = Field(default_factory=list)
    started_at: datetime
    last_turn_at: datetime
    # Note: Cosmos container has default-TTL = DEFAULT_TTL_SECONDS (FR-029).
    ttl_seconds: int = DEFAULT_TTL_SECONDS


__all__ = ["ChatSession", "ChatTurn", "RefusalReason", "DEFAULT_TTL_SECONDS"]
