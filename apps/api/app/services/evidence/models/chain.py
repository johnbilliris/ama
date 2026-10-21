from __future__ import annotations

from decimal import Decimal
from typing import Annotated, Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator

Decimal4 = Annotated[Decimal, Field(max_digits=18, decimal_places=4)]


class Assumption(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(pattern=r"^[a-z0-9][a-z0-9-]{2,63}$")
    text: str = Field(min_length=1)
    resolved: bool = False
    review_state: Literal["pending", "validated", "rejected"] = "pending"
    validation_method: str = Field(min_length=1)
    evidence_required: str = Field(min_length=1)
    owner_role: str = Field(min_length=1)
    review_due_at: AwareDatetime | None = None

    @model_validator(mode="after")
    def align_resolution_state(self) -> Assumption:
        if self.resolved != (self.review_state == "validated"):
            raise ValueError("resolved must be true only when review_state is validated")
        return self


class ThreatToValidity(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str = Field(min_length=1)
    severity: Literal["low", "medium", "high"]
    mitigation: str = Field(min_length=1)


class CausalChain(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    capability_id: str
    capability_name: str
    version: int = Field(ge=1)
    claim: str = Field(min_length=1)
    kpis_moved: list[str] = Field(min_length=1)
    magnitude_status: Literal["source_grounded", "hypothesis"]
    expected_magnitude_value: Decimal4 | None = None
    expected_magnitude_unit: str | None = None
    assumptions: list[Assumption] = Field(min_length=1)
    threats_to_validity: list[ThreatToValidity] = Field(min_length=1)
    originating_spec_path: str = Field(pattern=r"^specs/[0-9]{3}[^/]*/spec\.md$")
    originating_requirement: str = Field(pattern=r"^(FR|SC)(-[A-Z]+)*-[0-9]+[a-z]?$")
    created_at: AwareDatetime
    superseded_by: str | None = None

    @model_validator(mode="after")
    def validate_magnitude(self) -> CausalChain:
        if self.magnitude_status == "source_grounded":
            if self.expected_magnitude_value is None or not self.expected_magnitude_unit:
                raise ValueError("source-grounded magnitudes require value and unit")
        elif self.expected_magnitude_value is not None:
            raise ValueError("hypothesis magnitudes must not publish unsupported numeric values")
        return self
