"""Pydantic v2 model for Spec-037 KpiRow (T028).

Citations: FR-019, FR-020.
"""

from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ._common import BackCitation, Provenance

_KPI_ID_RE = re.compile(r"^KPI-CAP-\d{3}$")


class ThresholdBand(BaseModel):
    model_config = ConfigDict(extra="forbid")

    green: str
    amber: str
    red: str


class KpiRow(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kpi_id: str
    capstone_criterion: Literal[
        "lives-saved",
        "response-time",
        "evacuation-lead-time",
        "logistics-efficiency",
        "economic-loss-reduction",
    ]
    kind: Literal["leading", "lagging"]
    name: str = Field(min_length=1)
    owner: str = Field(min_length=1)
    refresh_cadence: Literal["realtime", "hourly", "daily", "weekly", "monthly", "quarterly"]
    target_value: float
    target_unit: str = Field(min_length=1)
    threshold_band: ThresholdBand
    source_of_truth: BackCitation
    consolidates: list[str] = Field(default_factory=list)
    current_value: float | None = None
    last_observed_utc: str | None = None
    back_citations: list[BackCitation] = Field(min_length=1)
    provenance: Provenance

    @field_validator("kpi_id")
    @classmethod
    def _kpi_id_pattern(cls, v: str) -> str:
        if not _KPI_ID_RE.match(v):
            raise ValueError(f"kpi_id must match KPI-CAP-NNN; got {v!r}")
        return v
