"""AIIMS approval workflow — escalation chain, timeout, commander interaction.

All alerts enter ``pending_review``. Commander approves/rejects/modifies via
POST endpoints. Auto-escalation at 15 minutes (configurable). Max 3 levels.
NEVER auto-approve per CHK019.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime

from communication.config import CommunicationConfig
from communication.models import (
    AlertStatus,
    ApprovalMode,
    CommunicationDecisionRecord,
    CommunicationDecisionType,
    EscalationEvent,
    PublicAlert,
    VALID_STATUS_TRANSITIONS,
)

logger = logging.getLogger(__name__)


class ApprovalConflictError(Exception):
    """Raised when concurrent approval conflicts occur."""


class ApprovalWorkflow:
    """AIIMS-aligned approval workflow with escalation chain."""

    def __init__(
        self,
        config: CommunicationConfig | None = None,
        cosmos_client: object | None = None,
        service_bus_client: object | None = None,
    ) -> None:
        self._config = config or CommunicationConfig()
        self._cosmos = cosmos_client
        self._service_bus = service_bus_client
        self._escalation_timers: dict[str, asyncio.Task] = {}
        self._pending_alerts: dict[str, PublicAlert] = {}

    async def request_approval(
        self,
        alert: PublicAlert,
        commander_chain: list[str] | None = None,
    ) -> None:
        """Publish approval request to Service Bus commander-approval-queue.

        Includes full alert preview with all language variants, audience segments,
        delivery channels, and traceability per FR-020.
        """
        self._pending_alerts[alert.alert_id] = alert

        approval_payload = {
            "alert_id": alert.alert_id,
            "incident_id": alert.incident_id,
            "version": alert.version,
            "content_blocks": {
                lang: {
                    "title": block.title,
                    "body": block.body,
                    "action_items": block.action_items,
                    "language_code": block.language_code,
                }
                for lang, block in alert.content_blocks.items()
            },
            "audience_segments": alert.audience_segments,
            "channel_set": [ch.value for ch in alert.channel_set],
            "recommendation_id": alert.recommendation_id,
            "assessment_id": alert.assessment_id,
            "confidence": alert.confidence,
            "change_type": alert.change_type.value,
            "change_summary": alert.change_summary,
        }

        # Publish to Service Bus (in production)
        if self._service_bus is not None:
            try:
                self._service_bus.send_message(approval_payload)
            except Exception as exc:
                logger.error("Failed to publish approval request: %s", exc)

        logger.info(
            "Approval requested for alert %s (v%d)",
            alert.alert_id, alert.version,
        )

    async def start_escalation_timer(
        self,
        alert_id: str,
        timeout_minutes: int | None = None,
    ) -> None:
        """Start escalation timer for an alert."""
        timeout = timeout_minutes or self._config.approval_escalation_timeout_minutes

        async def _escalation_callback() -> None:
            await asyncio.sleep(timeout * 60)
            alert = self._pending_alerts.get(alert_id)
            if alert and alert.status == AlertStatus.pending_review:
                await self.escalate(alert_id, alert.escalation_level)

        task = asyncio.create_task(_escalation_callback())
        self._escalation_timers[alert_id] = task

    async def escalate(self, alert_id: str, current_level: int) -> None:
        """Escalate to next commander if within max levels per CHK019."""
        alert = self._pending_alerts.get(alert_id)
        if not alert:
            return

        max_levels = self._config.max_escalation_levels
        new_level = current_level + 1

        if new_level > max_levels:
            # Max levels reached — hold with CRITICAL flag per CHK019
            # NEVER auto-approve
            event = EscalationEvent(
                level=max_levels,
                from_commander_id=f"commander-level-{current_level}",
                to_commander_id=None,
                elapsed_minutes=float(
                    self._config.approval_escalation_timeout_minutes * current_level
                ),
                held_for_next_available=True,
            )
            alert.escalation_history.append(event)
            alert.escalation_level = max_levels
            logger.critical(
                "Escalation exhausted for %s at level %d — holding with CRITICAL flag. "
                "NEVER auto-approve per CHK019.",
                alert_id, max_levels,
            )
            return

        event = EscalationEvent(
            level=new_level,
            from_commander_id=f"commander-level-{current_level}",
            to_commander_id=f"commander-level-{new_level}",
            elapsed_minutes=float(self._config.approval_escalation_timeout_minutes),
        )
        alert.escalation_history.append(event)
        alert.escalation_level = new_level

        logger.info(
            "Escalated alert %s to level %d", alert_id, new_level,
        )

        # Re-publish approval request for next commander
        await self.request_approval(alert)
        await self.start_escalation_timer(alert_id)

    def process_approval(
        self,
        alert_id: str,
        user_id: str,
        role: str,
        action: str,
        justification: str | None = None,
        etag: str | None = None,
    ) -> PublicAlert:
        """Execute approve/reject with optimistic concurrency per R-014.

        First write wins, second gets 409.
        """
        alert = self._pending_alerts.get(alert_id)
        if alert is None:
            raise ValueError(f"Alert {alert_id} not found")

        if alert.status != AlertStatus.pending_review:
            raise ApprovalConflictError(
                f"Alert {alert_id} is not in pending_review status (current: {alert.status.value})"
            )

        now = datetime.now(UTC)

        if action == "approve":
            alert.status = AlertStatus.approved
            alert.approval_mode = ApprovalMode.human_approved
            alert.approved_by_user_id = user_id
            alert.approved_by_role = role
            alert.approval_action = "approve"
            alert.approved_at = now
            alert.updated_at = now
        elif action == "reject":
            if not justification:
                raise ValueError("Justification is required for rejection")
            alert.status = AlertStatus.rejected
            alert.approved_by_user_id = user_id
            alert.approved_by_role = role
            alert.approval_action = "reject"
            alert.approval_justification = justification
            alert.updated_at = now
        else:
            raise ValueError(f"Invalid approval action: {action}")

        # Cancel escalation timer
        timer = self._escalation_timers.pop(alert_id, None)
        if timer and not timer.done():
            timer.cancel()

        # Persist to Cosmos (in production)
        if self._cosmos is not None:
            try:
                doc = alert.model_dump(mode="json")
                doc["id"] = alert.alert_id
                if etag:
                    self._cosmos.replace_item(
                        item=alert.alert_id, body=doc, if_match=etag
                    )
                else:
                    self._cosmos.upsert_item(body=doc)
            except Exception as exc:
                if "412" in str(exc) or "PreconditionFailed" in str(exc):
                    raise ApprovalConflictError(
                        "Concurrent approval conflict — first write wins"
                    ) from exc
                raise

        return alert

    def create_modified_version(
        self,
        alert: PublicAlert,
        modifications: dict,
        user_id: str,
        role: str,
    ) -> PublicAlert:
        """Create a new alert version incorporating commander's changes."""
        new_version = alert.version + 1
        new_alert_id = f"ca-{alert.incident_id}-v{new_version}"

        # Start with the existing alert data
        new_data = alert.model_dump()
        new_data.update({
            "alert_id": new_alert_id,
            "version": new_version,
            "status": AlertStatus.pending_review,
            "change_type": "update",
            "change_summary": f"Modified by {user_id} ({role})",
            "approval_mode": None,
            "approved_by_user_id": None,
            "approved_by_role": None,
            "approval_action": None,
            "approval_justification": None,
            "approved_at": None,
            "escalation_level": 0,
            "escalation_history": [],
            "created_at": datetime.now(UTC),
            "updated_at": datetime.now(UTC),
        })

        # Apply modifications
        if "audience_segments" in modifications:
            new_data["audience_segments"] = modifications["audience_segments"]
        if "content_overrides" in modifications:
            for lang, content in modifications["content_overrides"].items():
                if lang in new_data.get("content_blocks", {}):
                    new_data["content_blocks"][lang].update(content)

        new_alert = PublicAlert.model_validate(new_data)
        self._pending_alerts[new_alert.alert_id] = new_alert
        return new_alert

    def cancel_alert(
        self,
        alert_id: str,
        user_id: str,
        role: str,
        reason: str,
    ) -> PublicAlert:
        """Transition alert to cancelled from pre-delivery states only."""
        alert = self._pending_alerts.get(alert_id)
        if alert is None:
            raise ValueError(f"Alert {alert_id} not found")

        cancellable = {AlertStatus.drafting, AlertStatus.pending_review, AlertStatus.approved}
        if alert.status not in cancellable:
            raise ApprovalConflictError(
                f"Cannot cancel alert in {alert.status.value} status"
            )

        alert.status = AlertStatus.cancelled
        alert.updated_at = datetime.now(UTC)
        alert.approval_justification = f"Cancelled by {user_id}: {reason}"

        # Cancel escalation timer
        timer = self._escalation_timers.pop(alert_id, None)
        if timer and not timer.done():
            timer.cancel()

        return alert

    def get_pending_count(self) -> int:
        """Return count of alerts in pending_review status."""
        return sum(
            1 for a in self._pending_alerts.values()
            if a.status == AlertStatus.pending_review
        )
