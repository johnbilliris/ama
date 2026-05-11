"""Pillar E — Benchmarks router (T-E05, contracts: getBenchmarksForKpi)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Path, Query

from .._correlation import correlation_id_dep
from ..models.benchmark import BenchmarkEntry
from .repository import list_for, publish
from .seed import seed_register

router = APIRouter(tags=["evidence-benchmarks"])

_SEEDED = False


def _ensure_seed() -> None:
    global _SEEDED
    if _SEEDED:
        return
    for entry in seed_register():
        publish(entry)
    _SEEDED = True


@router.get(
    "/benchmarks/{kpi_id}",
    response_model=list[BenchmarkEntry],
    operation_id="getBenchmarksForKpi",
)
def get_benchmarks(
    kpi_id: str = Path(...),
    jurisdiction: str | None = Query(default=None),
    correlation_id: str = Depends(correlation_id_dep),
) -> list[BenchmarkEntry]:
    _ensure_seed()
    return list_for(kpi_id, jurisdiction=jurisdiction)
