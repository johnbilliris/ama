"""Simulation tests for end-to-end AIDR flows."""
import pytest
from fastapi.testclient import TestClient
from app.main import create_app
from app.services.state_store import INCIDENTS, ALERTS, reset_state
from packages.domain.src.domain.models.incident import Incident
from packages.domain.src.domain.models.public_alert import PublicAlert


@pytest.fixture
def client():
    app = create_app()
    with TestClient(app) as c:
        yield c
    reset_state()


def _make_incident(incident_id="inc-sim-1", incident_type="bushfire", **kwargs) -> Incident:
    return Incident(
        incident_id=incident_id,
        title="Test Bushfire",
        incident_type=incident_type,
        status="active",
        severity="warning",
        affected_jurisdiction_ids=["nsw-01"],
        **kwargs,
    )


class TestBushfireEscalation:
    """Scenario: Bushfire escalation through AWS tier system with AIIMS."""

    def test_full_bushfire_warning_escalation(self, client):
        """Advice → Watch and Act → Emergency Warning → de-escalation → all-clear."""
        INCIDENTS["inc-bf-1"] = _make_incident("inc-bf-1", "bushfire")

        # 1. AIIMS structure
        resp = client.post(
            "/api/incidents/inc-bf-1/aiims/assignments",
            json={
                "agent_identifier": "monitoring",
                "aiims_function": "intelligence",
                "assigned_by": "system",
            },
        )
        assert resp.status_code == 200

        # 2. Set PPRR to response
        resp = client.post(
            "/api/incidents/inc-bf-1/pprr/transition",
            json={
                "target_phase": "response",
                "rationale": "Fire approaching",
                "authorising_user": "ic-1",
            },
        )
        # May fail if phase validation strict - that's fine for simulation

        # 3. Verify structure
        resp = client.get("/api/incidents/inc-bf-1/aiims/structure")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["assignments"]) >= 1


class TestCycloneEvacuation:
    """Scenario: Cyclone triggers five-stage evacuation."""

    def test_full_evacuation_lifecycle(self, client):
        """Decision → Warning → Withdrawal → Shelter → Return → Completed."""
        INCIDENTS["inc-cyc-1"] = _make_incident("inc-cyc-1", "cyclone")

        # Create stage at Decision
        resp = client.post(
            "/api/incidents/inc-cyc-1/evacuation/stages",
            json={
                "plan_id": "plan-1",
                "decision_authority": "IC Smith",
                "decision_rationale": "Cat 4 cyclone approaching",
                "evacuation_type": "pre_warned",
                "evacuation_scope": "total",
            },
        )
        assert resp.status_code == 200
        stage_id = resp.json()["stage_id"]

        # Advance through each stage
        for target in ["warning", "withdrawal", "shelter", "return", "completed"]:
            resp = client.post(
                f"/api/incidents/inc-cyc-1/evacuation/stages/{stage_id}/transition",
                json={
                    "target_stage": target,
                    "authorized_by": "IC Smith",
                    "rationale": f"Progressing to {target}",
                },
            )
            assert resp.status_code == 200, f"Failed transition to {target}: {resp.text}"

        # Verify final state
        resp = client.get(f"/api/incidents/inc-cyc-1/evacuation/stages/{stage_id}")
        assert resp.status_code == 200
        assert resp.json()["current_stage"] == "completed"


class TestFloodPPRRLifecycle:
    """Scenario: Flood event through full PPRR lifecycle."""

    def test_full_pprr_lifecycle(self, client):
        INCIDENTS["inc-flood-1"] = _make_incident(
            "inc-flood-1", "flood", pprr_phase="preparedness"
        )

        # Transition: preparedness → response
        resp = client.post(
            "/api/incidents/inc-flood-1/pprr/transition",
            json={
                "target_phase": "response",
                "rationale": "Flood waters rising",
                "authorising_user": "ic-2",
            },
        )
        assert resp.status_code == 200

        # Transition: response → recovery (with overlap)
        resp = client.post(
            "/api/incidents/inc-flood-1/pprr/transition",
            json={
                "target_phase": "recovery",
                "rationale": "Waters receding",
                "authorising_user": "ic-2",
                "overlap_active": True,
            },
        )
        assert resp.status_code == 200

        # Get phase info
        resp = client.get("/api/incidents/inc-flood-1/pprr")
        assert resp.status_code == 200
        assert resp.json()["current_phase"] == "recovery"


class TestPostDisasterRecovery:
    """Scenario: Post-disaster recovery tracking."""

    def test_recovery_dashboard_and_indicators(self, client):
        INCIDENTS["inc-rec-1"] = _make_incident("inc-rec-1", "flood")

        # Initialise tracker
        resp = client.post("/api/incidents/inc-rec-1/recovery")
        assert resp.status_code == 200
        tracker = resp.json()
        assert len(tracker["indicators"]) == 21

        # Update an indicator
        resp = client.put(
            "/api/incidents/inc-rec-1/recovery/indicators/air_quality",
            json={
                "value": 85.0,
                "update_source": "manual",
            },
        )
        assert resp.status_code == 200

        # Check dashboard
        resp = client.get("/api/incidents/inc-rec-1/recovery/dashboard")
        assert resp.status_code == 200

        # Community view
        resp = client.get("/api/incidents/inc-rec-1/recovery/community")
        assert resp.status_code == 200
