from datetime import UTC, datetime
import logging
from typing import Any

from app.core.tenant_context import get_current_tenant
from app.services.state_store import ALERTS
from fastapi import HTTPException

from packages.domain.src.domain.models.public_alert import PublicAlert

logger = logging.getLogger(__name__)

DELIVERY_TEMPLATES: dict[str, dict[str, str]] = {
    "evacuation": {
        "headline": "Prepare to evacuate if directed.",
        "body": "Follow emergency services instructions for your area.",
    },
    "shelter_in_place": {
        "headline": "Shelter in place.",
        "body": "Stay indoors and monitor official updates.",
    },
    "all_clear": {
        "headline": "All-clear notification.",
        "body": "The immediate threat has passed. Follow agency guidance before returning.",
    },
}


CHANNEL_ADAPTERS = {
    "sms": lambda alert: {
        "channel": "sms",
        "recipients": alert.audience_segments,
        "headline": alert.content_blocks.get("headline", ""),
    },
    "push": lambda alert: {
        "channel": "push",
        "recipients": alert.audience_segments,
        "headline": alert.content_blocks.get("headline", ""),
    },
    "email": lambda alert: {
        "channel": "email",
        "recipients": alert.audience_segments,
        "body": alert.content_blocks.get("body", ""),
    },
}


def _validate_publishable(alert: PublicAlert) -> None:
    if alert.status not in {"approved", "pending_approval"}:
        raise HTTPException(
            status_code=409, detail=f"Alert status '{alert.status}' is not publishable"
        )
    if not alert.content_blocks.get("headline"):
        raise HTTPException(status_code=422, detail="Alert must have a headline before publishing")
    if not alert.channel_set:
        raise HTTPException(status_code=422, detail="Alert must target at least one channel")


class PublicAlertService:
    def apply_template(self, alert_id: str, template_key: str) -> PublicAlert:
        alert = ALERTS[alert_id]
        template = DELIVERY_TEMPLATES.get(template_key)
        if template is None:
            raise HTTPException(status_code=404, detail=f"Unknown template '{template_key}'")
        alert.content_blocks.update(template)
        return alert

    def publish(self, alert_id: str, published_by_persona_id: str) -> PublicAlert:
        alert = ALERTS[alert_id]
        _validate_publishable(alert)
        alert.status = "published"
        alert.published_at = datetime.now(UTC)
        alert.content_blocks["publishedBy"] = published_by_persona_id
        return alert

    def supersede(self, alert_id: str, new_alert_id: str) -> PublicAlert:
        old = ALERTS.get(alert_id)
        new = ALERTS.get(new_alert_id)
        if old is None or new is None:
            raise HTTPException(status_code=404, detail="Alert not found")
        old.status = "superseded"
        return old

    def deliver(self, alert_id: str) -> list[dict[str, Any]]:
        alert = ALERTS[alert_id]
        if alert.status != "published":
            raise HTTPException(status_code=409, detail="Alert must be published before delivery")

        tenant = get_current_tenant()
        if tenant and tenant.is_simulation:
            logger.info(
                "alert_delivery_blocked_simulation tenant_id=%s alert_id=%s",
                tenant.tenant_id, alert_id,
            )
            return [{"channel": "simulation", "status": "published (simulation)", "alert_id": alert_id}]

        results = []
        for channel in alert.channel_set:
            adapter = CHANNEL_ADAPTERS.get(channel)
            if adapter:
                results.append(adapter(alert))
        return results
