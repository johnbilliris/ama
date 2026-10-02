"""AIIMS approval workflow — escalation chain, timeout, commander interaction.

All alerts enter ``pending_review``. Commander approves/rejects/modifies via
POST endpoints. Auto-escalation at 15 minutes (configurable). Max 3 levels.
NEVER auto-approve per CHK019.
"""

from __future__ import annotations

import asyncio
import inspect
import json
import logging
import os
import time
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid5

from common.async_bridge import run_async
from communication.audit import AuditWriter
from communication.config import CommunicationConfig
from communication.models import (
    AlertStatus,
    ApprovalMode,
    CommunicationDecisionRecord,
    CommunicationDecisionType,
    EscalationEvent,
    PublicAlert,
)
from communication.repository import CommunicationAlertRepository
from communication.telemetry import CustomEventEmitter, metrics
from communication.versioning import VersionCounter

logger = logging.getLogger(__name__)

_APPROVAL_NAMESPACE = UUID("c6cf3a6a-8a68-4c18-9e7f-2d03c0f0c2b5")


class ApprovalConflictError(Exception):
    """Raised when concurrent approval conflicts occur."""


class ApprovalNotificationError(RuntimeError):
    """Raised when a durable approval request cannot be published."""


class ServiceBusApprovalPublisher:
    """Publish approval envelopes to Service Bus using managed identity."""

    def __init__(self, namespace: str, queue_name: str, client: Any | None = None) -> None:
        self._namespace = namespace
        self._queue_name = queue_name
        self._client = client

    async def publish(self, payload: dict[str, Any]) -> None:
        if not self._namespace:
            raise ApprovalNotificationError("Service Bus namespace is not configured")
        await asyncio.to_thread(self._publish_sync, payload)

    def _publish_sync(self, payload: dict[str, Any]) -> None:
        client = self._client
        if client is None:
            from azure.identity import DefaultAzureCredential
            from azure.servicebus import ServiceBusClient

            client_id = os.environ.get("AZURE_CLIENT_ID")
            credential = (
                DefaultAzureCredential(managed_identity_client_id=client_id) if client_id else DefaultAzureCredential()
            )
            client = ServiceBusClient(fully_qualified_namespace=self._namespace, credential=credential)
            self._client = client

        from azure.servicebus import ServiceBusMessage

        with client.get_queue_sender(queue_name=self._queue_name) as sender:
            sender.send_messages(ServiceBusMessage(json.dumps(payload)))


class ApprovalWorkflow:
    """AIIMS-aligned approval workflow with escalation chain."""

    def __init__(
        self,
        config: CommunicationConfig | None = None,
        cosmos_client: object | None = None,
        service_bus_client: object | None = None,
        alert_repository: CommunicationAlertRepository | None = None,
        version_counter: VersionCounter | None = None,
        audit_writer: AuditWriter | None = None,
    ) -> None:
        self._config = config or CommunicationConfig()
        self._cosmos = cosmos_client
        self._service_bus = service_bus_client
        self._alert_repository = alert_repository
        self._version_counter = version_counter or VersionCounter(config=self._config)
        self._audit_writer = audit_writer
        self._escalation_timers: dict[tuple[str, str], asyncio.Task] = {}
        self._pending_alerts: dict[str, PublicAlert] = {}

    def get_alert(self, tenant_id: str, alert_id: str) -> PublicAlert | None:
        if self._alert_repository is not None:
            return self._alert_repository.get(tenant_id, alert_id)
        alert = self._pending_alerts.get(alert_id)
        return alert if alert is not None and alert.tenant_id == tenant_id else None

    def get_segments(self, tenant_id: str, alert_id: str):
        if self._alert_repository is None:
            return []
        return self._alert_repository.audience_segments(tenant_id, alert_id)

    def get_delivery_records(self, tenant_id: str, alert_id: str):
        if self._alert_repository is None:
            return []
        return self._alert_repository.delivery_records(tenant_id, alert_id)

    def get_version_history(self, tenant_id: str, incident_id: str):
        if self._alert_repository is None:
            return []
        return self._alert_repository.version_history(tenant_id, incident_id)

    def expire_due_alerts(self) -> list[str]:
        if self._alert_repository is None:
            return []
        return self._alert_repository.expire_due()

    async def request_approval(
        self,
        alert: PublicAlert,
        commander_chain: list[str] | None = None,
    ) -> None:
        """Publish approval request to Service Bus commander-approval-queue.

        Includes full alert preview with all language variants, audience segments,
        delivery channels, and traceability per FR-020.
        """
        if self._alert_repository is None:
            raise ApprovalNotificationError("Alert aggregate repository is not configured")
        self._pending_alerts[alert.alert_id] = alert

        if commander_chain is not None:
            alert.commander_chain = list(dict.fromkeys(commander for commander in commander_chain if commander))
            alert.escalation_level = 0
        if not alert.commander_chain:
            raise ApprovalNotificationError("Incident commander chain is unavailable")
        if alert.escalation_level >= len(alert.commander_chain):
            raise ApprovalNotificationError("Incident commander chain is exhausted")
        alert.current_commander_id = alert.commander_chain[alert.escalation_level]
        alert.approval_deadline_at = None
        alert = self._alert_repository.replace(alert)

        segments = self._alert_repository.audience_segments(alert.tenant_id, alert.alert_id)
        request_id = str(
            uuid5(
                _APPROVAL_NAMESPACE,
                f"{alert.tenant_id}|{alert.alert_id}|{alert.version}|{alert.escalation_level}",
            )
        )
        deadline = datetime.now(UTC) + timedelta(minutes=self._timeout_minutes(alert))

        approval_payload = {
            "request_id": request_id,
            "tenant_id": alert.tenant_id,
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
            "audience_segments": [segment.model_dump(mode="json") for segment in segments],
            "channel_set": [ch.value for ch in alert.channel_set],
            "recommendation_id": alert.recommendation_id,
            "assessment_id": alert.assessment_id,
            "confidence": alert.confidence,
            "change_type": alert.change_type.value,
            "change_summary": alert.change_summary,
            "content_safety_result": alert.content_safety_result.value,
            "content_safety_details": {
                language: detail.model_dump(mode="json") for language, detail in alert.content_safety_details.items()
            },
            "assigned_commander_id": alert.current_commander_id,
            "escalation_level": alert.escalation_level,
            "approval_deadline_at": deadline.isoformat(),
            "status": "pending",
            "created_at": datetime.now(UTC).isoformat(),
        }

        self._alert_repository.save_approval_request(alert.tenant_id, alert.alert_id, approval_payload)

        publish_started = time.perf_counter()
        if self._service_bus is None:
            approval_payload["status"] = "failed"
            approval_payload["failure_reason"] = "Approval publisher is not configured"
            self._alert_repository.save_approval_request(alert.tenant_id, alert.alert_id, approval_payload)
            raise ApprovalNotificationError("Approval publisher is not configured")
        try:
            await self._publish(approval_payload)
        except Exception as exc:
            approval_payload["status"] = "failed"
            approval_payload["failure_reason"] = str(exc)
            self._alert_repository.save_approval_request(alert.tenant_id, alert.alert_id, approval_payload)
            raise ApprovalNotificationError("Failed to publish approval request") from exc

        approval_payload["status"] = "sent"
        approval_payload["sent_at"] = datetime.now(UTC).isoformat()
        persisted = self._alert_repository.require(alert.tenant_id, alert.alert_id)
        persisted.approval_deadline_at = deadline
        persisted = self._alert_repository.replace(persisted)
        self._pending_alerts[persisted.alert_id] = persisted
        self._alert_repository.save_approval_request(alert.tenant_id, alert.alert_id, approval_payload)
        metrics.approval_notification_latency.record(
            (time.perf_counter() - publish_started) * 1000,
            {"tenant_id": alert.tenant_id, "alert_id": alert.alert_id},
        )
        CustomEventEmitter.approval_requested(
            alert.alert_id,
            tenant_id=alert.tenant_id,
            commander_id=alert.current_commander_id,
        )
        await self.start_escalation_timer(alert.alert_id, tenant_id=alert.tenant_id)

        logger.info(
            "Approval requested for alert %s (v%d)",
            alert.alert_id,
            alert.version,
        )

    async def retry_pending_notifications(self) -> int:
        if self._alert_repository is None or self._service_bus is None:
            return 0
        sent = 0
        for request in self._alert_repository.pending_approval_requests():
            request["attempt_count"] = int(request.get("attempt_count", 0)) + 1
            request["last_attempt_at"] = datetime.now(UTC).isoformat()
            try:
                await self._publish(request)
            except Exception as exc:
                request["status"] = "failed"
                request["failure_reason"] = str(exc)
            else:
                request["status"] = "sent"
                request["sent_at"] = datetime.now(UTC).isoformat()
                request.pop("failure_reason", None)
                alert = self._alert_repository.require(str(request["tenant_id"]), str(request["alert_id"]))
                deadline = datetime.now(UTC) + timedelta(minutes=self._timeout_minutes(alert))
                alert.approval_deadline_at = deadline
                self._alert_repository.replace(alert)
                request["approval_deadline_at"] = deadline.isoformat()
                sent += 1
            self._alert_repository.save_approval_request(
                str(request["tenant_id"]),
                str(request["alert_id"]),
                request,
            )
        return sent

    async def recover_escalation_deadlines(self) -> int:
        if self._alert_repository is None:
            return 0
        recovered = 0
        for alert in self._alert_repository.pending_escalations():
            await self.start_escalation_timer(alert.alert_id, tenant_id=alert.tenant_id)
            recovered += 1
        return recovered

    async def _publish(self, payload: dict[str, Any]) -> None:
        publish = getattr(self._service_bus, "publish", None) or getattr(self._service_bus, "send_message")
        result = publish(payload)
        if inspect.isawaitable(result):
            await result

    async def start_escalation_timer(
        self,
        alert_id: str,
        tenant_id: str = "live",
        timeout_minutes: int | None = None,
    ) -> None:
        """Start escalation timer for an alert."""
        alert = self.get_alert(tenant_id, alert_id)
        if alert is None or alert.status != AlertStatus.pending_review:
            return
        deadline = alert.approval_deadline_at
        if deadline is None:
            timeout = timeout_minutes if timeout_minutes is not None else self._timeout_minutes(alert)
            deadline = datetime.now(UTC) + timedelta(minutes=timeout)
            alert.approval_deadline_at = deadline
            if self._alert_repository is not None:
                alert = self._alert_repository.replace(alert)

        async def _escalation_callback() -> None:
            delay_seconds = max(0.0, (deadline - datetime.now(UTC)).total_seconds())
            await asyncio.sleep(delay_seconds)
            current = self.get_alert(tenant_id, alert_id)
            if current and current.status == AlertStatus.pending_review:
                await self.escalate(alert_id, tenant_id=tenant_id)

        task = asyncio.create_task(_escalation_callback())
        existing = self._escalation_timers.pop((tenant_id, alert_id), None)
        if existing and not existing.done():
            existing.cancel()
        self._escalation_timers[(tenant_id, alert_id)] = task

    async def escalate(self, alert_id: str, current_level: int | None = None, tenant_id: str = "live") -> None:
        """Escalate to next commander if within max levels per CHK019."""
        alert = self.get_alert(tenant_id, alert_id)
        if not alert:
            return

        current_index = alert.escalation_level if current_level is None else current_level
        max_index = min(self._config.max_escalation_levels - 1, len(alert.commander_chain) - 1)
        new_level = current_index + 1

        if new_level > max_index:
            event = EscalationEvent(
                level=max(1, min(3, current_index + 1)),
                from_commander_id=alert.current_commander_id or alert.commander_chain[current_index],
                to_commander_id=None,
                elapsed_minutes=float(self._timeout_minutes(alert)),
                held_for_next_available=True,
            )
            alert.escalation_history.append(event)
            alert.escalation_exhausted = True
            alert.approval_deadline_at = None
            if self._alert_repository is not None:
                alert = self._alert_repository.replace(alert)
            self._write_escalation_audit(alert, event, "Commander chain exhausted; awaiting human authority")
            CustomEventEmitter.escalation_exhausted(
                alert.alert_id,
                tenant_id=alert.tenant_id,
                held_for_next_available=True,
            )
            logger.critical(
                "Escalation exhausted for %s at level %d; awaiting human authority",
                alert_id,
                current_index,
            )
            return

        event = EscalationEvent(
            level=new_level,
            from_commander_id=alert.current_commander_id or alert.commander_chain[current_index],
            to_commander_id=alert.commander_chain[new_level],
            elapsed_minutes=float(self._timeout_minutes(alert)),
        )
        alert.escalation_history.append(event)
        alert.escalation_level = new_level
        alert.current_commander_id = alert.commander_chain[new_level]
        alert.approval_deadline_at = None
        if self._alert_repository is not None:
            alert = self._alert_repository.replace(alert)
        self._write_escalation_audit(alert, event, f"Escalated to {event.to_commander_id}")
        metrics.escalation_count.add(1, {"tenant_id": alert.tenant_id})
        CustomEventEmitter.escalation_triggered(
            alert.alert_id,
            new_level,
            tenant_id=alert.tenant_id,
            from_commander=event.from_commander_id,
            to_commander=event.to_commander_id,
        )

        logger.info(
            "Escalated alert %s to level %d",
            alert_id,
            new_level,
        )

        # Re-publish approval request for next commander
        await self.request_approval(alert)

    def _timeout_minutes(self, alert: PublicAlert) -> int:
        warning_tier = "".join(character for character in (alert.warning_tier or "").casefold() if character.isalnum())
        if warning_tier == "emergencywarning":
            return self._config.emergency_warning_timeout_minutes
        return self._config.approval_escalation_timeout_minutes

    def _write_escalation_audit(
        self,
        alert: PublicAlert,
        event: EscalationEvent,
        summary: str,
    ) -> None:
        if self._audit_writer is None:
            return
        self._audit_writer.write(
            CommunicationDecisionRecord(
                tenant_id=alert.tenant_id,
                correlation_id=alert.alert_id,
                alert_id=alert.alert_id,
                decision_type=CommunicationDecisionType.escalation_triggered,
                output_summary=summary,
                escalation_details=event.model_dump(mode="json"),
                agent_version=self._config.agent_version,
                config_version=self._config.compute_config_hash(),
            )
        )

    def process_approval(
        self,
        alert_id: str,
        user_id: str,
        role: str,
        action: str,
        justification: str | None = None,
        etag: str | None = None,
        tenant_id: str = "live",
    ) -> PublicAlert:
        """Execute approve/reject with optimistic concurrency per R-014.

        First write wins, second gets 409.
        """
        alert = self.get_alert(tenant_id, alert_id)
        if alert is None:
            raise ValueError(f"Alert {alert_id} not found")

        if alert.status != AlertStatus.pending_review:
            raise ApprovalConflictError(
                f"Alert {alert_id} is not in pending_review status (current: {alert.status.value})"
            )

        now = datetime.now(UTC)
        metrics.approval_wait_time.record(
            max(0.0, (now - alert.created_at).total_seconds() * 1000),
            {"tenant_id": alert.tenant_id, "alert_id": alert.alert_id, "action": action},
        )
        metrics.pending_approvals.add(-1, {"tenant_id": alert.tenant_id})

        if action == "approve":
            alert.status = AlertStatus.approved
            alert.approval_mode = ApprovalMode.human_approved
            alert.approved_by_user_id = user_id
            alert.approved_by_role = role
            alert.approval_action = "approve"
            alert.approved_at = now
            alert.decision_at = now
            alert.updated_at = now
        elif action == "reject":
            if not justification:
                raise ValueError("Justification is required for rejection")
            alert.status = AlertStatus.rejected
            alert.approved_by_user_id = user_id
            alert.approved_by_role = role
            alert.approval_action = "reject"
            alert.approval_justification = justification
            alert.decision_at = now
            alert.updated_at = now
        else:
            raise ValueError(f"Invalid approval action: {action}")

        # Cancel escalation timer
        timer = self._escalation_timers.pop((tenant_id, alert_id), None)
        if timer and not timer.done():
            timer.cancel()

        if self._alert_repository is not None:
            try:
                alert = self._alert_repository.replace(alert, expected_etag=etag)
            except Exception as exc:
                if "412" in str(exc) or "PreconditionFailed" in str(exc):
                    raise ApprovalConflictError("Concurrent approval conflict — first write wins") from exc
                raise
        elif self._cosmos is not None:
            try:
                doc = alert.model_dump(mode="json")
                doc["id"] = alert.alert_id
                if etag:
                    self._cosmos.replace_item(item=alert.alert_id, body=doc, if_match=etag)
                else:
                    self._cosmos.upsert_item(body=doc)
            except Exception as exc:
                if "412" in str(exc) or "PreconditionFailed" in str(exc):
                    raise ApprovalConflictError("Concurrent approval conflict — first write wins") from exc
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
        allowed_fields = {"audience_segments", "content_overrides"}
        unknown_fields = set(modifications) - allowed_fields
        if unknown_fields:
            raise ValueError(f"Unsupported modification fields: {', '.join(sorted(unknown_fields))}")

        modification_fingerprint = json.dumps(modifications, sort_keys=True, separators=(",", ":"))
        new_version = run_async(
            self._version_counter.assign_version(
                alert.incident_id,
                alert.tenant_id,
                reservation_key=f"modify:{alert.alert_id}:{user_id}:{modification_fingerprint}",
            )
        )
        if new_version <= alert.version:
            raise ApprovalConflictError("Allocated version does not advance the existing alert")
        new_alert_id = f"ca-{alert.incident_id}-v{new_version}"

        # Start with the existing alert data
        new_data = alert.model_dump()
        new_data.update(
            {
                "alert_id": new_alert_id,
                "version": new_version,
                "status": AlertStatus.pending_review,
                "change_type": "update",
                "change_summary": f"Modified by {user_id} ({role})",
                "referenced_alert_id": alert.alert_id,
                "approval_mode": None,
                "approved_by_user_id": None,
                "approved_by_role": None,
                "approval_action": None,
                "approval_justification": None,
                "approved_at": None,
                "decision_at": None,
                "current_commander_id": None,
                "approval_deadline_at": None,
                "escalation_exhausted": False,
                "escalation_level": 0,
                "escalation_history": [],
                "created_at": datetime.now(UTC),
                "updated_at": datetime.now(UTC),
            }
        )

        if "audience_segments" in modifications:
            audience_segments = modifications["audience_segments"]
            if not isinstance(audience_segments, list) or not all(
                isinstance(segment_id, str) and segment_id.strip() for segment_id in audience_segments
            ):
                raise ValueError("audience_segments must contain non-empty IDs")
            new_data["audience_segments"] = list(dict.fromkeys(audience_segments))
        if "content_overrides" in modifications:
            content_overrides = modifications["content_overrides"]
            if not isinstance(content_overrides, dict):
                raise ValueError("content_overrides must be an object")
            for lang, content in content_overrides.items():
                if lang in new_data.get("content_blocks", {}):
                    if not isinstance(content, dict):
                        raise ValueError(f"content_overrides.{lang} must be an object")
                    unknown_content = set(content) - {"title", "body", "action_items"}
                    if unknown_content:
                        raise ValueError(f"Unsupported content fields for {lang}: {', '.join(sorted(unknown_content))}")
                    new_data["content_blocks"][lang].update(content)
                else:
                    raise ValueError(f"Cannot override missing language {lang}")

        new_alert = PublicAlert.model_validate(new_data)
        if self._alert_repository is not None:
            segments = self._alert_repository.audience_segments(alert.tenant_id, alert.alert_id)
            new_alert = self._alert_repository.create(new_alert, segments)
        self._pending_alerts[new_alert.alert_id] = new_alert
        return new_alert

    def cancel_alert(
        self,
        alert_id: str,
        user_id: str,
        role: str,
        reason: str,
        tenant_id: str = "live",
    ) -> PublicAlert:
        """Transition alert to cancelled from pre-delivery states only."""
        alert = self.get_alert(tenant_id, alert_id)
        if alert is None:
            raise ValueError(f"Alert {alert_id} not found")

        cancellable = {AlertStatus.drafting, AlertStatus.pending_review, AlertStatus.approved}
        if alert.status not in cancellable:
            raise ApprovalConflictError(f"Cannot cancel alert in {alert.status.value} status")

        alert.status = AlertStatus.cancelled
        alert.updated_at = datetime.now(UTC)
        alert.approved_by_user_id = user_id
        alert.approved_by_role = role
        alert.approval_action = "cancel"
        alert.approval_justification = reason
        alert.decision_at = alert.updated_at

        # Cancel escalation timer
        timer = self._escalation_timers.pop((tenant_id, alert_id), None)
        if timer and not timer.done():
            timer.cancel()

        if self._alert_repository is not None:
            alert = self._alert_repository.replace(alert)

        return alert

    def get_pending_count(self) -> int:
        """Return count of alerts in pending_review status."""
        return sum(1 for a in self._pending_alerts.values() if a.status == AlertStatus.pending_review)
