"""spec-038 entity — KnowledgeCorpusSource. FR-011 / FR-011-AMEND."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class KnowledgeCorpusSource(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    snapshot_id: str
    source_kind: Literal["help_article", "docs_corpus", "docs_aidr", "spec"]
    source_path: str
    spec_id: str | None = None
    spec_version: str | None = None
    spec_status: Literal["Active", "Implemented"] | None = None
    content_hash: str = Field(..., pattern=r"^[a-f0-9]{64}$")
    classification: Literal["OFFICIAL", "OFFICIAL: SENSITIVE"] = "OFFICIAL"
    scope: Literal["tenant", "global"] = "global"
    indexed_at: datetime

    @model_validator(mode="after")
    def _spec_status_required(self) -> "KnowledgeCorpusSource":
        # FR-011 admission gate — only Active|Implemented specs admitted.
        if self.source_kind == "spec":
            if self.spec_status not in {"Active", "Implemented"}:
                raise ValueError(
                    "FR-011: spec sources require spec_status ∈ {Active, Implemented}"
                )
        return self


__all__ = ["KnowledgeCorpusSource"]
