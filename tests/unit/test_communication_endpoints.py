"""Tests for communication.agent — FastAPI endpoints."""

from unittest.mock import MagicMock

import pytest
from common.entra_principal import AuthenticatedPrincipal
from communication.agent import AdmissionRejectedError, BoundedAdmissionController, create_app
from communication.approval import ApprovalWorkflow
from communication.audit import AuditWriter
from communication.config import CommunicationConfig
from communication.delivery import MultiChannelDeliveryService
from communication.models import AlertStatus, AudienceSegment, ChannelType, ContentBlock, PublicAlert
from communication.pipeline import CommunicationProcessingPipeline
from communication.repository import CommunicationAlertRepository
from fastapi.testclient import TestClient


def _principal(
    *,
    subject: str = "commander-1",
    tenant_id: str = "live",
    roles: tuple[str, ...] = ("ic",),
) -> AuthenticatedPrincipal:
    return AuthenticatedPrincipal(subject=subject, tenant_id=tenant_id, roles=roles)


def _make_app(**overrides):
    config = CommunicationConfig()
    approval = overrides.get("approval_workflow", ApprovalWorkflow(config=config))
    audit = overrides.get("audit_writer", AuditWriter(config=config))
    app = create_app(
        config=config,
        approval_workflow=approval,
        audit_writer=audit,
        principal_resolver=overrides.get("principal_resolver", lambda _request: _principal()),
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
        tenant_id="live",
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


class TestAlertAuthorization:
    @pytest.mark.parametrize(
        ("method", "path", "body"),
        [
            ("post", "/alerts/ca-inc1-v1/approve", {}),
            ("post", "/alerts/ca-inc1-v1/reject", {"justification": "unsafe"}),
            ("post", "/alerts/ca-inc1-v1/modify", {"modifications": {"title": "Updated"}}),
            ("post", "/alerts/ca-inc1-v1/cancel", {"reason": "withdrawn"}),
            ("get", "/alerts/ca-inc1-v1", None),
            ("get", "/alerts/ca-inc1-v1/delivery-status", None),
        ],
    )
    def test_every_alert_route_requires_bearer_authentication(self, method, path, body):
        app = create_app(config=CommunicationConfig())
        client = TestClient(app)

        response = client.request(method, path, json=body)

        assert response.status_code == 401

    def test_non_commander_cannot_read_alert(self):
        approval = ApprovalWorkflow()
        alert = _make_pending_alert()
        approval._pending_alerts[alert.alert_id] = alert
        app = _make_app(
            approval_workflow=approval,
            principal_resolver=lambda _request: _principal(roles=("observer",)),
        )

        response = TestClient(app).get(f"/alerts/{alert.alert_id}")

        assert response.status_code == 403

    def test_foreign_tenant_cannot_discover_alert(self):
        approval = ApprovalWorkflow()
        alert = _make_pending_alert(tenant_id="tenant-one", mode="rehearsal")
        approval._pending_alerts[alert.alert_id] = alert
        app = _make_app(
            approval_workflow=approval,
            principal_resolver=lambda _request: _principal(tenant_id="tenant-two"),
        )

        response = TestClient(app).get(f"/alerts/{alert.alert_id}")

        assert response.status_code == 404

    def test_body_identity_cannot_impersonate_commander(self):
        approval = ApprovalWorkflow()
        alert = _make_pending_alert()
        approval._pending_alerts[alert.alert_id] = alert
        app = _make_app(approval_workflow=approval)

        response = TestClient(app).post(
            f"/alerts/{alert.alert_id}/approve",
            json={"user_id": "forged-commander", "role": "ic"},
        )

        assert response.status_code == 403
        assert alert.status == AlertStatus.pending_review

    def test_verified_oid_owns_approval_and_audit(self):
        approval = ApprovalWorkflow()
        alert = _make_pending_alert()
        approval._pending_alerts[alert.alert_id] = alert
        audit = AuditWriter()
        app = _make_app(approval_workflow=approval, audit_writer=audit)

        response = TestClient(app).post(
            f"/alerts/{alert.alert_id}/approve",
            json={"user_id": "commander-1", "role": "ic"},
        )

        assert response.status_code == 200
        assert response.json()["user_id"] == "commander-1"
        assert "commander-1" in audit._buffer[-1].record.output_summary


class TestDeliveryStatusRoutes:
    class _Sms:
        def send(self, **_kwargs):
            return [{"successful": True, "message_id": "sms-accepted-1"}]

    @staticmethod
    def _app_for_delivery(*, sms_client):
        config = CommunicationConfig(delivery_max_retries=0, sms_sender_identity="EmergencyAlert")
        repository = CommunicationAlertRepository()
        alert = _make_pending_alert(
            status=AlertStatus.approved,
            approval_mode="human_approved",
            approved_by_user_id="commander-1",
            approved_by_role="ic",
            approved_at="2026-09-17T00:00:00Z",
            channel_set=[ChannelType.sms],
        )
        segment = AudienceSegment(
            segment_id="segment-1",
            zone_level=1,
            recipient_ids=["recipient-1"],
            delivery_channels=[ChannelType.sms],
        )
        repository.create(alert, [segment])
        workflow = ApprovalWorkflow(config=config, alert_repository=repository)
        delivery = MultiChannelDeliveryService(
            config=config,
            sms_client=sms_client,
            approval_resolver=lambda tenant_id, alert_id, _version: repository.get(tenant_id, alert_id),
        )
        pipeline = CommunicationProcessingPipeline(
            config=config,
            approval_workflow=workflow,
            alert_repository=repository,
            delivery_service=delivery,
        )
        app = create_app(
            config=config,
            pipeline=pipeline,
            approval_workflow=workflow,
            principal_resolver=lambda _request: _principal(),
        )
        return app, repository, alert

    def test_provider_acceptance_remains_in_progress_and_is_persisted(self):
        app, repository, alert = self._app_for_delivery(sms_client=self._Sms())
        client = TestClient(app)

        response = client.post(f"/alerts/{alert.alert_id}/deliver")
        status = client.get(f"/alerts/{alert.alert_id}/delivery-status")

        assert response.status_code == 200
        assert response.json()[0]["delivery_status"] == "accepted"
        assert repository.require("live", alert.alert_id).status == AlertStatus.delivering
        assert status.json()["overall_status"] == "delivering"
        assert status.json()["delivery_summary"]["accepted"] == 1
        assert status.json()["by_channel"]["sms"][0]["provider_receipt_ids"] == ["sms-accepted-1"]

    def test_unconfigured_provider_persists_all_failed_state(self):
        app, repository, alert = self._app_for_delivery(sms_client=None)

        response = TestClient(app).post(f"/alerts/{alert.alert_id}/deliver")

        assert response.status_code == 200
        assert response.json()[0]["delivery_status"] == "unconfigured"
        assert repository.require("live", alert.alert_id).status == AlertStatus.delivery_failed


class TestBoundedAdmission:
    @pytest.mark.asyncio
    async def test_rejects_above_limit_and_releases_after_completion(self):
        import asyncio

        controller = BoundedAdmissionController(1)
        entered = asyncio.Event()
        release = asyncio.Event()

        def blocking_work():
            event_loop.call_soon_threadsafe(entered.set)
            asyncio.run_coroutine_threadsafe(release.wait(), event_loop).result()
            return "done"

        event_loop = asyncio.get_running_loop()
        first = asyncio.create_task(controller.run(blocking_work))
        await entered.wait()

        with pytest.raises(AdmissionRejectedError):
            await controller.run(lambda: "overflow")

        release.set()
        assert await first == "done"
        assert controller.active == 0
        assert await controller.run(lambda: "next") == "next"

    @pytest.mark.asyncio
    async def test_failure_releases_capacity(self):
        controller = BoundedAdmissionController(1)

        def fail():
            raise RuntimeError("failed")

        with pytest.raises(RuntimeError, match="failed"):
            await controller.run(fail)

        assert controller.active == 0


class TestHandoffAuthorization:
    def test_process_handoff_requires_producer_role(self):
        app = _make_app(principal_resolver=lambda _request: _principal(roles=("observer",)))
        response = TestClient(app).post(
            "/process-handoff",
            json={
                "handoffId": "handoff-1",
                "incidentId": "inc-1",
                "sourceAgent": "risk_assessment",
                "targetAgent": "communication",
                "scopeKey": "inc-1",
                "confidence": 0.9,
                "tenantId": "live",
                "payload": {
                    "recommendationId": "rec-1",
                    "assessmentId": "assessment-1",
                    "summary": "Alert",
                    "explanation": "Risk threshold exceeded",
                },
            },
        )

        assert response.status_code == 403

    def test_process_handoff_rejects_foreign_tenant_before_pipeline(self):
        pipeline = MagicMock()
        app = create_app(
            config=CommunicationConfig(),
            pipeline=pipeline,
            principal_resolver=lambda _request: _principal(
                tenant_id="tenant-one",
                roles=("RiskAssessmentAgent",),
            ),
        )
        response = TestClient(app).post(
            "/process-handoff",
            json={
                "handoffId": "handoff-1",
                "incidentId": "inc-1",
                "sourceAgent": "risk_assessment",
                "targetAgent": "communication",
                "scopeKey": "inc-1",
                "confidence": 0.9,
                "tenantId": "tenant-two",
                "payload": {
                    "recommendationId": "rec-1",
                    "assessmentId": "assessment-1",
                    "summary": "Alert",
                    "explanation": "Risk threshold exceeded",
                },
            },
        )

        assert response.status_code == 403
        pipeline.process_handoff.assert_not_called()
