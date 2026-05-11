"""Tests for spec-036 T-N04 — FR-048 fail-closed surface for sequence-allocator exhaustion.

When the audit writer's sequence allocator exhausts its 5-retry budget
(``SequenceAllocationExhausted`` from
:mod:`apps.api.app.repositories.simulation_sequence_repository`) the API
SHALL respond with:

* ``HTTP 503 Service Unavailable``
* ``Retry-After: 5`` response header
* RFC 9457 ``application/problem+json`` body with
  ``type=https://aidr.gov.au/problems/sequence-allocator-unavailable``
  and ``title``, ``status``, ``detail`` fields
* AND a DLQ envelope MUST be buffered (T-N04 / ADR-036-007).

The handler is registered globally via the existing
``add_error_handler_middleware`` chain so any audit-writer call site
benefits without per-route boilerplate.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from apps.api.app.middleware.error_handler import add_error_handler_middleware
from apps.api.app.repositories.simulation_sequence_repository import (
    SequenceAllocationExhausted,
)
from apps.api.app.services.simulation.audit_writer import (
    get_audit_dlq_buffer,
    reset_audit_writer_for_tests,
)


def _build_app(handler_path: str = "/test/exhaust") -> FastAPI:
    app = FastAPI()
    add_error_handler_middleware(app)

    @app.post(handler_path)
    async def _raise() -> dict[str, str]:  # pragma: no cover - exercised via TestClient
        raise SequenceAllocationExhausted(
            "Failed to allocate sequence number for simulation_id='sim-X' "
            "after 5 ETag conflict retries"
        )

    return app


def test_sequence_allocator_exhausted_returns_503_with_retry_after() -> None:
    reset_audit_writer_for_tests()
    app = _build_app()
    client = TestClient(app)
    res = client.post("/test/exhaust")
    assert res.status_code == 503
    assert res.headers.get("Retry-After") == "5"


def test_sequence_allocator_exhausted_returns_problem_json_body() -> None:
    reset_audit_writer_for_tests()
    app = _build_app()
    client = TestClient(app)
    res = client.post("/test/exhaust")
    assert res.headers.get("content-type", "").startswith("application/problem+json")
    body = res.json()
    assert body["type"] == "https://aidr.gov.au/problems/sequence-allocator-unavailable"
    assert body["title"] == "Sequence allocator unavailable"
    assert body["status"] == 503
    assert "detail" in body


def test_dlq_buffer_holds_entry_after_exhaustion() -> None:
    """When the writer raises, the DLQ entry from T-N03 is observable."""

    from apps.api.app.repositories.simulation_sequence_repository import (
        SimulationSequenceRepository,
    )
    from apps.api.app.services.simulation.audit_writer import AuditWriter

    reset_audit_writer_for_tests()
    repo = SimulationSequenceRepository()

    async def _exhausted(simulation_id: str) -> int:
        raise SequenceAllocationExhausted("forced")

    repo.allocate = _exhausted  # type: ignore[method-assign]
    writer = AuditWriter(sequence_repository=repo)

    import asyncio

    async def _try_write() -> None:
        try:
            await writer.write(
                "lifecycle.paused",
                simulation_id="sim-FR048",
                details={"attempted_action": "chat_turn"},
            )
        except SequenceAllocationExhausted:
            return

    asyncio.run(_try_write())
    dlq = get_audit_dlq_buffer()
    assert any(entry.simulation_id == "sim-FR048" for entry in dlq)
    assert all(entry.sequence_number == -1 for entry in dlq)
