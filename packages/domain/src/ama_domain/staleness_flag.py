"""spec-038 entity — StalenessFlag. FR-010 / FR-010a / FR-010b."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class StalenessFlag(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    tenant_id: str = "__global__"
    target_kind: Literal["screenshot", "article"]
    target_id: str
    raised_reason: Literal["screen_id_hash_mismatch", "route_renamed", "manual"]
    raised_at: datetime
    grace_release_id: str = Field(..., min_length=1)
    cleared_at: datetime | None = None
    cleared_by: str | None = None
    bulk_baseline_id: str | None = None


__all__ = ["StalenessFlag"]
