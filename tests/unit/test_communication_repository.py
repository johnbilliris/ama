from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from communication.approval import ApprovalNotificationError, ApprovalWorkflow
from communication.models import AlertStatus, AudienceSegment, ChangeType, ContentBlock, PublicAlert
from communication.repository import CommunicationAlertRepository


def _alert() -> PublicAlert:
    return PublicAlert(
        alert_id="ca-inc-1-v1",
        incident_id="inc-1",
        version=1,
        tenant_id="tenant-one",
        mode="rehearsal",
        content_blocks={"en-AU": ContentBlock(language_code="en-AU", title="Alert", body="Body", action_items="Act")},
    )


def test_alert_aggregate_survives_repository_replacement() -> None:
    documents = {}
    first = CommunicationAlertRepository(documents=documents)
    alert = _alert().model_copy(update={"commander_chain": ["ic-1", "deputy-1", "control-1"]})
    segment = AudienceSegment(zone_level=1, recipient_ids=["recipient-a"])

    first.create(alert, [segment])
    restarted = CommunicationAlertRepository(documents=documents)

    assert restarted.require("tenant-one", alert.alert_id).alert_id == alert.alert_id
    assert restarted.audience_segments("tenant-one", alert.alert_id)[0].recipient_ids == ["recipient-a"]


def test_alert_lookup_is_tenant_partitioned() -> None:
    repository = CommunicationAlertRepository()
    alert = _alert()
    repository.create(alert, [])

    assert repository.get("tenant-two", alert.alert_id) is None


def test_stale_etag_cannot_overwrite_a_completed_decision() -> None:
    repository = CommunicationAlertRepository()
    alert = _alert()
    repository.create(alert, [])
    first = repository.require(alert.tenant_id, alert.alert_id)
    stale = repository.require(alert.tenant_id, alert.alert_id)

    first.status = AlertStatus.approved
    repository.replace(first)
    stale.status = AlertStatus.rejected

    try:
        repository.replace(stale)
    except RuntimeError as exc:
        assert "412" in str(exc)
    else:
        raise AssertionError("Stale decision overwrote the winning transition")


def test_persisted_content_cannot_be_mutated_in_place() -> None:
    repository = CommunicationAlertRepository()
    alert = _alert()
    repository.create(alert, [])
    persisted = repository.require(alert.tenant_id, alert.alert_id)
    persisted.content_blocks["en-AU"].body = "Changed after persistence"

    with pytest.raises(ValueError, match="content_blocks"):
        repository.replace(persisted)


def test_supersession_records_replacement_without_mutating_content() -> None:
    repository = CommunicationAlertRepository()
    original = _alert().model_copy(update={"status": AlertStatus.delivered})
    replacement = _alert().model_copy(
        update={
            "alert_id": "ca-inc-1-v2",
            "version": 2,
            "status": AlertStatus.delivered,
            "change_type": ChangeType.all_clear,
            "change_summary": "Threat passed",
            "referenced_alert_id": original.alert_id,
        }
    )
    repository.create(original, [])
    repository.create(replacement, [])

    repository.supersede("tenant-one", original.alert_id, replacement.alert_id)

    persisted = repository.require("tenant-one", original.alert_id)
    assert persisted.status == AlertStatus.superseded
    assert persisted.superseded_by_alert_id == replacement.alert_id
    assert persisted.content_blocks == original.content_blocks


@pytest.mark.asyncio
async def test_failed_approval_notification_is_recovered_with_same_request_id() -> None:
    class _Publisher:
        def __init__(self) -> None:
            self.fail = True
            self.messages = []

        async def publish(self, payload) -> None:
            self.messages.append(payload)
            if self.fail:
                raise RuntimeError("queue unavailable")

    repository = CommunicationAlertRepository()
    alert = _alert().model_copy(update={"commander_chain": ["ic-1", "deputy-1", "control-1"]})
    repository.create(alert, [AudienceSegment(zone_level=1, recipient_ids=["recipient-a"])])
    publisher = _Publisher()
    workflow = ApprovalWorkflow(service_bus_client=publisher, alert_repository=repository)

    try:
        await workflow.request_approval(alert)
    except ApprovalNotificationError:
        pass
    else:
        raise AssertionError("Queue failure was reported as successful")

    failed = repository.approval_requests(alert.tenant_id, alert.alert_id)
    assert len(failed) == 1
    assert failed[0]["status"] == "failed"
    request_id = failed[0]["request_id"]

    publisher.fail = False
    assert await workflow.retry_pending_notifications() == 1
    recovered = repository.approval_requests(alert.tenant_id, alert.alert_id)
    assert recovered[0]["request_id"] == request_id
    assert recovered[0]["status"] == "sent"
    assert recovered[0]["audience_segments"][0]["recipient_ids"] == ["recipient-a"]


def test_expiry_uses_persisted_deadline_and_history_remains_immutable() -> None:
    repository = CommunicationAlertRepository()
    now = datetime.now(UTC)
    expired = _alert().model_copy(update={"status": AlertStatus.delivered, "expires_at": now - timedelta(seconds=1)})
    active = _alert().model_copy(
        update={
            "alert_id": "ca-inc-1-v2",
            "version": 2,
            "status": AlertStatus.delivered,
            "change_type": ChangeType.update,
            "change_summary": "Updated guidance",
            "referenced_alert_id": expired.alert_id,
            "expires_at": now + timedelta(hours=1),
        }
    )
    repository.create(expired, [])
    repository.create(active, [])

    assert repository.expire_due(now) == [expired.alert_id]
    assert repository.expire_due(now) == []
    history = repository.version_history("tenant-one", "inc-1")
    assert [alert.version for alert in history] == [1, 2]
    assert [alert.status for alert in history] == [AlertStatus.expired, AlertStatus.delivered]
    assert repository.version_history("tenant-two", "inc-1") == []
