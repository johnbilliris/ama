import hashlib
import json
import logging
from datetime import UTC, datetime
from typing import Any, Protocol
from uuid import uuid4

from app.core.tenant_context import get_current_tenant
from app.services.audit_service import AuditService
from app.services.operational_store import OperationalStore
from fastapi import HTTPException

from apps.agents.communication.cap_serialiser import serialize_cap, validate_cap_xml
from apps.agents.communication.edxl_serialiser import serialize_to_edxl
from packages.domain.src.domain.models.approval_decision import ApprovalDecision
from packages.domain.src.domain.models.public_alert import PublicAlert
from packages.domain.src.domain.tenant_mode import is_live_tenant

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

REQUIRED_ALERT_LANGUAGES: frozenset[str] = frozenset({"en-AU", "zh-Hans", "ar", "vi", "el", "it"})

_AUTHORITY_RANKS: dict[str, int] = {
    "executive-leader": 5,
    "incident-commander": 10,
    "operations-officer": 20,
    "planning-officer": 30,
    "logistics-officer": 40,
    "public-information-officer": 50,
    "field-coordinator": 60,
    "risk-manager": 65,
    "resilience-planner": 70,
    "observer-auditor": 90,
}


class AlertTransportClient(Protocol):
    def send(
        self, *, alert: PublicAlert, channel: str, recipient: str, payload: dict[str, Any]
    ) -> dict[str, Any] | None: ...


_TRANSPORT_CLIENTS: dict[str, AlertTransportClient | None] = {
    "sms": None,
    "push": None,
    "email": None,
    "emergency_broadcast": None,
}


def configure_transport_clients(clients: dict[str, AlertTransportClient | None]) -> None:
    for channel, client in clients.items():
        _TRANSPORT_CLIENTS[channel] = client


def _canonical_payload_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def stamp_alert_content_version(alert: PublicAlert) -> None:
    content_digest = hashlib.sha256(_canonical_payload_bytes(alert.content_blocks)).hexdigest()
    alert.content_blocks["contentSha256"] = content_digest
    alert.content_blocks["contentVersion"] = content_digest[:16]


def compute_alert_binding_sha256(alert: PublicAlert) -> str:
    content_blocks = {
        key: value for key, value in alert.content_blocks.items() if key not in {"publishedBy", "approvalDecisionId"}
    }
    payload = {
        "alertId": alert.alert_id,
        "incidentId": alert.incident_id,
        "contentBlocks": content_blocks,
        "contentVersion": alert.content_blocks.get("contentVersion", ""),
        "audienceSegments": sorted(alert.audience_segments),
        "languages": sorted(alert.languages),
        "channelSet": sorted(alert.channel_set),
    }
    return hashlib.sha256(_canonical_payload_bytes(payload)).hexdigest()


def _condition_value(conditions: list[str], key: str) -> str | None:
    prefix = f"{key}="
    for condition in conditions:
        if condition.startswith(prefix):
            return condition[len(prefix) :]
    return None


def _normalize_approval_level(level: str) -> str:
    return level.strip().replace("_", "-").lower()


def _approval_rank_for_level(level: str) -> int:
    normalized = _normalize_approval_level(level)
    return _AUTHORITY_RANKS.get(normalized, 1)


def _approver_max_authority_rank(approver_roles: list[str] | tuple[str, ...]) -> int | None:
    ranks = [_AUTHORITY_RANKS[role] for role in approver_roles if role in _AUTHORITY_RANKS]
    return min(ranks) if ranks else None


def assert_approver_authority(required_level: str, approver_roles: list[str] | tuple[str, ...]) -> None:
    approver_rank = _approver_max_authority_rank(approver_roles)
    required_rank = _approval_rank_for_level(required_level)
    if approver_rank is None or approver_rank > required_rank:
        raise HTTPException(status_code=403, detail="Approver role does not satisfy required approval level")


def _require_alert_approval_ready(alert: PublicAlert) -> None:
    if not alert.audience_segments:
        raise HTTPException(status_code=409, detail="Alert draft must include at least one audience segment")
    if not alert.channel_set:
        raise HTTPException(status_code=409, detail="Alert draft must include at least one channel")
    languages = set(alert.languages)
    if not REQUIRED_ALERT_LANGUAGES.issubset(languages):
        raise HTTPException(status_code=409, detail="Alert draft must include all six supported languages")
    if alert.content_safety_result != "passed":
        raise HTTPException(status_code=409, detail="Alert draft safety metadata must pass before approval")
    if not alert.content_blocks.get("headline") or not alert.content_blocks.get("body"):
        raise HTTPException(status_code=409, detail="Alert draft must include headline and body")
    for language in REQUIRED_ALERT_LANGUAGES:
        if not str(alert.content_blocks.get(language, "")).strip():
            raise HTTPException(status_code=409, detail=f"Alert draft missing content block for language {language}")


def _resolve_required_approval_level(alert: PublicAlert, store: OperationalStore) -> str:
    recommendation_id = str(alert.content_blocks.get("recommendationId") or "")
    if recommendation_id:
        recommendation = store.recommendations.get(recommendation_id)
        if recommendation is not None and recommendation.required_approval_level:
            return recommendation.required_approval_level
    return str(alert.content_blocks.get("requiredApprovalLevel") or "incident_commander")


def _validate_publishable(alert: PublicAlert) -> None:
    if alert.status != "approved":
        raise HTTPException(status_code=409, detail=f"Alert status '{alert.status}' is not publishable")
    _require_alert_approval_ready(alert)


def _validate_dispatch_payloads(alert: PublicAlert) -> None:
    cap_xml = serialize_cap(alert)
    validate_cap_xml(cap_xml)
    edxl_xml = serialize_to_edxl(alert)
    if "urn:oasis:names:tc:emergency:EDXL:DE:2.0" not in edxl_xml:
        raise HTTPException(status_code=422, detail="EDXL payload does not use EDXL-DE 2.0 namespace")


def _resolve_approval_decision(alert_id: str) -> tuple[str, ApprovalDecision]:
    store = OperationalStore.current()
    for approval_decision_id, decision in store.approvals.items():
        if decision.public_alert_id == alert_id and decision.outcome == "approved":
            return approval_decision_id, decision
    raise HTTPException(
        status_code=409,
        detail="Alert must have a recorded approved decision before publishing",
    )


def _validate_approval_binding(alert: PublicAlert, conditions: list[str]) -> None:
    expected_version = _condition_value(conditions, "contentVersion")
    expected_binding = _condition_value(conditions, "bindingSha256")
    current_version = alert.content_blocks.get("contentVersion")
    current_binding = compute_alert_binding_sha256(alert)

    if not expected_version or not expected_binding:
        raise HTTPException(status_code=409, detail="Approval decision is missing binding metadata")
    if current_version != expected_version or current_binding != expected_binding:
        raise HTTPException(status_code=409, detail="Alert content/audience changed since approval")

    expected_safety = _condition_value(conditions, "safetyStatus")
    if expected_safety and expected_safety != alert.content_safety_result:
        raise HTTPException(status_code=409, detail="Alert safety state changed since approval")

    expected_languages = _condition_value(conditions, "languages")
    if expected_languages:
        current_languages = ",".join(sorted(alert.languages))
        if current_languages != expected_languages:
            raise HTTPException(status_code=409, detail="Alert language set changed since approval")

    expected_channels = _condition_value(conditions, "channels")
    if expected_channels:
        current_channels = ",".join(sorted(alert.channel_set))
        if current_channels != expected_channels:
            raise HTTPException(status_code=409, detail="Alert channel set changed since approval")

    expected_audience = _condition_value(conditions, "audience")
    if expected_audience:
        current_audience = ",".join(sorted(alert.audience_segments))
        if current_audience != expected_audience:
            raise HTTPException(status_code=409, detail="Alert audience changed since approval")


class PublicAlertService:
    def get_alert(self, alert_id: str) -> PublicAlert:
        return OperationalStore.current().alerts.require(alert_id)

    def update_draft(
        self,
        alert_id: str,
        *,
        content_blocks: dict[str, str] | None = None,
        audience_segments: list[str] | None = None,
        languages: list[str] | None = None,
        channel_set: list[str] | None = None,
    ) -> PublicAlert:
        store = OperationalStore.current()
        alert = store.alerts.require(alert_id)
        if alert.status in {"approved", "published", "superseded", "cancelled"}:
            raise HTTPException(status_code=409, detail="Alert draft cannot be edited after approval workflow")

        if content_blocks is not None:
            alert.content_blocks.update({key: value for key, value in content_blocks.items() if value})
        if audience_segments is not None:
            alert.audience_segments = list(dict.fromkeys(segment for segment in audience_segments if segment))
        if languages is not None:
            alert.languages = list(dict.fromkeys(language for language in languages if language))
        if channel_set is not None:
            alert.channel_set = list(dict.fromkeys(channel for channel in channel_set if channel))

        if not alert.languages:
            raise HTTPException(status_code=422, detail="Alert draft must include at least one language")
        if not alert.channel_set:
            raise HTTPException(status_code=422, detail="Alert draft must include at least one channel")

        stamp_alert_content_version(alert)
        return alert

    def apply_template(self, alert_id: str, template_key: str) -> PublicAlert:
        store = OperationalStore.current()
        alert = store.alerts.require(alert_id)
        if alert.status in {"approved", "published", "superseded", "cancelled"}:
            raise HTTPException(status_code=409, detail="Cannot modify template after approval workflow")
        template = DELIVERY_TEMPLATES.get(template_key)
        if template is None:
            raise HTTPException(status_code=404, detail=f"Unknown template '{template_key}'")
        alert.content_blocks.update(template)
        stamp_alert_content_version(alert)
        return alert

    def approve_draft(
        self,
        alert_id: str,
        approver_persona_id: str,
        approver_roles: list[str] | tuple[str, ...],
        rationale: str,
        conditions: list[str] | None = None,
    ) -> ApprovalDecision:
        store = OperationalStore.current()
        alert = store.alerts.require(alert_id)
        if alert.status in {"published", "superseded", "cancelled"}:
            raise HTTPException(status_code=409, detail="Alert is already in a terminal state")

        _require_alert_approval_ready(alert)

        required_level = _resolve_required_approval_level(alert, store)
        assert_approver_authority(required_level, approver_roles)

        stamp_alert_content_version(alert)
        binding_sha = compute_alert_binding_sha256(alert)
        normalized_conditions = list(conditions or [])
        normalized_conditions.extend(
            [
                f"contentVersion={alert.content_blocks['contentVersion']}",
                f"bindingSha256={binding_sha}",
                f"safetyStatus={alert.content_safety_result}",
                f"languages={','.join(sorted(alert.languages))}",
                f"channels={','.join(sorted(alert.channel_set))}",
                f"audience={','.join(sorted(alert.audience_segments))}",
                f"requiredApprovalLevel={_normalize_approval_level(required_level)}",
            ]
        )

        existing_decision: ApprovalDecision | None = None
        for _, decision in store.approvals.items():
            if decision.public_alert_id == alert_id and decision.outcome == "approved":
                existing_decision = decision
                break

        if existing_decision is not None:
            if (
                existing_decision.approver_persona_id == approver_persona_id
                and existing_decision.rationale == rationale.strip()
                and sorted(existing_decision.conditions) == sorted(normalized_conditions)
            ):
                return existing_decision
            raise HTTPException(status_code=409, detail="Alert already has an approved version decision")

        decision = ApprovalDecision(
            approval_decision_id=f"appr-{uuid4().hex[:8]}",
            recommendation_id=None,
            public_alert_id=alert_id,
            approver_persona_id=approver_persona_id,
            outcome="approved",
            rationale=rationale.strip(),
            conditions=normalized_conditions,
        )

        alert.status = "approved"
        store.alerts.put(alert.alert_id, alert)
        store.approvals.put(decision.approval_decision_id, decision)

        AuditService().record_event(
            incident_id=alert.incident_id,
            event_type="approval",
            summary=f"Approved alert draft {alert_id}",
            actor=approver_persona_id,
            tenant_id=store.tenant_id,
            mode=alert.mode,
            correlation_id=decision.approval_decision_id,
            outcome="approved",
            route="/api/alerts/{alert_id}/approvals",
            content_version=alert.content_blocks.get("contentVersion"),
            rationale=decision.rationale,
            payload={
                "alertId": alert.alert_id,
                "requiredApprovalLevel": _normalize_approval_level(required_level),
            },
        )
        return decision

    def publish(self, alert_id: str, published_by_persona_id: str) -> PublicAlert:
        store = OperationalStore.current()
        alert = store.alerts.require(alert_id)
        _validate_publishable(alert)
        approval_decision_id, approval_decision = _resolve_approval_decision(alert_id)
        _validate_approval_binding(alert, approval_decision.conditions)

        AuditService().record_event(
            incident_id=alert.incident_id,
            event_type="publication",
            summary=f"Published alert {alert_id}",
            actor=published_by_persona_id,
            tenant_id=store.tenant_id,
            mode=alert.mode,
            correlation_id=approval_decision_id,
            outcome="published",
            route="/api/alerts/{alert_id}/publish",
            content_version=alert.content_blocks.get("contentVersion"),
            rationale="Human-approved public alert published",
            payload={"alertId": alert.alert_id, "approvalDecisionId": approval_decision_id},
        )

        alert.status = "published"
        alert.published_at = datetime.now(UTC)
        alert.content_blocks["publishedBy"] = published_by_persona_id
        alert.content_blocks["approvalDecisionId"] = approval_decision_id
        return alert

    def supersede(self, alert_id: str, new_alert_id: str) -> PublicAlert:
        store = OperationalStore.current()
        old = store.alerts.get(alert_id)
        new = store.alerts.get(new_alert_id)
        if old is None or new is None:
            raise HTTPException(status_code=404, detail="Alert not found")
        if old.alert_id == new.alert_id:
            raise HTTPException(status_code=409, detail="Alert cannot supersede itself")
        if old.incident_id != new.incident_id:
            raise HTTPException(status_code=409, detail="Superseding alert must target the same incident")
        if old.status != "published":
            raise HTTPException(status_code=409, detail="Only published alerts can be superseded")
        if new.status not in {"approved", "published"}:
            raise HTTPException(status_code=409, detail="Superseding alert must be approved before use")

        AuditService().record_event(
            incident_id=old.incident_id,
            event_type="supersession",
            summary=f"Superseded alert {old.alert_id} with {new.alert_id}",
            actor="system",
            tenant_id=store.tenant_id,
            mode=old.mode,
            correlation_id=f"supersede-{old.alert_id}",
            outcome="superseded",
            route="/api/alerts/{alert_id}/supersede",
            content_version=new.content_blocks.get("contentVersion"),
            rationale="Updated public alert superseded a published predecessor",
            payload={"oldAlertId": old.alert_id, "newAlertId": new.alert_id},
        )

        old.status = "superseded"
        old.content_blocks["supersededByAlertId"] = new.alert_id
        new.superseded_warning_id = old.alert_id
        return old

    def deliver(self, alert_id: str) -> list[dict[str, Any]]:
        store = OperationalStore.current()
        alert = store.alerts.require(alert_id)
        if alert.status != "published":
            raise HTTPException(status_code=409, detail="Alert must be published before delivery")

        _validate_dispatch_payloads(alert)

        current_tenant_id = ""
        try:
            tenant = get_current_tenant()
            current_tenant_id = tenant.tenant_id
        except LookupError:
            current_tenant_id = ""

        artifact_is_live = is_live_tenant(alert.tenant_id) and alert.mode == "live"
        current_is_live = is_live_tenant(current_tenant_id)
        if not artifact_is_live or not current_is_live:
            correlation_id = alert.content_blocks.get("simulationDeliveryCorrelationId")
            if not correlation_id:
                content_version = str(alert.content_blocks.get("contentVersion", "unversioned"))
                correlation_id = f"sim-publish-{alert.alert_id}-{content_version}"
                AuditService().record_event(
                    incident_id=alert.incident_id,
                    event_type="publication",
                    summary=f"Recorded simulated publication for alert {alert_id}",
                    actor=str(alert.content_blocks.get("publishedBy", "system")),
                    tenant_id=store.tenant_id,
                    mode="rehearsal",
                    correlation_id=correlation_id,
                    outcome="published_simulation",
                    route="/api/alerts/{alert_id}/deliver",
                    content_version=alert.content_blocks.get("contentVersion"),
                    rationale="External delivery blocked for non-live tenant or artifact",
                    payload={"alertId": alert.alert_id, "currentTenantId": current_tenant_id},
                )
                alert.content_blocks["simulationDeliveryCorrelationId"] = correlation_id
            logger.info(
                "alert_delivery_blocked_non_live artifact_tenant_id=%s artifact_mode=%s current_tenant_id=%s alert_id=%s",  # noqa: E501
                alert.tenant_id,
                alert.mode,
                current_tenant_id,
                alert_id,
            )
            return [
                {
                    "alertId": alert.alert_id,
                    "contentVersion": alert.content_blocks.get("contentVersion"),
                    "channel": "simulation",
                    "recipient": "simulation",
                    "status": "simulation",
                    "providerReceipt": correlation_id,
                }
            ]

        results = []
        recipients = list(dict.fromkeys(alert.audience_segments))
        languages = alert.languages or ["en-AU"]
        content_version = str(alert.content_blocks.get("contentVersion", ""))
        content_payload = {
            "headline": alert.content_blocks.get("headline", ""),
            "body": alert.content_blocks.get("body", ""),
        }

        for channel in alert.channel_set:
            client = _TRANSPORT_CLIENTS.get(channel)
            for recipient in recipients:
                for language in languages:
                    if channel == "emergency_broadcast" and language != "en-AU":
                        results.append(
                            {
                                "alertId": alert.alert_id,
                                "contentVersion": content_version,
                                "channel": channel,
                                "recipient": recipient,
                                "language": language,
                                "status": "skipped",
                                "providerReceipt": None,
                            }
                        )
                        continue

                    if client is None:
                        results.append(
                            {
                                "alertId": alert.alert_id,
                                "contentVersion": content_version,
                                "channel": channel,
                                "recipient": recipient,
                                "language": language,
                                "status": "skipped",
                                "providerReceipt": None,
                            }
                        )
                        continue

                    try:
                        receipt = client.send(
                            alert=alert,
                            channel=channel,
                            recipient=recipient,
                            payload={
                                **content_payload,
                                "language": language,
                                "audienceSegments": recipients,
                                "channels": alert.channel_set,
                            },
                        )
                        acknowledged = bool(receipt and receipt.get("acknowledged"))
                        results.append(
                            {
                                "alertId": alert.alert_id,
                                "contentVersion": content_version,
                                "channel": channel,
                                "recipient": recipient,
                                "language": language,
                                "status": "acknowledged" if acknowledged else "submitted",
                                "providerReceipt": receipt if acknowledged else None,
                            }
                        )
                    except Exception as exc:
                        results.append(
                            {
                                "alertId": alert.alert_id,
                                "contentVersion": content_version,
                                "channel": channel,
                                "recipient": recipient,
                                "language": language,
                                "status": "failed",
                                "providerReceipt": {"error": str(exc)},
                            }
                        )

        AuditService().record_event(
            incident_id=alert.incident_id,
            event_type="delivery",
            summary=f"Delivered alert {alert_id} to {len(results)} channels",
            actor="system",
            tenant_id=store.tenant_id,
            mode=alert.mode,
            correlation_id=f"delivery-{alert_id}",
            outcome="delivered",
            route="/api/alerts/{alert_id}/deliver",
            content_version=alert.content_blocks.get("contentVersion"),
            rationale="Delivery attempted for published alert",
            payload={
                "alertId": alert.alert_id,
                "channels": [entry.get("channel") for entry in results],
                "statuses": [entry.get("status") for entry in results],
            },
        )
        return results
