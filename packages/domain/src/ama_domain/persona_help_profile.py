"""spec-038 entity — PersonaHelpProfile. FR-027 / FR-028 / FR-027-AMEND."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .authority_rank_registry import AUTHORITY_RANK


class PersonaHelpProfile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    tenant_id: str = "__global__"
    persona_kind: Literal["operational", "sector"]
    authority_rank: int = Field(..., ge=1)
    landing_tile_ids: list[str] = Field(default_factory=list)
    recommended_workflow_article_ids: list[str] = Field(default_factory=list)
    decision_rights_summary: str = ""
    handoff_destinations: list[str] = Field(default_factory=list)
    chat_starter_prompts: list[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    @model_validator(mode="after")
    def _authority_matches_registry(self) -> "PersonaHelpProfile":
        expected = AUTHORITY_RANK.get(self.id)
        if expected is not None and expected != self.authority_rank:
            raise ValueError(
                f"authority_rank for {self.id} must equal {expected} (registry); got {self.authority_rank}"
            )
        return self


__all__ = ["PersonaHelpProfile"]
