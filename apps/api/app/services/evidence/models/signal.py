from __future__ import annotations

import math
from datetime import datetime
from decimal import Decimal
from typing import Annotated, Any, Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator

AuRegion = Literal["australiaeast", "australiasoutheast"]
KpiId = Literal[
    "lives_saved_lagging",
    "response_time_p1",
    "evac_lead_lagging",
    "logistics_efficiency",
    "econ_loss_lagging",
]
ConfidenceDecimal = Annotated[
    Decimal,
    Field(ge=0, le=1, max_digits=3, decimal_places=2),
]

_KPI_PAYLOAD_FIELDS = {
    "lives_saved_lagging": ("fatalities",),
    "response_time_p1": (),
    "evac_lead_lagging": ("warning_issued_at", "evacuation_completed_at"),
    "logistics_efficiency": ("assets_requested", "assets_deployed"),
    "econ_loss_lagging": ("exposure_value", "loss_value"),
}


class ConfidenceScore(BaseModel):
    model_config = ConfigDict(extra="forbid")

    value: ConfidenceDecimal

    @property
    def band(self) -> Literal["high", "medium", "low"]:
        value = Decimal(self.value)
        if value >= Decimal("0.80"):
            return "high"
        if value >= Decimal("0.50"):
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

    @model_validator(mode="after")
    def timestamps_are_ordered(self) -> CanonicalEventChain:
        values = [
            self.call_received_at,
            self.dispatched_at,
            self.arrived_at,
            self.controlled_at,
            self.cleared_at,
        ]
        populated = [value for value in values if value is not None]
        if any(current > following for current, following in zip(populated, populated[1:])):
            raise ValueError("canonical event timestamps must be ordered")
        return self


class SignalIngressRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1, max_length=128)
    scenario_id: str = Field(min_length=1, max_length=128)
    seed: str = Field(min_length=1, max_length=128)
    mode: Literal["baseline", "ama_assisted"]
    kpi_id: KpiId
    capability_id: str = Field(min_length=1, max_length=128)
    capability_version: str = Field(min_length=1, max_length=128)
    actor: str | None = Field(default=None, max_length=256)
    source: str = Field(min_length=1, max_length=256)
    occurred_at: AwareDatetime
    region: str | None = Field(default=None, max_length=64)
    chain: CanonicalEventChain
    confidence: ConfidenceScore
    reduced_fidelity: bool = False
    advisory_only: bool = False
    payload: dict[str, Any] = Field(default_factory=dict)
    correlation_id: str = Field(default="", max_length=128)


class Signal(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1, max_length=128)
    scenario_id: str = Field(min_length=1, max_length=128)
    seed: str = Field(min_length=1, max_length=128)
    mode: Literal["baseline", "ama_assisted"]
    kpi_id: KpiId
    capability_id: str = Field(min_length=1, max_length=128)
    capability_version: str = Field(min_length=1, max_length=128)
    actor: str = Field(min_length=1, max_length=256)
    source: str = Field(min_length=1, max_length=256)
    occurred_at: AwareDatetime
    region: AuRegion
    chain: CanonicalEventChain
    confidence: ConfidenceScore
    reduced_fidelity: bool = False
    advisory_only: bool = False
    payload: dict[str, Any] = Field(default_factory=dict)
    correlation_id: str = Field(default="", max_length=128)

    @model_validator(mode="after")
    def validate_fidelity_and_payload(self) -> Signal:
        if self.confidence.band == "low" and (not self.advisory_only or not self.reduced_fidelity):
            raise ValueError("low-confidence signals require advisory_only and reduced_fidelity")
        required = _KPI_PAYLOAD_FIELDS[self.kpi_id]
        missing = [field for field in required if field not in self.payload]
        if missing:
            raise ValueError(f"{self.kpi_id} payload missing required fields: {', '.join(missing)}")
        _validate_payload_values(self.kpi_id, self.payload)
        return self


def _validate_payload_values(kpi_id: KpiId, payload: dict[str, Any]) -> None:
    if kpi_id == "evac_lead_lagging":
        warning = _aware_datetime(payload["warning_issued_at"], "warning_issued_at")
        completed = _aware_datetime(
            payload["evacuation_completed_at"],
            "evacuation_completed_at",
        )
        if warning > completed:
            raise ValueError("warning_issued_at must not follow evacuation_completed_at")
        return

    for field in _KPI_PAYLOAD_FIELDS[kpi_id]:
        value = payload[field]
        if isinstance(value, bool) or not isinstance(value, (int, float, Decimal)):
            raise ValueError(f"{field} must be numeric")
        if not math.isfinite(float(value)) or float(value) < 0:
            raise ValueError(f"{field} must be finite and non-negative")
    if kpi_id == "logistics_efficiency" and float(payload["assets_requested"]) <= 0:
        raise ValueError("assets_requested must be greater than zero")
    if kpi_id == "econ_loss_lagging" and float(payload["exposure_value"]) <= 0:
        raise ValueError("exposure_value must be greater than zero")


def _aware_datetime(value: Any, field: str) -> datetime:
    parsed = value if isinstance(value, datetime) else datetime.fromisoformat(str(value))
    if parsed.tzinfo is None:
        raise ValueError(f"{field} must be timezone-aware")
    return parsed
