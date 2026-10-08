"""Contract tests for GET /api/v1/incidents/map.

Validates GeoJSON FeatureCollection schema, query parameter combinations,
error responses, pagination metadata, unmapped count, and severity-to-AWS-tier
mapping.
"""

import pytest
from app.api.routes.incidents_map import _repo
from app.main import create_app
from fastapi.testclient import TestClient

# ── Fixtures ──


_UNSET = object()


def _make_incident(
    incident_id: str,
    title: str = "Test Incident",
    incident_type: str = "bushfire",
    status: str = "active",
    severity: str = "warning",
    pprr_phase: str | None = "response",
    started_at: str = "2024-01-15T08:30:00Z",
    location: dict | None | object = _UNSET,
) -> dict:
    return {
        "incident_id": incident_id,
        "kind": "disaster",
        "title": title,
        "incident_type": incident_type,
        "status": status,
        "severity": severity,
        "affected_jurisdiction_ids": ["nsw"],
        "participating_organisation_ids": ["rfs-nsw"],
        "owning_framework_ids": [],
        "started_at": started_at,
        "pprr_phase": pprr_phase,
        "incident_level": 2,
        "location": {"type": "Point", "coordinates": [151.2, -33.8]} if location is _UNSET else location,
    }


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("AMA_ALLOW_ANONYMOUS_INCIDENT_MAP", "1")
    app = create_app()
    _repo.seed(
        [
            _make_incident("inc-001", "Sydney Bushfire", "bushfire", "active", "warning"),
            _make_incident(
                "inc-002",
                "Brisbane Flood",
                "flood",
                "monitoring",
                "advisory",
                started_at="2023-06-20T14:00:00Z",
                location={"type": "Point", "coordinates": [153.0, -27.5]},
            ),
            _make_incident("inc-003", "Storm Watch", "storm", "stabilising", "watch"),
            _make_incident("inc-004", "Emergency", "cyclone", "active", "emergency"),
            _make_incident("inc-rehearsal", "Rehearsal", status="rehearsal"),
            _make_incident("inc-nomap", "No Location", location=None),
        ]
    )
    with TestClient(app) as c:
        yield c


# ── Schema validation tests ──


class TestGeoJSONSchema:
    def test_response_is_feature_collection(self, client: TestClient):
        resp = client.get("/api/incidents/map")
        assert resp.status_code == 200
        data = resp.json()
        assert data["type"] == "FeatureCollection"
        assert "features" in data
        assert "metadata" in data

    def test_feature_has_required_fields(self, client: TestClient):
        resp = client.get("/api/incidents/map")
        data = resp.json()
        assert len(data["features"]) > 0
        feature = data["features"][0]
        assert feature["type"] == "Feature"
        assert "id" in feature
        assert feature["geometry"]["type"] == "Point"
        assert len(feature["geometry"]["coordinates"]) == 2
        props = feature["properties"]
        assert "incident_id" in props
        assert "title" in props
        assert "incident_type" in props
        assert "status" in props
        assert "severity" in props
        assert "severity_tier" in props
        assert "affected_jurisdiction_ids" in props
        assert "participating_organisation_ids" in props
        assert "started_at" in props
        assert "incident_level" in props

    def test_metadata_fields(self, client: TestClient):
        resp = client.get("/api/incidents/map")
        meta = resp.json()["metadata"]
        assert "total" in meta
        assert "unmapped_count" in meta
        assert "page" in meta
        assert "page_size" in meta
        assert "fetched_at" in meta


# ── Severity-to-AWS-tier mapping tests ──


class TestSeverityMapping:
    def test_advisory_maps_to_advice(self, client: TestClient):
        resp = client.get("/api/incidents/map?severity=advisory")
        data = resp.json()
        for f in data["features"]:
            assert f["properties"]["severity_tier"] == "advice"

    def test_watch_maps_to_watch(self, client: TestClient):
        resp = client.get("/api/incidents/map?severity=watch")
        data = resp.json()
        for f in data["features"]:
            assert f["properties"]["severity_tier"] == "watch"

    def test_warning_maps_to_emergency(self, client: TestClient):
        resp = client.get("/api/incidents/map?severity=warning")
        data = resp.json()
        for f in data["features"]:
            assert f["properties"]["severity_tier"] == "emergency"

    def test_emergency_maps_to_emergency(self, client: TestClient):
        resp = client.get("/api/incidents/map?severity=emergency")
        data = resp.json()
        for f in data["features"]:
            assert f["properties"]["severity_tier"] == "emergency"


# ── Filter tests ──


class TestQueryParameters:
    def test_filter_by_type(self, client: TestClient):
        resp = client.get("/api/incidents/map?type=bushfire")
        data = resp.json()
        assert data["metadata"]["total"] == 1
        assert data["features"][0]["properties"]["incident_type"] == "bushfire"

    def test_filter_by_multiple_types(self, client: TestClient):
        resp = client.get("/api/incidents/map?type=bushfire,flood")
        data = resp.json()
        assert data["metadata"]["total"] == 2

    def test_filter_by_severity(self, client: TestClient):
        resp = client.get("/api/incidents/map?severity=advisory")
        data = resp.json()
        assert data["metadata"]["total"] == 1

    def test_filter_by_status(self, client: TestClient):
        resp = client.get("/api/incidents/map?status=active")
        data = resp.json()
        assert all(f["properties"]["status"] == "active" for f in data["features"])

    def test_filter_by_pprr_phase(self, client: TestClient):
        resp = client.get("/api/incidents/map?pprr_phase=response")
        data = resp.json()
        assert all(f["properties"]["pprr_phase"] == "response" for f in data["features"])

    def test_keyword_filter(self, client: TestClient):
        resp = client.get("/api/incidents/map?keyword=sydney")
        data = resp.json()
        assert data["metadata"]["total"] == 1
        assert "Sydney" in data["features"][0]["properties"]["title"]

    def test_combined_filters(self, client: TestClient):
        resp = client.get("/api/incidents/map?type=bushfire&status=active")
        data = resp.json()
        assert data["metadata"]["total"] == 1


# ── Pagination tests ──


class TestPagination:
    def test_default_pagination(self, client: TestClient):
        resp = client.get("/api/incidents/map")
        meta = resp.json()["metadata"]
        assert meta["page"] == 1
        assert meta["page_size"] == 200

    def test_custom_page_size(self, client: TestClient):
        resp = client.get("/api/incidents/map?page_size=2")
        data = resp.json()
        assert len(data["features"]) == 2
        assert data["metadata"]["page_size"] == 2


# ── Exclusion tests ──


class TestExclusions:
    def test_rehearsal_excluded(self, client: TestClient):
        resp = client.get("/api/incidents/map")
        data = resp.json()
        ids = [f["properties"]["incident_id"] for f in data["features"]]
        assert "inc-rehearsal" not in ids

    def test_unmapped_count(self, client: TestClient):
        resp = client.get("/api/incidents/map")
        meta = resp.json()["metadata"]
        assert meta["unmapped_count"] >= 1  # inc-nomap is unmapped


# ── Error response tests ──


class TestErrorResponses:
    def test_invalid_type_returns_400(self, client: TestClient):
        resp = client.get("/api/incidents/map?type=invalid_type")
        assert resp.status_code == 400

    def test_invalid_severity_returns_400(self, client: TestClient):
        resp = client.get("/api/incidents/map?severity=invalid")
        assert resp.status_code == 400

    def test_invalid_status_returns_400(self, client: TestClient):
        resp = client.get("/api/incidents/map?status=invalid")
        assert resp.status_code == 400

    def test_invalid_pprr_returns_400(self, client: TestClient):
        resp = client.get("/api/incidents/map?pprr_phase=invalid")
        assert resp.status_code == 400

    def test_year_start_gt_year_end_returns_400(self, client: TestClient):
        resp = client.get("/api/incidents/map?year_start=2025&year_end=2020")
        assert resp.status_code == 400

    def test_page_zero_returns_422(self, client: TestClient):
        resp = client.get("/api/incidents/map?page=0")
        assert resp.status_code == 422

    def test_page_size_too_large_returns_422(self, client: TestClient):
        resp = client.get("/api/incidents/map?page_size=501")
        assert resp.status_code == 422
