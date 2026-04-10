import json
import logging
from datetime import UTC, datetime
from typing import Any, Literal
from uuid import uuid4

logger = logging.getLogger(__name__)


class SimulationAuditWriter:
    """Writes audit events to blob storage for active simulation tenants (FR-025).

    Every safety-critical action (signal write, recommendation, approval, alert,
    agent handoff) within a simulation tenant is recorded as an append blob entry
    at `audit/{tenant_id}/{date}/{event_id}.json`.
    """

    def __init__(self, blob_service_client: Any = None):
        self._blob_client = blob_service_client
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
    ) -> str:
        if not tenant_id.startswith("sim-"):
            return ""

        event_id = f"audit-{uuid4().hex[:12]}"
        now = datetime.now(UTC)
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
        }

        if self._blob_client:
            try:
                container = self._blob_client.get_container_client(self._container_name)
                container.upload_blob(
                    name=blob_path,
                    data=json.dumps(event).encode("utf-8"),
                    overwrite=False,
                )
            except Exception:
                logger.exception("Failed to write simulation audit event %s", blob_path)
        else:
            self._in_memory_log.append(event)

        return event_id
