from unittest.mock import AsyncMock

from app.api.routes import incidents_map
from fastapi import FastAPI
from fastapi.testclient import TestClient


def test_reversed_year_range_returns_empty_feature_collection(monkeypatch) -> None:
    query_incidents = AsyncMock()
    count_unmapped = AsyncMock()
    monkeypatch.setattr(incidents_map._repo, "query_incidents", query_incidents)
    monkeypatch.setattr(incidents_map._repo, "count_unmapped", count_unmapped)

    app = FastAPI()
    app.include_router(incidents_map.router, prefix="/api")

    response = TestClient(app).get(
        "/api/incidents/map",
        params={"year_start": 2024, "year_end": 2023, "page": 2, "page_size": 50},
    )

    body = response.json()
    assert response.status_code == 200
    assert body["type"] == "FeatureCollection"
    assert body["features"] == []
    assert body["metadata"]["total"] == 0
    assert body["metadata"]["unmapped_count"] == 0
    assert body["metadata"]["page"] == 2
    assert body["metadata"]["page_size"] == 50
    assert body["metadata"]["fetched_at"]
    query_incidents.assert_not_awaited()
    count_unmapped.assert_not_awaited()
