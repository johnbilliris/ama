"""Spec-038 / T-E02 — Benchmark register coverage (SC-007)."""

from __future__ import annotations

import pytest
from app.main import create_app
from app.services.evidence._clients import reset_registry
from app.services.evidence.kpi_ladder.repository import list_published
from fastapi.testclient import TestClient


@pytest.fixture()
def client():
    reset_registry()
    from app.services.evidence.benchmarks import router as bm
    from app.services.evidence.kpi_ladder import router as kpi_router

    bm._SEEDED = False
    kpi_router._SEEDED = False
    app = create_app()
    with TestClient(app) as c:
        # Force-seed both pillars.
        c.get("/api/v1/evidence/kpi-ladder")
        yield c


def test_every_kpi_in_ladder_has_benchmark(client):
    indicators = list_published()
    assert indicators, "expected the ladder to be seeded"
    for ind in indicators:
        r = client.get(f"/api/v1/evidence/benchmarks/{ind.kpi_id}")
        assert r.status_code == 200, f"benchmark fetch failed for {ind.kpi_id}"
        rows = r.json()
        assert len(rows) >= 1, f"no benchmark entries for {ind.kpi_id}"
        # Sibling rule: any not_available external entry must coexist with prototype baseline.
        unavail = [row for row in rows if row.get("not_available")]
        proto = [row for row in rows if row["kind"] == "prototype_baseline"]
        if unavail:
            assert proto, f"FR-022 violated for {ind.kpi_id}: not_available without prototype_baseline"
