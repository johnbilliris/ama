"""Pydantic v2 model for Spec-037 PublicationGateMetadata (T031).

Citations: FR-037, FR-038, RES-05.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class AuditorSignoff(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    role: str = Field(min_length=1)
    signoff_date_utc: str
    basis: str = Field(min_length=8)


class PublicationGateMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    manual_row_count: int = Field(ge=0)
    total_row_count: int = Field(ge=1)
    manual_row_ratio: float = Field(ge=0.0, le=1.0)
    manual_row_ratio_threshold: float = Field(default=0.5, ge=0.0, le=1.0)
    auditor_signoff: AuditorSignoff | None = None
    link_check_status: Literal["passed", "failed", "pending"]
    last_gate_run_utc: str

    @model_validator(mode="after")
    def _ratio_consistent(self) -> "PublicationGateMetadata":
        if self.total_row_count > 0:
            expected = self.manual_row_count / self.total_row_count
            if abs(expected - self.manual_row_ratio) > 1e-9:
                raise ValueError(
                    f"manual_row_ratio={self.manual_row_ratio} does not match "
                    f"manual_row_count/total_row_count={expected}"
                )
        return self

    @model_validator(mode="after")
    def _signoff_required_when_over_cap(self) -> "PublicationGateMetadata":
        if self.manual_row_ratio > self.manual_row_ratio_threshold and self.auditor_signoff is None:
            raise ValueError(
                f"auditor_signoff required when manual_row_ratio "
                f"({self.manual_row_ratio}) exceeds threshold "
                f"({self.manual_row_ratio_threshold}); see FR-038"
            )
        return self
