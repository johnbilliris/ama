"""Tests for Risk Assessment Agent FastAPI endpoints (health + override)."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "apps", "agents"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from risk_assessment.agent import RiskAssessmentAgent, create_app
from risk_assessment.config import RiskAssessmentConfig


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class MockAuditWriter:
    """Lightweight audit writer stub for endpoint tests."""

    def __init__(self, status="healthy", depth=0):
        self._status = status
        self._depth = depth
        self.records = []

    def write(self, record):
        self.records.append(record)

    def get_status(self):
        return self._status

    @property
    def buffer_depth(self):
        return self._depth


def _override_payload(**overrides):
    """Return a valid override request body, merging any overrides."""
    base = {
        "recommendation_id": "rec-001",
        "action": "approve",
        "user_id": "cmd-42",
        "role": "incident_commander",
        "justification": "Field conditions confirm recommendation.",
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# Health endpoint tests
# ---------------------------------------------------------------------------


class TestHealthEndpoint:
    """GET /health tests."""

    def test_health_all_healthy(self):
        """When no agent/pipeline/audit are supplied the LLM is offline → degraded.
        With a fully-mocked healthy agent the overall status is healthy."""
        # Bare app — no agent, no pipeline, no audit writer
        app = create_app(config=RiskAssessmentConfig())
        client = TestClient(app)
        resp = client.get("/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "degraded"  # llm_connectivity offline

        # Now build a fully healthy app
        agent = RiskAssessmentAgent(config=RiskAssessmentConfig())
        mock_llm = MagicMock()
        mock_llm.generate_response.return_value = "pong"
        agent._llm_client = mock_llm

        pipeline = MagicMock()
        pipeline._signal_store = MagicMock()

        audit = MockAuditWriter(status="healthy", depth=0)

        app2 = create_app(
            agent=agent,
            pipeline=pipeline,
            audit_writer=audit,
            config=RiskAssessmentConfig(),
        )
        client2 = TestClient(app2)
        resp2 = client2.get("/health")
        assert resp2.status_code == 200
        assert resp2.json()["status"] == "healthy"

    def test_health_response_schema(self):
        """Response contains all required top-level and nested keys."""
        app = create_app(config=RiskAssessmentConfig())
        client = TestClient(app)
        body = client.get("/health").json()

        assert "status" in body
        assert "agent_version" in body
        assert "timestamp" in body
        assert "checks" in body

        checks = body["checks"]
        assert "llm_connectivity" in checks
        assert "signal_store" in checks
        assert "processing_queue" in checks
        assert "audit_store" in checks

        # Sub-key shapes
        llm = checks["llm_connectivity"]
        assert "status" in llm
        assert "last_checked_at" in llm

        pq = checks["processing_queue"]
        assert "depth" in pq
        assert "status" in pq

        audit = checks["audit_store"]
        assert "status" in audit
        assert "buffer_depth" in audit

    def test_health_llm_offline(self):
        """Agent without an LLM client → llm_connectivity offline, overall degraded."""
        agent = RiskAssessmentAgent(config=RiskAssessmentConfig())
        agent._llm_client = None  # explicitly no LLM

        app = create_app(agent=agent, config=RiskAssessmentConfig())
        client = TestClient(app)
        body = client.get("/health").json()

        assert body["checks"]["llm_connectivity"]["status"] == "offline"
        assert body["status"] == "degraded"

    def test_health_audit_buffering(self):
        """Audit writer with buffer depth > 0 → audit_store 'buffering', overall degraded."""
        audit = MockAuditWriter(status="buffering", depth=5)
        app = create_app(audit_writer=audit, config=RiskAssessmentConfig())
        client = TestClient(app)
        body = client.get("/health").json()

        assert body["checks"]["audit_store"]["status"] == "buffering"
        assert body["checks"]["audit_store"]["buffer_depth"] == 5
        assert body["status"] == "degraded"

    def test_health_audit_degraded(self):
        """Audit writer returning 'degraded' → audit_store degraded, overall degraded."""
        audit = MockAuditWriter(status="degraded", depth=100)
        app = create_app(audit_writer=audit, config=RiskAssessmentConfig())
        client = TestClient(app)
        body = client.get("/health").json()

        assert body["checks"]["audit_store"]["status"] == "degraded"
        assert body["status"] == "degraded"

    def test_health_returns_200_even_when_unhealthy(self):
        """HTTP status is always 200 regardless of health status per contract."""
        # No agent → LLM offline → degraded, but HTTP 200
        app = create_app(config=RiskAssessmentConfig())
        client = TestClient(app)
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] != "healthy"  # confirm it's not fully healthy


# ---------------------------------------------------------------------------
# Override endpoint tests
# ---------------------------------------------------------------------------


class TestOverrideEndpoint:
    """POST /override tests."""

    def test_override_approve(self):
        """action=approve → new_status=approved."""
        app = create_app(config=RiskAssessmentConfig())
        client = TestClient(app)
        resp = client.post("/override", json=_override_payload(action="approve"))
        assert resp.status_code == 200
        body = resp.json()
        assert body["new_status"] == "approved"
        assert body["recommendation_id"] == "rec-001"

    def test_override_reject(self):
        """action=reject → new_status=rejected."""
        app = create_app(config=RiskAssessmentConfig())
        client = TestClient(app)
        resp = client.post("/override", json=_override_payload(action="reject"))
        assert resp.status_code == 200
        assert resp.json()["new_status"] == "rejected"

    def test_override_modify(self):
        """action=modify with modifications → new_status=modified."""
        app = create_app(config=RiskAssessmentConfig())
        client = TestClient(app)
        payload = _override_payload(
            action="modify",
            modifications={"priority": "critical", "radius_km": 10},
        )
        resp = client.post("/override", json=payload)
        assert resp.status_code == 200
        assert resp.json()["new_status"] == "modified"

    def test_override_invalid_action(self):
        """action='invalid' → 422."""
        app = create_app(config=RiskAssessmentConfig())
        client = TestClient(app)
        resp = client.post("/override", json=_override_payload(action="invalid"))
        assert resp.status_code == 422

    def test_override_missing_fields(self):
        """Omitting required fields → 422."""
        app = create_app(config=RiskAssessmentConfig())
        client = TestClient(app)
        # Missing user_id, role, justification
        resp = client.post(
            "/override",
            json={"recommendation_id": "rec-001", "action": "approve"},
        )
        assert resp.status_code == 422

    def test_override_writes_audit(self):
        """Successful override writes an audit record via audit_writer."""
        audit = MockAuditWriter()
        app = create_app(audit_writer=audit, config=RiskAssessmentConfig())
        client = TestClient(app)
        resp = client.post("/override", json=_override_payload())
        assert resp.status_code == 200
        assert len(audit.records) == 1

        record = audit.records[0]
        assert record.recommendation_id == "rec-001"
        assert record.generation_method == "human_override"
        assert "cmd-42" in record.decision_rationale

    def test_override_no_rec_store(self):
        """Override without recommendation_store still succeeds; previous_status defaults to 'proposed'."""
        app = create_app(config=RiskAssessmentConfig())
        client = TestClient(app)
        resp = client.post("/override", json=_override_payload())
        assert resp.status_code == 200
        body = resp.json()
        assert body["previous_status"] == "proposed"
        assert body["new_status"] == "approved"
        assert "audit_record_id" in body
        assert "override_timestamp" in body
