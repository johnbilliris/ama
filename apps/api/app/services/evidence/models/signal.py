"""Pillar C — Signal + canonical event chain (T-C04, FR-024 / FR-029)."""

from __future__ import annotations

from typing import Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, condecimal, model_validator

AuRegion = Literal["australiaeast", "australiasoutheast"]


class ConfidenceScore(BaseModel):
    model_config = ConfigDict(extra="forbid")

    value: condecimal(ge=0, le=1, decimal_places=2)

    @property
    def band(self) -> Literal["high", "medium", "low"]:
        v = float(self.value)
        if v >= 0.80:
            return "high"
        if v >= 0.50:
            return "medium"
        return "low"


class CanonicalEventChain(BaseModel):
    model_config = ConfigDict(extra="forbid")

    call_received_at: AwareDatetime | None = None
    dispatched_at: AwareDatetime | None = None
    arrived_at: AwareDatetime | None = None
    controlled_at: AwareDatetime | None = None
    cleared_at: AwareDatetime | None = None
    imputed_fields: list[str] = Field(default_factory=list)


class Signal(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    scenario_id: str
    seed: str
    mode: Literal["baseline", "ama_assisted"]
    kpi_id: str
    capability_id: str
    capability_version: str
    actor: str
    source: str
    occurred_at: AwareDatetime
    region: AuRegion
    chain: CanonicalEventChain
    confidence: ConfidenceScore
    reduced_fidelity: bool = False
    advisory_only: bool = False
    payload: dict = Field(default_factory=dict)
    correlation_id: str

    @model_validator(mode="after")
    def _low_band_must_be_advisory(self) -> Signal:
        if self.confidence.band == "low":
            if not self.advisory_only or not self.reduced_fidelity:
                self.advisory_only = True
                self.reduced_fidelity = True
        return self
