from __future__ import annotations

from decimal import Decimal
from typing import Annotated, Literal

from pydantic import (
    AliasChoices,
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    HttpUrl,
    model_validator,
)

Decimal4 = Annotated[Decimal, Field(max_digits=18, decimal_places=4)]


class CitationRef(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    organisation: str = Field(
        min_length=1,
        validation_alias=AliasChoices("organisation", "org"),
    )
    document: str = Field(min_length=1)
    year: int = Field(ge=1900, le=2100)
    url: HttpUrl


class BenchmarkEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1, max_length=128)
    kpi_id: str = Field(min_length=1, max_length=128)
    jurisdiction: str = Field(min_length=1, max_length=128)
    category: Literal["fire", "ambulance", "ses", "police", "cross_sector"]
    kind: Literal["external_benchmark", "prototype_baseline"]
    source_name: str = Field(min_length=1)
    source_citation: CitationRef | None = None
    provenance: Literal["auto", "manual"] = "auto"
    benchmark_type: Literal[
        "performance_target",
        "operational_aim",
        "trigger_window",
        "metric_definition",
        "prototype_measurement",
        "unavailable",
    ]
    target_value: Decimal4 | None = None
    target_unit: str = Field(min_length=1)
    target_context: str = Field(min_length=1)
    not_available: bool = False
    created_at: AwareDatetime

    @model_validator(mode="after")
    def validate_source_and_target(self) -> BenchmarkEntry:
        if self.kind == "external_benchmark" and self.source_citation is None:
            raise ValueError("external benchmarks require a structured citation")
        if self.not_available:
            if self.target_value is not None or self.benchmark_type != "unavailable":
                raise ValueError("unavailable rows must omit target_value")
        elif self.target_value is None:
            raise ValueError("available rows require target_value")
        if self.provenance == "auto" and self.source_citation is None:
            raise ValueError("automatic provenance requires a citation")
        return self
