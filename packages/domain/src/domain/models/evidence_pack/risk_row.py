"""Pydantic v2 model for Spec-037 RiskRow (T026).

Citations: FR-010, FR-011, FR-012, FR-014.
Mirrors `packages/schemas/spec_037/risk-register.schema.json`.
"""

from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from ._common import BackCitation, Provenance

_RISK_ID_RE = re.compile(r"^RISK-[A-Z0-9]+-\d{3}$")


class RiskRow(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    title: str = Field(min_length=1)
    category: Literal["Platform", "AI", "Operational", "Jurisdictional", "Data", "Supply-chain"]
    description: str = Field(min_length=1)
    likelihood: int = Field(ge=1, le=5)
    consequence: int = Field(ge=1, le=5)
    inherent_score: int = Field(ge=1, le=25)
    treatment: str = Field(min_length=1)
    owner: str = Field(min_length=1)
    residual_likelihood: int = Field(ge=1, le=5)
    residual_consequence: int = Field(ge=1, le=5)
    residual_score: int = Field(ge=1, le=25)
    next_review_date: str  # ISO 8601 date
    back_citations: list[BackCitation] = Field(min_length=1)
    provenance: Provenance

    @field_validator("id")
    @classmethod
    def _id_pattern(cls, v: str) -> str:
        if not _RISK_ID_RE.match(v):
            raise ValueError(f"id must match RISK-<DOMAIN>-NNN; got {v!r}")
        return v

    @model_validator(mode="after")
    def _scores_consistent(self) -> "RiskRow":
        if self.inherent_score != self.likelihood * self.consequence:
            raise ValueError("inherent_score must equal likelihood × consequence")
        if self.residual_score != self.residual_likelihood * self.residual_consequence:
            raise ValueError("residual_score must equal residual_likelihood × residual_consequence")
        return self
