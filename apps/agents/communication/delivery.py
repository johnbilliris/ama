"""Multi-channel delivery — SMS, push, emergency broadcast with retry.

Per-channel independent retry (3×, exponential backoff 1s/2s/4s).
Vulnerable/critical segments delivered first per FR-024.
Overlapping segment deduplication at delivery time per CHK041.
Simulation tenant alerts MUST NOT trigger real public delivery per FR-040.
"""

from __future__ import annotations

import asyncio
import inspect
import json
import logging
import math
import re
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Protocol
from uuid import UUID, uuid5

from communication.config import CommunicationConfig
from communication.models import (
    AlertStatus,
    ApprovalMode,
    AudienceSegment,
    ChannelType,
    ContentBlock,
    DeliveryRecord,
    DeliveryStatus,
    PublicAlert,
    SegmentPriority,
)
from communication.telemetry import CustomEventEmitter, metrics

from packages.domain.src.domain.tenant_mode import is_live_tenant

logger = logging.getLogger(__name__)

ApprovalResolver = Callable[[str, str, int], PublicAlert | None | Awaitable[PublicAlert | None]]


class SmsDeliveryClient(Protocol):
    def send(
        self,
        *,
        from_: str,
        to: list[str],
        message: str,
        enable_delivery_report: bool,
        tag: str,
    ) -> object | Awaitable[object]: ...


class PushDeliveryClient(Protocol):
    def send_notification(
        self,
        payload: dict[str, object],
        *,
        target: str | list[str],
    ) -> object | Awaitable[object]: ...


class BroadcastDeliveryClient(Protocol):
    def post(
        self,
        url: str,
        *,
        json: dict[str, object],
        headers: dict[str, str],
        timeout: float,
    ) -> object | Awaitable[object]: ...


_DELIVERY_NAMESPACE = UUID("23803077-a011-41be-8f74-c39104c9eec8")
_GSM7_BASIC = frozenset(
    "@£$¥èéùìòÇ\nØø\rÅåΔ_ΦΓΛΩΠΨΣΘΞÆæßÉ !\"#¤%&'()*+,-./0123456789:;<=>?"
    "¡ABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÑÜ§¿abcdefghijklmnopqrstuvwxyzäöñüà"
)
_GSM7_EXTENDED = frozenset("^{}\\[~]|€")


class ApprovalRequiredError(RuntimeError):
    """Raised before provider access when durable human approval is absent."""


class NotificationHubRestClient:
    """Minimal targeted Notification Hubs data-plane adapter."""

    def __init__(self, endpoint: str, authorization: str, timeout_seconds: float = 10.0) -> None:
        self._endpoint = endpoint
        self._authorization = authorization
        self._timeout_seconds = timeout_seconds

    async def send_notification(self, payload: dict[str, Any], *, target: str | list[str]) -> object:
        import httpx

        tags = [target] if isinstance(target, str) else target
        headers = {
            "Authorization": self._authorization,
            "Content-Type": "application/json;charset=utf-8",
            "ServiceBusNotification-Format": "template",
            "ServiceBusNotification-Tags": " || ".join(tags),
        }
        async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
            return await client.post(self._endpoint, json=payload, headers=headers)


@dataclass(frozen=True)
class _ProviderOutcome:
    status: DeliveryStatus
    receipt_ids: tuple[str, ...] = ()
    provider_status: str | None = None
    failure_reason: str | None = None


@dataclass(frozen=True)
class _DeliveryTarget:
    segment: AudienceSegment
    channel: ChannelType
    recipient_ids: tuple[str, ...]
    deduplicated_recipient_count: int = 0
    deduplicated_by_segment_id: str | None = None


# Priority ordering for delivery: critical first
_PRIORITY_ORDER = {
    SegmentPriority.critical: 0,
    SegmentPriority.high: 1,
    SegmentPriority.moderate: 2,
}


class MultiChannelDeliveryService:
    """Orchestrates multi-channel alert delivery with retry and deduplication."""

    def __init__(
        self,
        config: CommunicationConfig | None = None,
        sms_client: SmsDeliveryClient | None = None,
        push_client: PushDeliveryClient | None = None,
        broadcast_client: BroadcastDeliveryClient | None = None,
        approval_resolver: ApprovalResolver | None = None,
    ) -> None:
        self._config = config or CommunicationConfig()
        self._sms_client = sms_client
        self._push_client = push_client
        self._broadcast_client = broadcast_client
        self._approval_resolver = approval_resolver
        self._channel_health: dict[str, bool] = {
            "sms": True,
            "push": True,
            "emergency_broadcast": True,
        }

    async def deliver_alert(
        self,
        alert: PublicAlert,
        segments: list[AudienceSegment],
    ) -> list[DeliveryRecord]:
        """Orchestrate delivery across configured channels.

        Returns list of DeliveryRecord for all channel × segment combinations.
        """
        alert = await self._require_persisted_approval(alert)

        # Delivery is live-only. Every non-live or unknown mode receives synthetic receipts.
        if alert.mode != "live" or not is_live_tenant(alert.tenant_id):
            logger.info(
                "Non-live alert %s (tenant=%s mode=%s) — skipping real delivery per FR-040",
                alert.alert_id,
                alert.tenant_id,
                alert.mode,
            )
            return self._create_simulation_records(alert, segments)

        # Sort delivery order: critical first per FR-024
        segments = self._sort_delivery_order(segments)
        targets = self._deduplicate_targets(segments)

        records: list[DeliveryRecord] = []
        concurrency = asyncio.Semaphore(self._config.delivery_max_concurrency)
        priority_groups: dict[int, list[_DeliveryTarget]] = {}
        for target in targets:
            priority = _PRIORITY_ORDER.get(target.segment.priority, 99)
            priority_groups.setdefault(priority, []).append(target)
        for priority in sorted(priority_groups):
            group_records = await asyncio.gather(
                *(self._deliver_target(alert, target, concurrency) for target in priority_groups[priority])
            )
            records.extend(record for record in group_records if record is not None)

        return records

    async def _deliver_target(
        self,
        alert: PublicAlert,
        target: _DeliveryTarget,
        concurrency: asyncio.Semaphore,
    ) -> DeliveryRecord | None:
        segment = target.segment
        language_used = segment.preferred_language
        if target.channel == ChannelType.emergency_broadcast:
            content_block = alert.content_blocks.get("en-AU")
            language_used = "en-AU"
        else:
            content_block = alert.content_blocks.get(
                segment.preferred_language,
                alert.content_blocks.get("en-AU"),
            )
        if content_block is None:
            return None

        recipient_key = ",".join(sorted(target.recipient_ids))
        delivery_id = str(
            uuid5(
                _DELIVERY_NAMESPACE,
                (
                    f"{alert.tenant_id}|{alert.alert_id}|{alert.version}|{target.channel.value}|"
                    f"{segment.segment_id}|{recipient_key}"
                ),
            )
        )
        record = DeliveryRecord(
            delivery_id=delivery_id,
            alert_id=alert.alert_id,
            alert_version=alert.version,
            channel=target.channel,
            audience_segment_id=segment.segment_id,
            language_used=language_used,
            content_payload=self._format_content(content_block, target.channel),
            tenant_id=alert.tenant_id,
            max_retries=self._config.delivery_max_retries,
            targeted_recipient_count=len(target.recipient_ids),
            deduplicated_recipient_count=target.deduplicated_recipient_count,
            is_deduplicated=target.deduplicated_recipient_count > 0,
            deduplicated_by_segment_id=target.deduplicated_by_segment_id,
        )

        if not target.recipient_ids:
            record.delivery_status = DeliveryStatus.skipped
            record.completed_at = datetime.now(UTC)
            return record
        async with concurrency:
            return await self._deliver_with_retry(record, target.channel, target.recipient_ids)

    async def _require_persisted_approval(self, requested: PublicAlert) -> PublicAlert:
        if self._approval_resolver is None:
            raise ApprovalRequiredError("Durable approval storage is not configured")
        resolved = self._approval_resolver(requested.tenant_id, requested.alert_id, requested.version)
        persisted = await resolved if inspect.isawaitable(resolved) else resolved
        if (
            persisted is None
            or persisted.tenant_id != requested.tenant_id
            or persisted.alert_id != requested.alert_id
            or persisted.version != requested.version
            or persisted.status != AlertStatus.approved
            or persisted.approval_mode != ApprovalMode.human_approved
            or not persisted.approved_by_user_id
            or not persisted.approved_by_role
            or persisted.approved_at is None
        ):
            raise ApprovalRequiredError("Persisted human approval for this alert version is required")
        return persisted

    def _deduplicate_targets(
        self,
        segments: list[AudienceSegment],
    ) -> list[_DeliveryTarget]:
        """Remove only recipients already covered by a higher-priority segment."""
        seen_recipients: dict[tuple[ChannelType, str], str] = {}
        seen_geometry: dict[tuple[ChannelType, str, str], str] = {}
        targets: list[_DeliveryTarget] = []

        for segment in segments:
            for channel_value in segment.delivery_channels:
                channel = ChannelType(channel_value)
                recipients = tuple(dict.fromkeys(recipient for recipient in segment.recipient_ids if recipient))
                winners: list[str] = []

                if recipients:
                    remaining: list[str] = []
                    for recipient in recipients:
                        winner = seen_recipients.get((channel, recipient))
                        if winner is None:
                            seen_recipients[(channel, recipient)] = segment.segment_id
                            remaining.append(recipient)
                        else:
                            winners.append(winner)
                    target_recipients = tuple(remaining)
                    deduplicated_count = len(recipients) - len(target_recipients)
                else:
                    geometry_key = self._geometry_key(segment.zone_boundary)
                    fallback_target = segment.segment_id
                    winner = (
                        seen_geometry.get((channel, segment.preferred_language, geometry_key))
                        if geometry_key is not None
                        else None
                    )
                    if winner is None:
                        if geometry_key is not None:
                            seen_geometry[(channel, segment.preferred_language, geometry_key)] = segment.segment_id
                        target_recipients = (fallback_target,)
                        deduplicated_count = 0
                    else:
                        winners.append(winner)
                        target_recipients = ()
                        deduplicated_count = max(segment.estimated_segment_size, segment.population_estimate, 1)

                targets.append(
                    _DeliveryTarget(
                        segment=segment,
                        channel=channel,
                        recipient_ids=target_recipients,
                        deduplicated_recipient_count=deduplicated_count,
                        deduplicated_by_segment_id=winners[0] if winners else None,
                    )
                )

        return targets

    @staticmethod
    def _geometry_key(zone_boundary: dict[str, object]) -> str | None:
        if not zone_boundary:
            return None
        return json.dumps(zone_boundary, sort_keys=True, separators=(",", ":"))

    def _sort_delivery_order(self, segments: list[AudienceSegment]) -> list[AudienceSegment]:
        """Order critical first, then by zone_level ascending per FR-024."""
        return sorted(
            segments,
            key=lambda s: (
                _PRIORITY_ORDER.get(s.priority, 99),
                s.zone_level,
                s.segment_id,
            ),
        )

    async def _deliver_with_retry(
        self,
        record: DeliveryRecord,
        channel: ChannelType,
        recipient_ids: tuple[str, ...],
    ) -> DeliveryRecord:
        """Implement per-channel independent retry with exponential backoff."""
        record.initiated_at = datetime.now(UTC)
        dimensions = {
            "tenant_id": record.tenant_id,
            "segment_id": record.audience_segment_id,
            "language": record.language_used,
        }
        CustomEventEmitter.delivery_started(record.alert_id, channel.value, **dimensions)
        backoff = record.retry_backoff_intervals or [1.0, 2.0, 4.0]
        max_retries = self._config.delivery_max_retries

        for attempt in range(max_retries + 1):
            record.attempt_count = attempt + 1
            try:
                if channel == ChannelType.sms:
                    outcome = await self._deliver_sms(record, recipient_ids)
                elif channel == ChannelType.push:
                    outcome = await self._deliver_push(record, recipient_ids)
                else:
                    outcome = await self._deliver_broadcast(record, recipient_ids)

                record.provider_receipt_ids = list(outcome.receipt_ids)
                record.provider_status = outcome.provider_status
                record.failure_reason = outcome.failure_reason
                if outcome.status in (
                    DeliveryStatus.accepted,
                    DeliveryStatus.delivered,
                    DeliveryStatus.skipped,
                    DeliveryStatus.unconfigured,
                ):
                    record.delivery_status = outcome.status
                    if outcome.status == DeliveryStatus.unconfigured:
                        self._channel_health[channel.value] = False
                    record = self._complete_record(record)
                    metrics.delivery_latency_per_channel.record(
                        record.delivery_duration_ms or 0,
                        {**dimensions, "channel": channel.value},
                    )
                    if outcome.status in {DeliveryStatus.accepted, DeliveryStatus.delivered}:
                        metrics.delivery_success_rate.add(1, {**dimensions, "channel": channel.value})
                        CustomEventEmitter.delivery_completed(
                            record.alert_id,
                            channel.value,
                            delivery_id=record.delivery_id,
                            duration_ms=record.delivery_duration_ms or 0,
                            **dimensions,
                        )
                    return record

                raise RuntimeError(outcome.failure_reason or f"{channel.value} provider rejected delivery")

            except Exception as exc:
                logger.warning(
                    "Delivery attempt %d/%d failed for %s/%s: %s",
                    attempt + 1,
                    max_retries + 1,
                    channel.value,
                    record.audience_segment_id,
                    exc,
                )
                record.failure_reason = str(exc)

                if attempt < max_retries and attempt < len(backoff):
                    record.delivery_status = DeliveryStatus.retrying
                    await asyncio.sleep(backoff[attempt])

        # All retries exhausted
        record.delivery_status = DeliveryStatus.failed
        self._channel_health[channel.value] = False
        record = self._complete_record(record)
        metrics.delivery_failure_count.add(1, {**dimensions, "channel": channel.value})
        metrics.channel_degraded.add(1, {"tenant_id": record.tenant_id, "channel": channel.value})
        CustomEventEmitter.delivery_failed(
            record.alert_id,
            channel.value,
            record.failure_reason or "unknown",
            delivery_id=record.delivery_id,
            attempt_count=record.attempt_count,
            **dimensions,
        )
        return record

    async def _deliver_sms(self, record: DeliveryRecord, recipient_ids: tuple[str, ...]) -> _ProviderOutcome:
        """Deliver via Azure Communication Services SMS."""
        content = record.content_payload
        record.segment_count = self._sms_segment_count(content)
        metrics.sms_segment_count.record(
            record.segment_count,
            {"tenant_id": record.tenant_id, "alert_id": record.alert_id},
        )

        if self._sms_client is None or not self._config.sms_sender_identity:
            return _ProviderOutcome(
                DeliveryStatus.unconfigured,
                failure_reason="SMS client and sender identity must be configured",
            )

        result = await self._invoke_provider(
            self._sms_client.send,
            from_=self._config.sms_sender_identity,
            to=list(recipient_ids),
            message=content[: self._config.sms_max_length],
            enable_delivery_report=True,
            tag=record.delivery_id,
        )
        return self._normalise_sms_result(result)

    async def _deliver_push(self, record: DeliveryRecord, recipient_ids: tuple[str, ...]) -> _ProviderOutcome:
        """Deliver via Azure Notification Hubs."""
        if self._push_client is None:
            return _ProviderOutcome(DeliveryStatus.unconfigured, failure_reason="Push client is not configured")

        result = await self._invoke_provider(
            self._push_client.send_notification,
            {
                "title": record.content_payload.splitlines()[0][:100],
                "body": record.content_payload,
            },
            target=recipient_ids[0] if len(recipient_ids) == 1 else list(recipient_ids),
        )
        return self._normalise_provider_result(result, "push")

    async def _deliver_broadcast(self, record: DeliveryRecord, recipient_ids: tuple[str, ...]) -> _ProviderOutcome:
        """Deliver approved en-AU content via an authenticated EAS webhook."""
        eas_url = self._config.eas_endpoint_url
        auth_token = self._config.eas_auth_token
        if not eas_url or not auth_token:
            return _ProviderOutcome(
                DeliveryStatus.unconfigured,
                failure_reason="EAS endpoint URL and authentication token must be configured",
            )

        payload = {
            "alert_id": record.alert_id,
            "alert_version": record.alert_version,
            "audience_segment_id": record.audience_segment_id,
            "recipient_ids": list(recipient_ids),
            "language": "en-AU",
            "message": record.content_payload,
        }
        headers = {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
        if self._broadcast_client is not None:
            result = await self._invoke_provider(
                self._broadcast_client.post,
                eas_url,
                json=payload,
                headers=headers,
                timeout=self._config.eas_timeout_seconds,
            )
        else:
            import httpx

            async with httpx.AsyncClient() as client:
                result = await client.post(
                    eas_url,
                    json=payload,
                    headers=headers,
                    timeout=self._config.eas_timeout_seconds,
                )
        return self._normalise_http_result(result, "EAS")

    async def _invoke_provider(self, provider_call: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        if inspect.iscoroutinefunction(provider_call):
            return await provider_call(*args, **kwargs)
        result = await asyncio.to_thread(provider_call, *args, **kwargs)
        return await result if inspect.isawaitable(result) else result

    def _normalise_sms_result(self, result: Any) -> _ProviderOutcome:
        results = list(result) if isinstance(result, (list, tuple)) else []
        if not results:
            return _ProviderOutcome(DeliveryStatus.failed, failure_reason="SMS provider returned no receipt")

        receipt_ids = tuple(
            str(message_id) for item in results if (message_id := self._result_value(item, "message_id"))
        )
        rejected = [item for item in results if self._result_value(item, "successful") is not True]
        if rejected:
            errors = [
                str(
                    self._result_value(item, "error_message")
                    or self._result_value(item, "http_status_code")
                    or "rejected"
                )
                for item in rejected
            ]
            accepted_count = len(results) - len(rejected)
            return _ProviderOutcome(
                DeliveryStatus.failed,
                receipt_ids=receipt_ids,
                provider_status="partially_accepted" if accepted_count else "rejected",
                failure_reason=f"SMS accepted {accepted_count}/{len(results)} results; rejected: {', '.join(errors)}",
            )
        return _ProviderOutcome(
            DeliveryStatus.accepted,
            receipt_ids=receipt_ids,
            provider_status="accepted",
        )

    def _normalise_http_result(self, result: Any, provider: str) -> _ProviderOutcome:
        status_code = self._result_value(result, "status_code")
        if not isinstance(status_code, int):
            return self._normalise_provider_result(result, provider)

        body: Any = None
        try:
            body = result.json()
        except (TypeError, ValueError):
            body = None
        if isinstance(body, dict) and self._has_explicit_outcome(body):
            outcome = self._normalise_provider_result(body, provider)
            if outcome.status == DeliveryStatus.failed or 200 <= status_code < 300:
                return outcome
        if 200 <= status_code < 300:
            receipt_ids = self._receipt_ids(body)
            if not receipt_ids:
                location = self._header_value(result, "Location")
                receipt_ids = (location,) if location else ()
            return _ProviderOutcome(
                DeliveryStatus.accepted,
                receipt_ids=receipt_ids,
                provider_status=str(status_code),
            )
        return _ProviderOutcome(
            DeliveryStatus.failed,
            provider_status=str(status_code),
            failure_reason=f"{provider} provider returned HTTP {status_code}",
        )

    def _normalise_provider_result(self, result: Any, provider: str) -> _ProviderOutcome:
        if result is True:
            return _ProviderOutcome(DeliveryStatus.accepted, provider_status="accepted")
        if result is False:
            return _ProviderOutcome(
                DeliveryStatus.failed,
                provider_status="rejected",
                failure_reason=f"{provider} provider rejected delivery",
            )

        accepted = self._result_value(result, "accepted")
        if accepted is None:
            accepted = self._result_value(result, "successful")
        status = self._result_value(result, "status")
        normalised_status = str(status).lower() if status is not None else None
        receipt_ids = self._receipt_ids(result)

        if accepted is True or normalised_status in {"accepted", "queued", "submitted", "success", "succeeded"}:
            return _ProviderOutcome(DeliveryStatus.accepted, receipt_ids, normalised_status or "accepted")
        if normalised_status in {"confirmed", "delivered"}:
            return _ProviderOutcome(DeliveryStatus.delivered, receipt_ids, normalised_status)

        reason = self._result_value(result, "error_message") or self._result_value(result, "reason")
        return _ProviderOutcome(
            DeliveryStatus.failed,
            receipt_ids,
            normalised_status or "rejected",
            str(reason or f"{provider} provider rejected delivery without an acceptance receipt"),
        )

    @staticmethod
    def _result_value(result: Any, name: str) -> Any:
        return result.get(name) if isinstance(result, dict) else getattr(result, name, None)

    def _receipt_ids(self, result: Any) -> tuple[str, ...]:
        if result is None:
            return ()
        for name in ("receipt_ids", "receipt_id", "message_id", "notification_id", "tracking_id", "id"):
            value = self._result_value(result, name)
            if isinstance(value, (list, tuple)):
                return tuple(str(item) for item in value if item)
            if value:
                return (str(value),)
        return ()

    @staticmethod
    def _has_explicit_outcome(result: dict[str, Any]) -> bool:
        return any(name in result for name in ("accepted", "successful", "status"))

    @staticmethod
    def _header_value(result: Any, name: str) -> str | None:
        headers = getattr(result, "headers", None)
        if headers is None:
            return None
        value = headers.get(name)
        return str(value) if value else None

    @staticmethod
    def _complete_record(record: DeliveryRecord) -> DeliveryRecord:
        record.completed_at = datetime.now(UTC)
        if record.initiated_at:
            record.delivery_duration_ms = int((record.completed_at - record.initiated_at).total_seconds() * 1000)
        return record

    def _format_content(self, content_block: ContentBlock, channel: ChannelType) -> str:
        """Format content for specific channel constraints."""
        if channel == ChannelType.sms:
            return self._format_sms(content_block)
        elif channel == ChannelType.push:
            return f"{content_block.title}\n{content_block.body}\n{content_block.action_items}"
        elif channel == ChannelType.emergency_broadcast:
            # Broadcast: full content en-AU only
            return f"{content_block.title}\n{content_block.body}\n{content_block.action_items}"
        return content_block.body

    def _format_sms(self, content_block: ContentBlock) -> str:
        full_text = f"{content_block.title}\n{content_block.body}\n{content_block.action_items}"
        capacity = min(self._config.sms_max_length, self._sms_character_capacity(full_text))
        if len(full_text) <= capacity:
            return full_text

        urls = re.findall(r"https?://\S+|www\.\S+", content_block.action_items)
        action = content_block.action_items.strip()
        fixed = f"{content_block.title}\n{action}"
        if len(fixed) >= capacity:
            url_suffix = f" {urls[0]}" if urls else ""
            action_without_url = action.replace(urls[0], "").strip() if urls else action
            action_limit = max(0, capacity - len(content_block.title) - len(url_suffix) - 2)
            return f"{content_block.title}\n{action_without_url[:action_limit].rstrip()}…{url_suffix}"[:capacity]
        body_limit = capacity - len(fixed) - 2
        return f"{content_block.title}\n{content_block.body[:body_limit].rstrip()}…\n{action}"[:capacity]

    @staticmethod
    def _gsm7_units(text: str) -> int | None:
        units = 0
        for character in text:
            if character in _GSM7_BASIC:
                units += 1
            elif character in _GSM7_EXTENDED:
                units += 2
            else:
                return None
        return units

    @classmethod
    def _sms_segment_count(cls, text: str) -> int:
        gsm_units = cls._gsm7_units(text)
        if gsm_units is not None:
            return 1 if gsm_units <= 160 else math.ceil(gsm_units / 153)
        return 1 if len(text) <= 70 else math.ceil(len(text) / 67)

    def _sms_character_capacity(self, text: str) -> int:
        return min(self._config.sms_max_length, 612 if self._gsm7_units(text) is not None else 268)

    def _create_simulation_records(self, alert: PublicAlert, segments: list[AudienceSegment]) -> list[DeliveryRecord]:
        """Create delivery records for simulation without real delivery."""
        records = []
        for segment in segments:
            for channel in segment.delivery_channels:
                channel_val = channel.value if isinstance(channel, ChannelType) else channel
                records.append(
                    DeliveryRecord(
                        delivery_id=str(
                            uuid5(
                                _DELIVERY_NAMESPACE,
                                f"{alert.tenant_id}|{alert.alert_id}|{alert.version}|{channel_val}|{segment.segment_id}",
                            )
                        ),
                        alert_id=alert.alert_id,
                        alert_version=alert.version,
                        channel=ChannelType(channel_val),
                        audience_segment_id=segment.segment_id,
                        language_used=segment.preferred_language,
                        delivery_status=DeliveryStatus.skipped,
                        targeted_recipient_count=len(segment.recipient_ids) or 1,
                        content_payload="[SIMULATION]",
                        tenant_id=alert.tenant_id,
                        completed_at=datetime.now(UTC),
                    )
                )
        return records

    def get_channel_health(self) -> dict[str, bool]:
        """Return current channel health status."""
        return dict(self._channel_health)

    __all__ = ["ApprovalRequiredError", "MultiChannelDeliveryService", "NotificationHubRestClient"]
