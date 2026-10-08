from datetime import UTC, datetime

import pytest
from app.core.tenant_context import TenantContext, reset_current_tenant, set_current_tenant
from app.services.operational_store import OperationalStore
from app.services.public_alert_service import (
    PublicAlertService,
    configure_transport_clients,
    stamp_alert_content_version,
)
from app.services.state_store import reset_state
from fastapi import HTTPException

from packages.domain.src.domain.models.public_alert import PublicAlert


@pytest.fixture(autouse=True)
def _live_tenant_context():
    token = set_current_tenant(TenantContext(agency_id="ses-nsw", jurisdiction_ids=("nsw",), tenant_id="live"))
    try:
        yield
    finally:
        reset_current_tenant(token)


class _AckClient:
    def send(self, *, alert, channel: str, recipient: str, payload: dict):
        return {
            "acknowledged": True,
            "providerMessageId": f"{channel}-{recipient}",
            "contentVersion": alert.content_blocks.get("contentVersion"),
            "payload": payload,
        }


class _FailClient:
    def send(self, *, alert, channel: str, recipient: str, payload: dict):
        raise RuntimeError("provider_timeout")


def _seed_published_alert(*, languages: list[str], channels: list[str]) -> None:
    reset_state()
    store = OperationalStore("live")
    alert = PublicAlert(
        alert_id="alert-010",
        incident_id="incident-010",
        tenant_id="live",
        mode="live",
        status="published",
        audience_segments=["recipient-1", "recipient-1", "recipient-2"],
        languages=languages,
        channel_set=channels,
        content_blocks={"headline": "Stay alert", "body": "Move to safer ground"},
        published_at=datetime.now(UTC),
    )
    stamp_alert_content_version(alert)
    store.alerts.put(alert.alert_id, alert)


def test_aud010_no_client_and_non_en_broadcast_never_delivered() -> None:
    _seed_published_alert(languages=["zh-Hans"], channels=["emergency_broadcast", "sms"])
    configure_transport_clients({"sms": None, "emergency_broadcast": None})

    receipts = PublicAlertService().deliver("alert-010")

    assert receipts
    assert all(
        receipt["status"] in {"skipped", "failed", "simulation", "submitted", "acknowledged"} for receipt in receipts
    )
    assert all(receipt["status"] != "delivered" for receipt in receipts)


def test_aud010_acknowledged_receipts_include_binding_fields() -> None:
    _seed_published_alert(languages=["en-AU", "zh-Hans"], channels=["sms"])
    configure_transport_clients({"sms": _AckClient()})

    receipts = PublicAlertService().deliver("alert-010")

    assert len(receipts) == 4
    assert all(receipt["alertId"] == "alert-010" for receipt in receipts)
    assert all(receipt["contentVersion"] for receipt in receipts)
    assert all(receipt["status"] == "acknowledged" for receipt in receipts)


def test_aud010_partial_failures_are_preserved() -> None:
    _seed_published_alert(languages=["en-AU"], channels=["sms", "push"])
    configure_transport_clients({"sms": _AckClient(), "push": _FailClient()})

    receipts = PublicAlertService().deliver("alert-010")

    statuses = {(receipt["channel"], receipt["status"]) for receipt in receipts}
    assert ("sms", "acknowledged") in statuses
    assert ("push", "failed") in statuses


def test_aud010_update_draft_rejects_empty_languages() -> None:
    reset_state()
    store = OperationalStore.current()
    draft = PublicAlert(
        alert_id="alert-010-draft",
        incident_id="incident-010",
        tenant_id="live",
        mode="live",
        status="draft",
        audience_segments=["recipient"],
        languages=["en-AU"],
        channel_set=["sms"],
        content_blocks={"headline": "H", "body": "B"},
    )
    store.alerts.put(draft.alert_id, draft)

    with pytest.raises(HTTPException) as exc:
        PublicAlertService().update_draft("alert-010-draft", languages=[])
    assert exc.value.status_code == 422
