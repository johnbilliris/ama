"""Tests for communication.approval — ApprovalWorkflow."""

import pytest

from communication.approval import ApprovalConflictError, ApprovalWorkflow
from communication.models import AlertStatus, ApprovalMode, ContentBlock, PublicAlert


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
