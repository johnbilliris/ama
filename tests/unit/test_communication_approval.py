"""Tests for communication.approval — ApprovalWorkflow."""

import pytest
from communication.approval import ApprovalConflictError, ApprovalWorkflow
from communication.audit import AuditWriter
from communication.models import AlertStatus, ApprovalMode, ContentBlock, PublicAlert
from communication.repository import CommunicationAlertRepository


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
# Approve
# ---------------------------------------------------------------------------


class TestApprove:
    def test_approve_transitions_to_approved(self):
        workflow = ApprovalWorkflow()
        alert = _make_pending_alert()
        workflow._pending_alerts[alert.alert_id] = alert

        result = workflow.process_approval(
            alert_id=alert.alert_id,
            user_id="commander-1",
            role="incident_commander",
            action="approve",
        )
        assert result.status == AlertStatus.approved
        assert result.approval_mode == ApprovalMode.human_approved
        assert result.approved_by_user_id == "commander-1"

    def test_approve_sets_approved_at(self):
        workflow = ApprovalWorkflow()
        alert = _make_pending_alert()
        workflow._pending_alerts[alert.alert_id] = alert

        result = workflow.process_approval(
            alert_id=alert.alert_id,
            user_id="commander-1",
            role="ic",
            action="approve",
        )
        assert result.approved_at is not None


# ---------------------------------------------------------------------------
# Reject
# ---------------------------------------------------------------------------


class TestReject:
    def test_reject_requires_justification(self):
        workflow = ApprovalWorkflow()
        alert = _make_pending_alert()
        workflow._pending_alerts[alert.alert_id] = alert

        with pytest.raises(ValueError, match="Justification"):
            workflow.process_approval(
                alert_id=alert.alert_id,
                user_id="commander-1",
                role="ic",
                action="reject",
                justification=None,
            )

    def test_reject_transitions_to_rejected(self):
        workflow = ApprovalWorkflow()
        alert = _make_pending_alert()
        workflow._pending_alerts[alert.alert_id] = alert

        result = workflow.process_approval(
            alert_id=alert.alert_id,
            user_id="commander-1",
            role="ic",
            action="reject",
            justification="Inaccurate data",
        )
        assert result.status == AlertStatus.rejected
        assert result.approval_justification == "Inaccurate data"
        assert result.approved_by_user_id == "commander-1"
        assert result.approved_by_role == "ic"
        assert result.decision_at is not None


# ---------------------------------------------------------------------------
# Cancel
# ---------------------------------------------------------------------------


class TestCancel:
    def test_cancel_from_pending_review(self):
        workflow = ApprovalWorkflow()
        alert = _make_pending_alert()
        workflow._pending_alerts[alert.alert_id] = alert

        result = workflow.cancel_alert(
            alert_id=alert.alert_id,
            user_id="commander-1",
            role="ic",
            reason="False alarm",
        )
        assert result.status == AlertStatus.cancelled
        assert result.approval_action == "cancel"
        assert result.approved_by_user_id == "commander-1"
        assert result.approved_by_role == "ic"
        assert result.approval_justification == "False alarm"
        assert result.decision_at is not None

    def test_cancel_from_drafting(self):
        workflow = ApprovalWorkflow()
        alert = _make_pending_alert(status=AlertStatus.drafting)
        workflow._pending_alerts[alert.alert_id] = alert

        result = workflow.cancel_alert(
            alert_id=alert.alert_id,
            user_id="commander-1",
            role="ic",
            reason="Not needed",
        )
        assert result.status == AlertStatus.cancelled

    def test_cancel_from_approved(self):
        workflow = ApprovalWorkflow()
        alert = _make_pending_alert(status=AlertStatus.approved)
        workflow._pending_alerts[alert.alert_id] = alert

        result = workflow.cancel_alert(
            alert_id=alert.alert_id,
            user_id="commander-1",
            role="ic",
            reason="Changed mind",
        )
        assert result.status == AlertStatus.cancelled

    def test_cancel_from_delivering_raises_conflict(self):
        workflow = ApprovalWorkflow()
        alert = _make_pending_alert(status=AlertStatus.delivering)
        workflow._pending_alerts[alert.alert_id] = alert

        with pytest.raises(ApprovalConflictError):
            workflow.cancel_alert(
                alert_id=alert.alert_id,
                user_id="commander-1",
                role="ic",
                reason="Too late",
            )

    def test_cancel_from_delivered_raises_conflict(self):
        workflow = ApprovalWorkflow()
        alert = _make_pending_alert(status=AlertStatus.delivered)
        workflow._pending_alerts[alert.alert_id] = alert

        with pytest.raises(ApprovalConflictError):
            workflow.cancel_alert(
                alert_id=alert.alert_id,
                user_id="commander-1",
                role="ic",
                reason="Recall",
            )


# ---------------------------------------------------------------------------
# Alert not found
# ---------------------------------------------------------------------------


class TestAlertNotFound:
    def test_process_approval_unknown_alert_raises(self):
        workflow = ApprovalWorkflow()
        with pytest.raises(ValueError, match="not found"):
            workflow.process_approval(
                alert_id="ca-unknown-v1",
                user_id="commander-1",
                role="ic",
                action="approve",
            )

    def test_cancel_unknown_alert_raises(self):
        workflow = ApprovalWorkflow()
        with pytest.raises(ValueError, match="not found"):
            workflow.cancel_alert(
                alert_id="ca-unknown-v1",
                user_id="commander-1",
                role="ic",
                reason="test",
            )


class TestModifiedVersion:
    def test_modification_uses_allocated_version_and_preserves_original(self):
        workflow = ApprovalWorkflow()
        original = _make_pending_alert()
        workflow._pending_alerts[original.alert_id] = original
        workflow._version_counter._local_counters[("live", "inc1")] = 1

        modified = workflow.create_modified_version(
            original,
            {"content_overrides": {"en-AU": {"body": "Updated body"}}},
            user_id="commander-1",
            role="ic",
        )

        assert modified.version == 2
        assert modified.status == AlertStatus.pending_review
        assert modified.content_blocks["en-AU"].body == "Updated body"
        assert original.content_blocks["en-AU"].body == "Body"
        assert modified.approval_mode is None

    def test_unknown_modification_field_is_rejected(self):
        workflow = ApprovalWorkflow()
        alert = _make_pending_alert()

        with pytest.raises(ValueError, match="Unsupported modification fields"):
            workflow.create_modified_version(
                alert,
                {"status": "approved"},
                user_id="commander-1",
                role="ic",
            )


# ---------------------------------------------------------------------------
# Double-approval conflict
# ---------------------------------------------------------------------------


class TestDoubleApprovalConflict:
    def test_second_approval_raises_conflict(self):
        workflow = ApprovalWorkflow()
        alert = _make_pending_alert()
        workflow._pending_alerts[alert.alert_id] = alert

        workflow.process_approval(
            alert_id=alert.alert_id,
            user_id="commander-1",
            role="ic",
            action="approve",
        )

        with pytest.raises(ApprovalConflictError):
            workflow.process_approval(
                alert_id=alert.alert_id,
                user_id="commander-2",
                role="ic",
                action="approve",
            )


# ---------------------------------------------------------------------------
# Pending count
# ---------------------------------------------------------------------------


class TestPendingCount:
    def test_pending_count_increments(self):
        workflow = ApprovalWorkflow()
        assert workflow.get_pending_count() == 0

        alert = _make_pending_alert()
        workflow._pending_alerts[alert.alert_id] = alert
        assert workflow.get_pending_count() == 1

    def test_pending_count_decrements_after_approval(self):
        workflow = ApprovalWorkflow()
        alert = _make_pending_alert()
        workflow._pending_alerts[alert.alert_id] = alert

        workflow.process_approval(
            alert_id=alert.alert_id,
            user_id="commander-1",
            role="ic",
            action="approve",
        )
        assert workflow.get_pending_count() == 0


class TestDurableEscalation:
    class _Publisher:
        def __init__(self):
            self.messages = []

        async def publish(self, payload):
            self.messages.append(payload)

    @staticmethod
    def _workflow(alert, *, config=None):
        repository = CommunicationAlertRepository()
        repository.create(alert, [])
        publisher = TestDurableEscalation._Publisher()
        audit = AuditWriter()
        workflow = ApprovalWorkflow(
            config=config,
            service_bus_client=publisher,
            alert_repository=repository,
            audit_writer=audit,
        )
        return workflow, repository, publisher, audit

    @pytest.mark.asyncio
    async def test_emergency_warning_uses_five_minute_deadline(self):
        alert = _make_pending_alert(
            commander_chain=["ic-1", "deputy-1"],
            warning_tier="Emergency Warning",
        )
        workflow, repository, publisher, _audit = self._workflow(alert)

        await workflow.request_approval(alert)

        persisted = repository.require("live", alert.alert_id)
        request = repository.approval_requests("live", alert.alert_id)[0]
        assert persisted.current_commander_id == "ic-1"
        assert request["assigned_commander_id"] == "ic-1"
        assert 299 <= (persisted.approval_deadline_at - persisted.updated_at).total_seconds() <= 301
        assert publisher.messages[0]["request_id"] == request["request_id"]
        workflow._escalation_timers[("live", alert.alert_id)].cancel()

    @pytest.mark.asyncio
    async def test_escalation_uses_real_chain_and_exhaustion_never_approves(self):
        alert = _make_pending_alert(commander_chain=["ic-1", "deputy-1"])
        workflow, repository, _publisher, audit = self._workflow(alert)

        await workflow.request_approval(alert)
        workflow._escalation_timers[("live", alert.alert_id)].cancel()
        await workflow.escalate(alert.alert_id, tenant_id="live")
        workflow._escalation_timers[("live", alert.alert_id)].cancel()
        escalated = repository.require("live", alert.alert_id)
        assert escalated.current_commander_id == "deputy-1"
        assert escalated.status == AlertStatus.pending_review

        await workflow.escalate(alert.alert_id, tenant_id="live")
        exhausted = repository.require("live", alert.alert_id)
        assert exhausted.escalation_exhausted is True
        assert exhausted.status == AlertStatus.pending_review
        assert audit._buffer[-1].record.escalation_details["to_commander_id"] is None

    @pytest.mark.asyncio
    async def test_restart_recovers_persisted_deadline(self):
        alert = _make_pending_alert(commander_chain=["ic-1", "deputy-1"])
        workflow, repository, _publisher, _audit = self._workflow(alert)
        await workflow.request_approval(alert)
        workflow._escalation_timers[("live", alert.alert_id)].cancel()

        restarted = ApprovalWorkflow(
            service_bus_client=self._Publisher(),
            alert_repository=repository,
        )
        assert await restarted.recover_escalation_deadlines() == 1
        assert ("live", alert.alert_id) in restarted._escalation_timers
        restarted._escalation_timers[("live", alert.alert_id)].cancel()
