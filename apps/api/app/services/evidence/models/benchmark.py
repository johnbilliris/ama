"""Pillar E — Benchmark Register entry (T-E03, FR-020..FR-022)."""

from __future__ import annotations

from typing import Literal

from pydantic import AwareDatetime, BaseModel, condecimal


class BenchmarkEntry(BaseModel):
    id: str
    kpi_id: str
    jurisdiction: str
    kind: Literal["external_benchmark", "prototype_baseline"]
    source_name: str
    source_citation: str
    target_value: condecimal(max_digits=18, decimal_places=4) | None = None
    target_unit: str
    not_available: bool = False
    created_at: AwareDatetime
