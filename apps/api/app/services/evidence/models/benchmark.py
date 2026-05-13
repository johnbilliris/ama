"""Pillar E — Benchmark Register entry (T-E03, FR-020..FR-022)."""

from __future__ import annotations

from typing import Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, condecimal


class CitationRef(BaseModel):
    model_config = ConfigDict(extra="forbid")

    org: str
    document: str
    year: int
    url: str


class BenchmarkEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    kpi_id: str
    jurisdiction: str
    kind: Literal["external_benchmark", "prototype_baseline"]
    source_name: str
    source_citation: CitationRef | None = None
    provenance: Literal["auto", "manual"] = "auto"
    target_value: condecimal(max_digits=18, decimal_places=4) | None = None
    target_unit: str
    not_available: bool = False
    created_at: AwareDatetime
