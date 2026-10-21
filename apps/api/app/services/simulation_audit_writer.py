import hashlib
import json
import logging
import os
from datetime import UTC, datetime
from typing import Any, Literal
from uuid import uuid4

from app.core.async_io import run_blocking

logger = logging.getLogger(__name__)


def build_simulation_blob_service_client() -> Any | None:
    account_name = os.environ.get("STORAGE_ACCOUNT_NAME", "").strip()
    if not account_name:
        return None
    from azure.identity import DefaultAzureCredential
    from azure.storage.blob import BlobServiceClient

    return BlobServiceClient(
        account_url=f"https://{account_name}.blob.core.windows.net",
        credential=DefaultAzureCredential(),
    )


class SimulationAuditWriter:
    """Writes audit events to blob storage for active simulation tenants (FR-025).

    Every safety-critical action (signal write, recommendation, approval, alert,
    agent handoff) within a simulation tenant is recorded as an append blob entry
    at `audit/{tenant_id}/{date}/{event_id}.json`.
    """

    def __init__(self, blob_service_client: Any = None):
        environment = (os.environ.get("AMA_ENVIRONMENT") or os.environ.get("ENVIRONMENT") or "dev").lower()
        self._blob_client = (
            blob_service_client if blob_service_client is not None else build_simulation_blob_service_client()
        )
        if self._blob_client is None and environment in {"production", "staging"}:
            raise RuntimeError("SimulationAuditWriter requires STORAGE_ACCOUNT_NAME in production/staging")
        self._container_name = "audit"
        self._in_memory_log: list[dict[str, Any]] = []

    async def write_event(
        self,
        tenant_id: str,
        action: Literal[
            "signal_write",
            "recommendation",
            "approval",
            "rejection",
            "escalation",
            "alert_publish",
            "agent_handoff",
        ],
        actor_id: str,
        resource_id: str,
        details: dict[str, Any] | None = None,
        correlation_id: str | None = None,
        timestamp: datetime | None = None,
    ) -> str:
        return await run_blocking(
            self.write_event_sync,
            tenant_id,
            action,
            actor_id,
            resource_id,
            details,
            correlation_id,
            timestamp,
        )

    def write_event_sync(
        self,
        tenant_id: str,
        action: Literal[
            "signal_write",
            "recommendation",
            "approval",
            "rejection",
            "escalation",
            "alert_publish",
            "agent_handoff",
            "task_change",
            "lifecycle",
        ],
        actor_id: str,
        resource_id: str,
        details: dict[str, Any] | None = None,
        correlation_id: str | None = None,
        timestamp: datetime | None = None,
    ) -> str:
        if not tenant_id.startswith("sim-"):
            return ""

        event_key = correlation_id or str(uuid4())
        digest = hashlib.sha256(f"{tenant_id}|{action}|{resource_id}|{event_key}".encode()).hexdigest()
        event_id = f"audit-{digest[:20]}"
        now = timestamp or datetime.now(UTC)
        date_prefix = now.strftime("%Y/%m/%d")
        blob_path = f"{tenant_id}/{date_prefix}/{event_id}.json"

        event = {
            "event_id": event_id,
            "tenant_id": tenant_id,
            "action": action,
            "actor_id": actor_id,
            "resource_id": resource_id,
            "timestamp": now.isoformat(),
            "details": details or {},
            "correlation_id": correlation_id,
        }

        if self._blob_client:
            try:
                container = self._blob_client.get_container_client(self._container_name)
                container.upload_blob(
                    name=blob_path,
                    data=json.dumps(event).encode("utf-8"),
                    overwrite=False,
                )
            except Exception as exc:
                if exc.__class__.__name__ == "ResourceExistsError":
                    return event_id
                logger.exception("Failed to write simulation audit event %s", blob_path)
                raise RuntimeError(f"Simulation audit persistence failed for {event_id}") from exc
        else:
            if not any(existing["event_id"] == event_id for existing in self._in_memory_log):
                self._in_memory_log.append(event)

        return event_id

    @property
    def in_memory_events(self) -> list[dict[str, Any]]:
        return list(self._in_memory_log)

    def audit_prefix(self, tenant_id: str) -> str:
        return f"{self._container_name}/{tenant_id}/"

    def list_tenant_events(self, tenant_id: str) -> list[dict[str, Any]]:
        """Enumerate every persisted audit record for a tenant (blocking)."""
        if not tenant_id.startswith("sim-"):
            return []
        if self._blob_client is None:
            return sorted(
                (dict(event) for event in self._in_memory_log if event.get("tenant_id") == tenant_id),
                key=lambda event: str(event.get("event_id", "")),
            )

        container = self._blob_client.get_container_client(self._container_name)
        events: list[dict[str, Any]] = []
        for blob in container.list_blobs(name_starts_with=f"{tenant_id}/"):
            name = blob["name"] if isinstance(blob, dict) else blob.name
            payload = container.get_blob_client(name).download_blob().readall()
            record = json.loads(payload)
            record["_blob_name"] = name
            events.append(record)
        events.sort(key=lambda event: str(event.get("_blob_name", "")))
        return events

    async def read_tenant_events(self, tenant_id: str) -> list[dict[str, Any]]:
        return await run_blocking(self.list_tenant_events, tenant_id)


_default_writer: SimulationAuditWriter | None = None


def get_simulation_audit_writer() -> SimulationAuditWriter:
    global _default_writer
    if _default_writer is None:
        _default_writer = SimulationAuditWriter()
    return _default_writer


def reset_simulation_audit_writer_for_tests() -> None:
    global _default_writer
    _default_writer = None
