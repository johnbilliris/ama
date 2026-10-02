"""Tenant-bound persistence for communication alert aggregates."""

from __future__ import annotations

from copy import deepcopy
from datetime import UTC, datetime
from typing import Any

from communication.models import AlertStatus, AudienceSegment, DeliveryRecord, PublicAlert


class AlertNotFoundError(LookupError):
    """Raised when an alert does not exist in the requested tenant partition."""


class CommunicationAlertRepository:
    """Persist alert state, audience snapshots, and delivery outcomes atomically."""

    def __init__(
        self,
        container: Any | None = None,
        *,
        documents: dict[tuple[str, str], dict[str, Any]] | None = None,
    ) -> None:
        self._container = container
        self._documents = documents if documents is not None else {}

    def create(self, alert: PublicAlert, segments: list[AudienceSegment]) -> PublicAlert:
        document = self._document(alert, segments=segments, delivery_records=[])
        if self._container is not None:
            created = self._container.create_item(body=document)
            return self._alert_from_document(created)

        key = (alert.tenant_id, alert.alert_id)
        if key in self._documents:
            raise ValueError(f"Alert {alert.alert_id} already exists")
        document["_etag"] = "1"
        self._documents[key] = deepcopy(document)
        return self._alert_from_document(document)

    def get(self, tenant_id: str, alert_id: str) -> PublicAlert | None:
        try:
            if self._container is not None:
                document = self._container.read_item(item=alert_id, partition_key=tenant_id)
            else:
                document = self._documents[(tenant_id, alert_id)]
        except (KeyError, LookupError):
            return None
        except Exception as exc:
            status_code = getattr(exc, "status_code", None) or getattr(exc, "http_status", None)
            if status_code == 404:
                return None
            raise
        return self._alert_from_document(deepcopy(document))

    def require(self, tenant_id: str, alert_id: str) -> PublicAlert:
        alert = self.get(tenant_id, alert_id)
        if alert is None:
            raise AlertNotFoundError(f"Alert {alert_id} not found")
        return alert

    def replace(self, alert: PublicAlert, *, expected_etag: str | None = None) -> PublicAlert:
        existing = self._read_document(alert.tenant_id, alert.alert_id)
        self._assert_immutable_version(existing, alert)
        document = self._document(
            alert,
            segments=[AudienceSegment.model_validate(row) for row in existing.get("audience_segment_snapshots", [])],
            delivery_records=[DeliveryRecord.model_validate(row) for row in existing.get("delivery_records", [])],
            approval_requests=existing.get("approval_requests", []),
        )
        etag = expected_etag or getattr(alert, "_etag", None) or existing.get("_etag")
        if self._container is not None:
            replaced = self._container.replace_item(
                item=alert.alert_id,
                body=document,
                if_match=etag,
            )
            return self._alert_from_document(replaced)

        key = (alert.tenant_id, alert.alert_id)
        if etag is not None and str(existing.get("_etag")) != str(etag):
            raise RuntimeError("412 PreconditionFailed")
        document["_etag"] = str(int(existing.get("_etag", "0")) + 1)
        self._documents[key] = deepcopy(document)
        return self._alert_from_document(document)

    def supersede(self, tenant_id: str, previous_alert_id: str, replacement_alert_id: str) -> PublicAlert:
        previous = self.require(tenant_id, previous_alert_id)
        if previous.status not in {
            "approved",
            "delivering",
            "delivered",
            "partially_delivered",
            "delivery_failed",
        }:
            return previous
        previous.status = AlertStatus.superseded
        previous.superseded_by_alert_id = replacement_alert_id
        return self.replace(previous)

    def save_delivery(self, alert: PublicAlert, records: list[DeliveryRecord]) -> PublicAlert:
        existing = self._read_document(alert.tenant_id, alert.alert_id)
        segments = [AudienceSegment.model_validate(row) for row in existing.get("audience_segment_snapshots", [])]
        existing_records = [DeliveryRecord.model_validate(row) for row in existing.get("delivery_records", [])]
        by_id = {record.delivery_id: record for record in existing_records}
        by_id.update({record.delivery_id: record for record in records})
        document = self._document(
            alert,
            segments=segments,
            delivery_records=list(by_id.values()),
            approval_requests=existing.get("approval_requests", []),
        )

        if self._container is not None:
            replaced = self._container.replace_item(
                item=alert.alert_id,
                body=document,
                if_match=existing.get("_etag"),
            )
            return self._alert_from_document(replaced)

        document["_etag"] = str(int(existing.get("_etag", "0")) + 1)
        self._documents[(alert.tenant_id, alert.alert_id)] = deepcopy(document)
        return self._alert_from_document(document)

    def audience_segments(self, tenant_id: str, alert_id: str) -> list[AudienceSegment]:
        document = self._read_document(tenant_id, alert_id)
        return [AudienceSegment.model_validate(row) for row in document.get("audience_segment_snapshots", [])]

    def delivery_records(self, tenant_id: str, alert_id: str) -> list[DeliveryRecord]:
        document = self._read_document(tenant_id, alert_id)
        return [DeliveryRecord.model_validate(row) for row in document.get("delivery_records", [])]

    def save_approval_request(
        self,
        tenant_id: str,
        alert_id: str,
        request: dict[str, Any],
    ) -> None:
        document = self._read_document(tenant_id, alert_id)
        requests = {
            str(item["request_id"]): item
            for item in document.get("approval_requests", [])
            if isinstance(item, dict) and item.get("request_id")
        }
        requests[str(request["request_id"])] = deepcopy(request)
        document["approval_requests"] = list(requests.values())
        self._replace_document(tenant_id, alert_id, document)

    def approval_requests(self, tenant_id: str, alert_id: str) -> list[dict[str, Any]]:
        document = self._read_document(tenant_id, alert_id)
        return deepcopy(document.get("approval_requests", []))

    def pending_approval_requests(self) -> list[dict[str, Any]]:
        if self._container is not None:
            documents = self._container.query_items(
                query="SELECT c.id, c.tenant_id, c.approval_requests FROM c WHERE IS_DEFINED(c.approval_requests)",
                enable_cross_partition_query=True,
            )
        else:
            documents = self._documents.values()
        pending: list[dict[str, Any]] = []
        for document in documents:
            for request in document.get("approval_requests", []):
                if isinstance(request, dict) and request.get("status") in {"pending", "failed"}:
                    pending.append(deepcopy(request))
        return pending

    def pending_escalations(self) -> list[PublicAlert]:
        if self._container is not None:
            documents = self._container.query_items(
                query=(
                    "SELECT * FROM c WHERE c.status = 'pending_review' "
                    "AND IS_DEFINED(c.approval_deadline_at) AND NOT IS_NULL(c.approval_deadline_at)"
                ),
                enable_cross_partition_query=True,
            )
        else:
            documents = self._documents.values()
        return [self._alert_from_document(deepcopy(document)) for document in documents]

    def version_history(self, tenant_id: str, incident_id: str) -> list[PublicAlert]:
        if self._container is not None:
            documents = self._container.query_items(
                query="SELECT * FROM c WHERE c.incident_id = @incident_id ORDER BY c.version ASC",
                parameters=[{"name": "@incident_id", "value": incident_id}],
                partition_key=tenant_id,
            )
        else:
            documents = [
                document
                for (document_tenant, _), document in self._documents.items()
                if document_tenant == tenant_id and document.get("incident_id") == incident_id
            ]
        return sorted(
            (self._alert_from_document(deepcopy(document)) for document in documents),
            key=lambda alert: alert.version,
        )

    def expire_due(self, now: datetime | None = None) -> list[str]:
        observed_at = (now or datetime.now(UTC)).astimezone(UTC)
        if self._container is not None:
            documents = self._container.query_items(
                query=(
                    "SELECT * FROM c WHERE c.status IN ('delivered', 'partially_delivered') "
                    "AND IS_DEFINED(c.expires_at) AND c.expires_at <= @now"
                ),
                parameters=[{"name": "@now", "value": observed_at.isoformat()}],
                enable_cross_partition_query=True,
            )
        else:
            documents = list(self._documents.values())

        expired: list[str] = []
        for document in documents:
            alert = self._alert_from_document(deepcopy(document))
            if alert.status not in {AlertStatus.delivered, AlertStatus.partially_delivered}:
                continue
            if alert.expires_at is None or alert.expires_at.astimezone(UTC) > observed_at:
                continue
            alert.status = AlertStatus.expired
            alert.updated_at = observed_at
            try:
                self.replace(alert)
            except Exception as exc:
                if "412" in str(exc) or "PreconditionFailed" in str(exc):
                    continue
                raise
            expired.append(alert.alert_id)
        return expired

    def _read_document(self, tenant_id: str, alert_id: str) -> dict[str, Any]:
        if self._container is not None:
            try:
                return self._container.read_item(item=alert_id, partition_key=tenant_id)
            except Exception as exc:
                status_code = getattr(exc, "status_code", None) or getattr(exc, "http_status", None)
                if status_code == 404:
                    raise AlertNotFoundError(f"Alert {alert_id} not found") from exc
                raise
        try:
            return deepcopy(self._documents[(tenant_id, alert_id)])
        except KeyError as exc:
            raise AlertNotFoundError(f"Alert {alert_id} not found") from exc

    @staticmethod
    def _assert_immutable_version(existing: dict[str, Any], alert: PublicAlert) -> None:
        immutable_fields = {
            "alert_id",
            "incident_id",
            "version",
            "change_type",
            "change_summary",
            "referenced_alert_id",
            "content_blocks",
            "audience_segments",
            "languages",
            "accessibility_attributes",
            "channel_set",
            "generation_method",
            "model_deployment_id",
            "content_safety_result",
            "content_safety_details",
            "confidence",
            "recommendation_id",
            "assessment_id",
            "assessment_timestamp",
            "assessment_freshness",
            "tenant_id",
            "mode",
            "warning_tier",
            "active_subzone_ids",
            "created_at",
            "expires_at",
        }
        replacement = alert.model_dump(mode="json")
        changed = sorted(field for field in immutable_fields if existing.get(field) != replacement.get(field))
        if changed:
            raise ValueError(f"Persisted alert versions are immutable: {', '.join(changed)}")

    @staticmethod
    def _document(
        alert: PublicAlert,
        *,
        segments: list[AudienceSegment],
        delivery_records: list[DeliveryRecord],
        approval_requests: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        document = alert.model_dump(mode="json")
        document["id"] = alert.alert_id
        document["audience_segment_snapshots"] = [segment.model_dump(mode="json") for segment in segments]
        document["delivery_records"] = [record.model_dump(mode="json") for record in delivery_records]
        document["approval_requests"] = deepcopy(approval_requests or [])
        return document

    def _replace_document(self, tenant_id: str, alert_id: str, document: dict[str, Any]) -> None:
        if self._container is not None:
            replacement = deepcopy(document)
            etag = replacement.pop("_etag", None)
            self._container.replace_item(
                item=alert_id,
                body=replacement,
                if_match=etag,
            )
            return
        current = self._documents[(tenant_id, alert_id)]
        document["_etag"] = str(int(current.get("_etag", "0")) + 1)
        self._documents[(tenant_id, alert_id)] = deepcopy(document)

    @staticmethod
    def _alert_from_document(document: dict[str, Any]) -> PublicAlert:
        payload = {
            key: value
            for key, value in document.items()
            if key not in {"id", "_etag", "audience_segment_snapshots", "delivery_records"}
        }
        alert = PublicAlert.model_validate(payload)
        alert._etag = str(document.get("_etag")) if document.get("_etag") is not None else None
        return alert


__all__ = ["AlertNotFoundError", "CommunicationAlertRepository"]
