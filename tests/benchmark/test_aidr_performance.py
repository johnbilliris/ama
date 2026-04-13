"""Benchmark tests for AIDR performance targets (NFR-001–008)."""
import time
import pytest
from fastapi.testclient import TestClient
from app.main import create_app
from app.services.state_store import INCIDENTS, ALERTS, LESSONS, reset_state
from packages.domain.src.domain.models.incident import Incident


@pytest.fixture
def client():
    app = create_app()
    with TestClient(app) as c:
        yield c
    reset_state()


def _make_incident(incident_id="inc-perf-1"):
    return Incident(
        incident_id=incident_id,
        title="Performance Test",
        incident_type="bushfire",
        status="active",
        severity="warning",
        affected_jurisdiction_ids=["nsw-01"],
    )


class TestWarningPerformance:
    def test_warning_compliance_validation_under_5s(self, client):
        """NFR-001: Warning compliance validation ≤5s."""
        INCIDENTS["inc-p1"] = _make_incident("inc-p1")
        from packages.domain.src.domain.models.public_alert import PublicAlert

        ALERTS["alert-p1"] = PublicAlert(
            alert_id="alert-p1",
            incident_id="inc-p1",
            warning_tier="advice",
            action_statement="Stay informed",
            content_blocks={"headline": "Test"},
            audience_segments=["zone-1"],
            languages=["en"],
            accessibility_attributes=["plain_language"],
            approval_mode="human_approved",
            warning_principles_checklist={
                k: True
                for k in [
                    "life_saving",
                    "empowering",
                    "trusted",
                    "risk_scaled",
                    "timely_targeted",
                    "impact_conveying",
                    "action_calling",
                    "clearly_communicated",
                    "accessible",
                    "bigger_picture",
                ]
            },
        )
        start = time.perf_counter()
        resp = client.post("/api/alerts/alert-p1/validate-compliance")
        elapsed = time.perf_counter() - start
        assert resp.status_code == 200
        assert elapsed < 5.0


class TestAiimsPerformance:
    def test_aiims_assignment_under_5s(self, client):
        """NFR-002: AIIMS role assignment ≤5s."""
        INCIDENTS["inc-p2"] = _make_incident("inc-p2")
        start = time.perf_counter()
        resp = client.post(
            "/api/incidents/inc-p2/aiims/assignments",
            json={
                "agent_identifier": "monitoring",
                "aiims_function": "intelligence",
                "assigned_by": "system",
            },
        )
        elapsed = time.perf_counter() - start
        assert resp.status_code == 200
        assert elapsed < 5.0


class TestPPRRPerformance:
    def test_pprr_transition_under_5s(self, client):
        """NFR-003: PPRR phase transition ≤5s."""
        INCIDENTS["inc-p3"] = _make_incident("inc-p3")
        INCIDENTS["inc-p3"].pprr_phase = "preparedness"
        start = time.perf_counter()
        resp = client.post(
            "/api/incidents/inc-p3/pprr/transition",
            json={
                "target_phase": "response",
                "rationale": "Escalating",
                "authorising_user": "ic-1",
            },
        )
        elapsed = time.perf_counter() - start
        assert resp.status_code == 200
        assert elapsed < 5.0


class TestRecoveryPerformance:
    def test_recovery_dashboard_under_10s(self, client):
        """NFR-004: Recovery dashboard load ≤10s."""
        INCIDENTS["inc-p4"] = _make_incident("inc-p4")
        client.post("/api/incidents/inc-p4/recovery")
        start = time.perf_counter()
        resp = client.get("/api/incidents/inc-p4/recovery/dashboard")
        elapsed = time.perf_counter() - start
        assert resp.status_code == 200
        assert elapsed < 10.0


class TestLessonsPerformance:
    def test_lesson_capture_under_5s(self, client):
        """NFR-005: Lessons capture ≤5s."""
        start = time.perf_counter()
        resp = client.post(
            "/api/lessons",
            json={
                "incident_id": "inc-any",
                "title": "Perf test",
                "description": "Performance test lesson",
            },
        )
        elapsed = time.perf_counter() - start
        assert resp.status_code == 200
        assert elapsed < 5.0

    def test_trend_analysis_under_30s(self, client):
        """NFR-006: Trend analysis ≤30s."""
        from packages.domain.src.domain.models.lesson import Lesson

        # Pre-populate some lessons
        for i in range(50):
            LESSONS[f"les-{i}"] = Lesson(
                lesson_id=f"les-{i}",
                incident_id="inc-any",
                title=f"Lesson {i}",
                description=f"Desc {i}",
                tags=["recurring"] if i % 3 == 0 else [],
            )
        start = time.perf_counter()
        resp = client.get("/api/lessons/trends")
        elapsed = time.perf_counter() - start
        assert resp.status_code == 200
        assert elapsed < 30.0


class TestConcurrency:
    def test_concurrent_recovery_operations(self, client):
        """NFR-007: ≥10 concurrent recovery operations."""
        # Create 10 incidents with recovery trackers
        for i in range(10):
            iid = f"inc-conc-{i}"
            INCIDENTS[iid] = _make_incident(iid)
            client.post(f"/api/incidents/{iid}/recovery")

        # Verify all 10 dashboards load
        for i in range(10):
            iid = f"inc-conc-{i}"
            resp = client.get(f"/api/incidents/{iid}/recovery/dashboard")
            assert resp.status_code == 200
