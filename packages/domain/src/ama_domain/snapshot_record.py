"""spec-038 entity — SnapshotRecord + Approver. FR-011a / FR-011b / FR-011c.

Frozen (immutable). Dual-approval validation enforced at construction:
- at least one approver with role ``help_content_owner``
- at least one approver with role ∈ {``safety_lead``, ``governance_lead``}
- the two MUST be distinct identities.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .knowledge_corpus_source import KnowledgeCorpusSource


class Approver(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    identity: str = Field(..., min_length=1)
    role: Literal["help_content_owner", "safety_lead", "governance_lead"]
    approved_at: datetime


class SnapshotRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str = Field(..., min_length=1)
    tenant_id: str = "__global__"
    sources: list[KnowledgeCorpusSource] = Field(default_factory=list)
    ai_search_index_name: str
    approvers: list[Approver] = Field(..., min_length=2)
    published_at: datetime
    published_by: str
    rollback_of: str | None = None

    @model_validator(mode="after")
    def _dual_approval(self) -> "SnapshotRecord":
        roles = {a.role for a in self.approvers}
        identities = {a.identity for a in self.approvers}
        if len(identities) < 2:
            raise ValueError("FR-011b: at least two distinct approver identities required")
        if "help_content_owner" not in roles:
            raise ValueError("FR-011b: at least one approver with role help_content_owner required")
        if not (roles & {"safety_lead", "governance_lead"}):
            raise ValueError(
                "FR-011b: at least one approver with role safety_lead or governance_lead required"
            )
        return self


__all__ = ["SnapshotRecord", "Approver"]
