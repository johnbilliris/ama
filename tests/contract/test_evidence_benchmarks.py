"""Spec-038 / T-E01 — Benchmark register contract test."""

from __future__ import annotations

import pytest
from app.main import create_app
from app.services.evidence._clients import reset_registry
from fastapi.testclient import TestClient


@pytest.fixture()
def client():
    reset_registry()
    from app.services.evidence.benchmarks import router as bm

    bm._SEEDED = False
    app = create_app()
    with TestClient(app) as c:
        yield c


def test_benchmarks_for_response_time(client):
    r = client.get("/api/v1/evidence/benchmarks/response_time_p1")
    assert r.status_code == 200
    rows = r.json()
    assert len(rows) >= 2
    kinds = {row["kind"] for row in rows}
    assert "external_benchmark" in kinds
    assert "prototype_baseline" in kinds


def test_benchmarks_jurisdiction_filter(client):
    r = client.get("/api/v1/evidence/benchmarks/response_time_p1?jurisdiction=NSW")
    assert r.status_code == 200
    rows = r.json()
    assert all(row["jurisdiction"] == "NSW" for row in rows)


def test_benchmarks_not_available_with_prototype_sibling(client):
    r = client.get("/api/v1/evidence/benchmarks/lives_saved_lagging")
    assert r.status_code == 200
    rows = r.json()
    has_unavail = any(row.get("not_available") for row in rows)
    has_proto = any(row["kind"] == "prototype_baseline" for row in rows)
    if has_unavail:
        assert has_proto, "FR-022 — not_available KPIs must surface a prototype_baseline sibling"
