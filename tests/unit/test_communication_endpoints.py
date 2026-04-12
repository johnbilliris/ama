"""Tests for communication.agent — FastAPI endpoints."""

from communication.agent import create_app
from communication.approval import ApprovalWorkflow
from communication.audit import AuditWriter
from communication.config import CommunicationConfig
from communication.models import AlertStatus, ContentBlock, PublicAlert
from fastapi.testclient import TestClient


def _make_app(**overrides):
    config = CommunicationConfig()
    approval = overrides.get("approval_workflow", ApprovalWorkflow(config=config))
    audit = overrides.get("audit_writer", AuditWriter(config=config))
    app = create_app(
        config=config,
        approval_workflow=approval,
        audit_writer=audit,
    )
    return app


def _make_pending_alert(**overrides):
    en_block = ContentBlock(
        language_code="en-AU",
        title="Alert",
        body="Body",
        action_items="Actions",
    )
    defaults = dict(
        alert_id="ca-inc1-v1",
        incident_id="inc1",
        version=1,
        status=AlertStatus.pending_review,
        content_blocks={"en-AU": en_block},
    )
    defaults.update(overrides)
    return PublicAlert(**defaults)


# ---------------------------------------------------------------------------
# GET /health
# ---------------------------------------------------------------------------


class TestHealthEndpoint:
    def test_health_returns_200(self):
        app = _make_app()
        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ("healthy", "degraded")
        assert data["agent"] == "communication"

    def test_health_includes_version(self):
        app = _make_app()
        client = TestClient(app)
        response = client.get("/health")
        data = response.json()
        assert "version" in data
        assert data["version"] == "0.1.0"

    def test_health_includes_config_hash(self):
        app = _make_app()
        client = TestClient(app)
        response = client.get("/health")
        data = response.json()
        assert "config_hash" in data
        assert len(data["config_hash"]) == 64


# ---------------------------------------------------------------------------
# POST /alerts/{alert_id}/approve
# ---------------------------------------------------------------------------


class TestApproveEndpoint:
    def test_approve_returns_approved(self):
        approval = ApprovalWorkflow()
        alert = _make_pending_alert()
        approval._pending_alerts[alert.alert_id] = alert

        app = _make_app(approval_workflow=approval)
        client = TestClient(app)
        response = client.post(
            f"/alerts/{alert.alert_id}/approve",
            json={"user_id": "commander-1", "role": "ic"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "approved"
        assert data["action"] == "approve"

    def test_approve_missing_alert_returns_404(self):
        app = _make_app()
        client = TestClient(app)
        response = client.post(
            "/alerts/ca-missing-v1/approve",
            json={"user_id": "commander-1"},
        )
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# POST /alerts/{alert_id}/reject
# ---------------------------------------------------------------------------


class TestRejectEndpoint:
    def test_reject_returns_rejected(self):
        approval = ApprovalWorkflow()
        alert = _make_pending_alert()
        approval._pending_alerts[alert.alert_id] = alert

        app = _make_app(approval_workflow=approval)
        client = TestClient(app)
        response = client.post(
            f"/alerts/{alert.alert_id}/reject",
            json={
                "user_id": "commander-1",
                "role": "ic",
                "justification": "Inaccurate info",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "rejected"

    def test_reject_without_justification_returns_422(self):
        approval = ApprovalWorkflow()
        alert = _make_pending_alert()
        approval._pending_alerts[alert.alert_id] = alert

        app = _make_app(approval_workflow=approval)
        client = TestClient(app)
        response = client.post(
            f"/alerts/{alert.alert_id}/reject",
            json={"user_id": "commander-1"},
        )
        assert response.status_code == 422

    def test_reject_missing_alert_returns_404(self):
        app = _make_app()
        client = TestClient(app)
        response = client.post(
            "/alerts/ca-missing-v1/reject",
            json={
                "user_id": "commander-1",
                "justification": "test",
            },
        )
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# POST /alerts/{alert_id}/cancel
# ---------------------------------------------------------------------------


class TestCancelEndpoint:
    def test_cancel_returns_cancelled(self):
        approval = ApprovalWorkflow()
        alert = _make_pending_alert()
        approval._pending_alerts[alert.alert_id] = alert

        app = _make_app(approval_workflow=approval)
        client = TestClient(app)
        response = client.post(
            f"/alerts/{alert.alert_id}/cancel",
            json={"user_id": "commander-1", "reason": "False alarm"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "cancelled"

    def test_cancel_from_delivering_returns_409(self):
        approval = ApprovalWorkflow()
        alert = _make_pending_alert(status=AlertStatus.delivering)
        approval._pending_alerts[alert.alert_id] = alert

        app = _make_app(approval_workflow=approval)
        client = TestClient(app)
        response = client.post(
            f"/alerts/{alert.alert_id}/cancel",
            json={"user_id": "commander-1", "reason": "Too late"},
        )
        assert response.status_code == 409

    def test_cancel_missing_alert_returns_404(self):
        app = _make_app()
        client = TestClient(app)
        response = client.post(
            "/alerts/ca-missing-v1/cancel",
            json={"user_id": "commander-1", "reason": "test"},
        )
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# GET /alerts/{alert_id}
# ---------------------------------------------------------------------------


class TestGetAlertEndpoint:
    def test_get_existing_alert(self):
        approval = ApprovalWorkflow()
        alert = _make_pending_alert()
        approval._pending_alerts[alert.alert_id] = alert

        app = _make_app(approval_workflow=approval)
        client = TestClient(app)
        response = client.get(f"/alerts/{alert.alert_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["alert_id"] == alert.alert_id

    def test_get_missing_alert_returns_404(self):
        app = _make_app()
        client = TestClient(app)
        response = client.get("/alerts/ca-missing-v1")
        assert response.status_code == 404
