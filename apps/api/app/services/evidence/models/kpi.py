# Versioned KPI ladder and indicator models.

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, field_validator

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
LifeSafetyTier = Literal["life_safety", "efficiency"]
PublicationStatus = Literal["draft", "published", "superseded"]
CapstoneScId = Literal[
    "SC-CAP-015-001",
    "SC-CAP-015-002",
    "SC-CAP-015-003",
    "SC-CAP-015-004",
    "SC-CAP-015-005",
]
Decimal4 = Annotated[Decimal, Field(max_digits=18, decimal_places=4)]


class ConfidenceBandRule(BaseModel):
    model_config = ConfigDict(extra="forbid")

    method: Literal["bootstrap_p2_5_p97_5", "stddev_pm1"] = "bootstrap_p2_5_p97_5"
    min_resamples: int = Field(default=1000, ge=1)
    fallback_label: Literal["small-sample"] = "small-sample"


class RiskAdjustment(BaseModel):
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
    formula_version: str = "040.1"
    unit: str
    owner_role: str
    refresh_cadence: str
    target_value: Decimal4
    alert_threshold: Decimal4
    baseline_source: str
    calibration_reference: str = "prototype baseline paired by scenario version, content hash, and seed"
    provenance: Provenance
    confidence_band_rule: ConfidenceBandRule
    risk_adjustment: RiskAdjustment | None = None
    publication_status: PublicationStatus = "published"
    created_at: AwareDatetime
    created_by: str
    superseded_by: str | None = None

    @field_validator(
        "id",
        "kpi_id",
        "name",
        "formula",
        "formula_version",
        "unit",
        "owner_role",
        "refresh_cadence",
        "baseline_source",
        "calibration_reference",
    )
    @classmethod
    def _must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("value must not be blank")
        return value

    def risk_adjusted_value(self, base: Decimal | float) -> Decimal:
        if self.risk_adjustment is None:
            raise ValueError("risk adjustment is not available")
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
    groups: list[KpiLadderGroup] = Field(min_length=1, max_length=5)
