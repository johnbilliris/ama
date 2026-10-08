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
    assert {row["jurisdiction"] for row in rows} == {"NSW", "AU"}
    assert any(row["not_available"] for row in rows if row["jurisdiction"] == "NSW")
    assert any(row["kind"] == "prototype_baseline" for row in rows)


def test_benchmarks_not_available_with_prototype_sibling(client):
    r = client.get("/api/v1/evidence/benchmarks/lives_saved_lagging")
    assert r.status_code == 200
    rows = r.json()
    has_unavail = any(row.get("not_available") for row in rows)
    has_proto = any(row["kind"] == "prototype_baseline" for row in rows)
    if has_unavail:
        assert has_proto, "FR-022 — not_available KPIs must surface a prototype_baseline sibling"


def test_unknown_jurisdiction_retains_prototype_baseline(client):
    response = client.get("/api/v1/evidence/benchmarks/response_time_p1?jurisdiction=UNKNOWN")

    assert response.status_code == 200
    rows = response.json()
    assert len(rows) == 1
    assert rows[0]["kind"] == "prototype_baseline"


def test_saidi_and_saifi_are_separate_dimensioned_rows(client):
    saidi = client.get("/api/v1/evidence/benchmarks/saidi").json()
    saifi = client.get("/api/v1/evidence/benchmarks/saifi").json()

    assert saidi[0]["target_unit"] == "minutes/customer/year"
    assert saifi[0]["target_unit"] == "interruptions/customer/year"
    assert saidi[0]["not_available"] is True
    assert saifi[0]["not_available"] is True


def test_airservices_arff_has_verified_three_minute_target(client):
    response = client.get("/api/v1/evidence/benchmarks/airservices_arff_response")

    row = response.json()[0]
    assert float(row["target_value"]) == 180.0
    assert row["target_unit"] == "seconds"
    assert row["source_citation"]["organisation"] == "Airservices Australia"
    assert "org" not in row["source_citation"]
