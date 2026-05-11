"""spec-038 entity — GlossaryTerm. FR-009a / FR-021."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

# Loose BCP-47 — matches `en`, `en-AU`, `yol-Latn-AU`, etc.
_BCP47 = re.compile(r"^[a-zA-Z]{2,3}(-[A-Za-z0-9]{2,8})*$")


class GlossaryTerm(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    tenant_id: str = "__global__"
    term: str = Field(..., min_length=1)
    definition: str = Field(..., min_length=1)
    domain: Literal["aiims", "aidr", "jurisdictional", "hub"]
    aliases: list[str] = Field(default_factory=list)
    related_article_ids: list[str] = Field(default_factory=list)
    lang: str = "en"
    cultural_authority_ref: str | None = None
    created_at: datetime
    updated_at: datetime

    @field_validator("lang")
    @classmethod
    def _bcp47(cls, v: str) -> str:
        if not _BCP47.match(v):
            raise ValueError(f"lang {v!r} is not a valid BCP-47 tag")
        return v


__all__ = ["GlossaryTerm"]
