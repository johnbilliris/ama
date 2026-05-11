"""Pillar A — KPI Ladder + Indicator Definition models (T-A04, FR-002..FR-006)."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, condecimal

AiimsFunction = Literal[
    "Control",
    "Intelligence",
    "Planning",
    "Operations",
    "Logistics",
    "PublicInformation",
]
IncidentLevel = Literal[1, 2, 3]
Provenance = Literal["auto", "manual"]
IndicatorKind = Literal["leading", "lagging"]
LifeSafetyTier = Literal["life_safety", "efficiency"]  # FR-006 ranking
CapstoneScId = Literal[
    "SC-CAP-015-001",
    "SC-CAP-015-002",
    "SC-CAP-015-003",
    "SC-CAP-015-004",
    "SC-CAP-015-005",
]


class ConfidenceBandRule(BaseModel):
    model_config = ConfigDict(extra="forbid")

    method: Literal["bootstrap_p2_5_p97_5", "stddev_pm1"] = "bootstrap_p2_5_p97_5"
    min_resamples: int = Field(default=1000, ge=1)
    fallback_label: Literal["small-sample"] = "small-sample"


class RiskAdjustment(BaseModel):
    """FR-004 — 5×5 likelihood × consequence (AS/NZS ISO 31000)."""

    model_config = ConfigDict(extra="forbid")

    likelihood: Annotated[int, Field(ge=1, le=5)]
    consequence: Annotated[int, Field(ge=1, le=5)]
    provenance: Literal["auto", "manual"] = "auto"
    auditor_signoff_required: bool = False

    @property
    def weight(self) -> float:
        return (self.likelihood * self.consequence) / 25.0


class IndicatorDefinition(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    kpi_id: str
    version: int = Field(ge=1)
    capstone_sc_id: CapstoneScId
    name: str
    kind: IndicatorKind
    aiims_function: AiimsFunction
    incident_level: IncidentLevel
    life_safety_tier: LifeSafetyTier
    formula: str
    unit: str
    owner_role: str
    refresh_cadence: str
    target_value: condecimal(max_digits=18, decimal_places=4)
    alert_threshold: condecimal(max_digits=18, decimal_places=4)
    baseline_source: str
    provenance: Provenance
    confidence_band_rule: ConfidenceBandRule
    risk_adjustment: RiskAdjustment
    created_at: AwareDatetime
    created_by: str
    superseded_by: str | None = None

    def risk_adjusted_value(self, base: Decimal | float) -> Decimal:
        return Decimal(str(base)) * Decimal(str(self.risk_adjustment.weight))


class KpiLadderGroup(BaseModel):
    model_config = ConfigDict(extra="forbid")

    capstone_sc_id: CapstoneScId
    leading: list[IndicatorDefinition] = Field(min_length=1)
    lagging: list[IndicatorDefinition] = Field(min_length=1)


class KpiLadderView(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: str
    generated_at: datetime
    groups: list[KpiLadderGroup] = Field(min_length=5, max_length=5)
