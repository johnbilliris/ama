"""Pydantic v2 model for Spec-037 FeatureValueRow (T030).

Citations: FR-030, FR-031, FR-033, FR-034.
"""

from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from ._common import BackCitation, Provenance

_SPEC_ID_RE = re.compile(r"^\d{3}-[a-z0-9-]+$")


class CapstoneMetricContribution(BaseModel):
    model_config = ConfigDict(extra="forbid")

    metric_id: Literal[
        "lives-saved",
        "response-time",
        "evacuation-lead-time",
        "logistics-efficiency",
        "economic-loss-reduction",
    ]
    magnitude: float
    direction: Literal["+", "-", "+/-"]
    residual_gap_to_target: float


class FeatureValueRow(BaseModel):
    model_config = ConfigDict(extra="forbid")

    spec_id: str
    spec_title: str = Field(min_length=1)
    tag: Literal["capstone-contributing", "delivery-hygiene"]
    capstone_metrics: list[CapstoneMetricContribution] | None = None
    open_followups: list[BackCitation] | None = None
    cross_link_to_metric_trace: BackCitation
    provenance: Provenance

    @field_validator("spec_id")
    @classmethod
    def _spec_id_pattern(cls, v: str) -> str:
        if not _SPEC_ID_RE.match(v):
            raise ValueError(f"spec_id must match NNN-<slug>; got {v!r}")
        return v

    @model_validator(mode="after")
    def _contributing_requires_metrics(self) -> FeatureValueRow:
        if self.tag == "capstone-contributing" and not self.capstone_metrics:
            raise ValueError("capstone-contributing rows require ≥1 capstone_metrics entry (FR-031)")
        return self
