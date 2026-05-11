"""spec-038 entity — HelpFeedback. FR-022 / FR-022a-AMEND."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class HelpFeedback(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    tenant_id: str
    target_kind: Literal["article", "chat_turn"]
    target_id: str
    rating: Literal["helpful", "not_helpful"]
    comment: str | None = Field(default=None, max_length=2000)
    submitted_by: str
    pattern_id: str | None = None
    created_at: datetime

    @model_validator(mode="after")
    def _pattern_id_required_for_chat(self) -> "HelpFeedback":
        if self.target_kind == "chat_turn" and not self.pattern_id:
            raise ValueError("FR-022a-AMEND: pattern_id required for chat_turn feedback")
        return self


__all__ = ["HelpFeedback"]
