"""Pillar E — Benchmark register repository + manager (T-E04, FR-020/021)."""

from __future__ import annotations

from .._clients import get_registry
from ..models.benchmark import BenchmarkEntry

CONTAINER = "benchmark_register"


def list_for(kpi_id: str, *, jurisdiction: str | None = None) -> list[BenchmarkEntry]:
    rows = [r for r in get_registry().get(CONTAINER).all() if r.get("kpi_id") == kpi_id]
    if jurisdiction:
        rows = [r for r in rows if r.get("jurisdiction") == jurisdiction]
    return [BenchmarkEntry.model_validate(r) for r in rows]


def publish(entry: BenchmarkEntry) -> BenchmarkEntry:
    get_registry().get(CONTAINER).upsert_item(entry.model_dump(mode="json"))
    return entry
