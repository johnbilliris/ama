from __future__ import annotations

import pytest
from app.repositories.audit_repository import AuditRepository
from app.services.audit_service import AuditService
from app.services.simulation_audit_writer import SimulationAuditWriter

pytestmark = pytest.mark.spec007_isolation


class _FailingContainer:
    def upload_blob(self, **kwargs):  # noqa: ANN003, ANN201, ARG002
        raise ConnectionError("blob unavailable")


class _FailingBlobService:
    def get_container_client(self, name):  # noqa: ANN001, ANN201, ARG002
        return _FailingContainer()


def test_simulation_audit_blob_failure_is_not_reported_as_success() -> None:
    writer = SimulationAuditWriter(blob_service_client=_FailingBlobService())

    with pytest.raises(RuntimeError, match="persistence failed"):
        writer.write_event_sync(
            tenant_id="sim-12345678-1234-1234-1234-123456789012",
            action="task_change",
            actor_id="participant-1",
            resource_id="task-1",
            correlation_id="task-1-completed",
        )


def test_simulation_audit_idempotently_bridges_domain_events(monkeypatch: pytest.MonkeyPatch) -> None:
    writer = SimulationAuditWriter()
    monkeypatch.setattr(
        "app.services.simulation_audit_writer.get_simulation_audit_writer",
        lambda: writer,
    )
    service = AuditService(repository=AuditRepository(environment="test"))
    kwargs = {
        "incident_id": "incident-1",
        "event_type": "task_status",
        "summary": "Task completed",
        "actor": "participant-1",
        "tenant_id": "sim-12345678-1234-1234-1234-123456789012",
        "mode": "rehearsal",
        "correlation_id": "task-1-completed",
        "outcome": "completed",
        "route": "/api/tasks/{task_id}",
        "payload": {"taskId": "task-1"},
    }

    service.record_event(**kwargs)
    service.record_event(**kwargs)

    assert len(writer.in_memory_events) == 1
    assert writer.in_memory_events[0]["action"] == "task_change"
    assert writer.in_memory_events[0]["tenant_id"].startswith("sim-")
