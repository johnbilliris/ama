"""Pillar D — Causal Chain (T-D03, FR-017..FR-019)."""

from __future__ import annotations

from typing import Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, condecimal, field_validator


class Assumption(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str
    resolved: bool = False  # FR-019


class ThreatToValidity(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str
    severity: Literal["low", "medium", "high"]


class CausalChain(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    capability_id: str
    capability_name: str
    version: int = Field(ge=1)
    kpis_moved: list[str] = Field(min_length=1)
    expected_magnitude_value: condecimal(max_digits=18, decimal_places=4)
    expected_magnitude_unit: str
    assumptions: list[Assumption] = Field(min_length=1)
    threats_to_validity: list[ThreatToValidity] = Field(min_length=1)
    originating_spec_path: str
    created_at: AwareDatetime
    superseded_by: str | None = None

    @field_validator("originating_spec_path")
    @classmethod
    def _spec_path(cls, v: str) -> str:
        if not v.startswith("specs/"):
            raise ValueError("originating_spec_path must start with 'specs/'")
        return v
