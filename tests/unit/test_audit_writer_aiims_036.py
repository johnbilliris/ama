"""Unit tests for spec-036 T-T03 — audit envelope writes propagate AIIMS fields.

Per tasks.md §13 (Phase T) and audit-envelope.md §6.3:

* The :class:`AuditEnvelope` carries top-level ``aiims_function`` and
  ``secondary_aiims_tags`` fields (introduced by T-A06 [AMEND] schema 2.0.0).
* :class:`AuditWriter.write` accepts those fields as keyword arguments and
  validates them against the constitution v1.2.0 1+≤2 cap.
* Sub-agent invocation audits (timeout / cancel / degraded) MUST propagate
  the AIIMS function from the originating
  :class:`SubAgentInvocationRecord` so post-hoc NDJSON joins (FR-054) can
  reconstruct AIIMS attribution without re-deriving from agent_role.

The per-type ``details`` schemas for ``sub_agent.timeout`` /
``sub_agent.cancel`` / ``sub_agent.degraded`` are intentionally **NOT
amended** this cycle (envelope §6.3 acknowledged carve-out).
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from apps.api.app.services.simulation.audit_writer import (
    AuditWriter,
    reset_audit_writer_for_tests,
)
from packages.domain.src.domain.models.telemetry_injection_audit_entry import (
    AuditEnvelope,
)


@pytest.fixture(autouse=True)
def _isolate_audit_state() -> None:
    reset_audit_writer_for_tests()


@pytest.mark.asyncio
async def test_audit_writer_propagates_aiims_function_into_envelope() -> None:
    writer = AuditWriter()

    envelope = await writer.write(
        "sub_agent.timeout",
        simulation_id="sim-1",
        details={
            "correlation_id": "corr-1",
            "sub_agent": "Risk",
            "timeout_seconds": 12.5,
        },
        aiims_function="planning",
        secondary_aiims_tags=["intelligence"],
    )

    assert envelope.aiims_function == "planning"
    assert envelope.secondary_aiims_tags == ["intelligence"]


@pytest.mark.asyncio
async def test_audit_writer_secondary_tags_capped_at_two() -> None:
    writer = AuditWriter()

    with pytest.raises(ValidationError):
        await writer.write(
            "sub_agent.cancel",
            simulation_id="sim-1",
            details={
                "correlation_id": "corr-1",
                "sub_agent": "Evac",
                "cancellation_reason": "aborted",
            },
            aiims_function="operations",
            secondary_aiims_tags=[
                "logistics",
                "intelligence",
                "planning",  # 3rd tag — must violate 1+≤2 cap.
            ],
        )


@pytest.mark.asyncio
async def test_audit_writer_aiims_fields_are_optional() -> None:
    """Audit entries unrelated to sub-agent invocation may omit AIIMS fields."""

    writer = AuditWriter()

    envelope = await writer.write(
        "lifecycle.paused",
        simulation_id="sim-1",
        details={
            "attempted_action": "chat_turn",
            "coordinator_user_id": "user-1",
        },
    )

    assert envelope.aiims_function is None
    assert envelope.secondary_aiims_tags is None


@pytest.mark.asyncio
async def test_audit_writer_secondary_tags_must_not_duplicate_primary() -> None:
    writer = AuditWriter()

    with pytest.raises(ValidationError):
        await writer.write(
            "sub_agent.degraded",
            simulation_id="sim-1",
            details={
                "correlation_id": "corr-1",
                "sub_agent": "Risk",
                "degradation_reason": "rate_limit_exhausted",
            },
            aiims_function="planning",
            secondary_aiims_tags=["planning"],  # primary duplicated → reject
        )


@pytest.mark.asyncio
async def test_audit_envelope_round_trips_aiims_fields() -> None:
    """Envelope serialises and deserialises the new fields intact."""

    writer = AuditWriter()

    envelope = await writer.write(
        "sub_agent.timeout",
        simulation_id="sim-1",
        details={
            "correlation_id": "corr-2",
            "sub_agent": "Comms",
            "timeout_seconds": 30.0,
        },
        aiims_function="public_information",
        secondary_aiims_tags=[],
    )

    payload = envelope.model_dump(mode="json", by_alias=True)
    assert payload["aiims_function"] == "public_information"
    assert payload["secondary_aiims_tags"] == []
    revived = AuditEnvelope.model_validate(payload)
    assert revived.aiims_function == "public_information"


@pytest.mark.asyncio
async def test_audit_writer_propagates_aiims_for_each_sub_agent_entry_type() -> None:
    """All three sub-agent entry types (timeout/cancel/degraded) carry AIIMS."""

    writer = AuditWriter()
    base_kwargs = {
        "simulation_id": "sim-1",
        "aiims_function": "logistics",
        "secondary_aiims_tags": ["operations"],
    }

    timeout = await writer.write(
        "sub_agent.timeout",
        details={
            "correlation_id": "c1",
            "sub_agent": "Resource",
            "timeout_seconds": 5.0,
        },
        **base_kwargs,
    )
    cancel = await writer.write(
        "sub_agent.cancel",
        details={
            "correlation_id": "c2",
            "sub_agent": "Resource",
            "cancellation_reason": "paused_clean_shutdown",
        },
        **base_kwargs,
    )
    degraded = await writer.write(
        "sub_agent.degraded",
        details={
            "correlation_id": "c3",
            "sub_agent": "Resource",
            "degradation_reason": "llm_unavailable",
        },
        **base_kwargs,
    )

    for envelope in (timeout, cancel, degraded):
        assert envelope.aiims_function == "logistics"
        assert envelope.secondary_aiims_tags == ["operations"]


@pytest.mark.asyncio
async def test_audit_writer_rejects_unknown_aiims_function_value() -> None:
    writer = AuditWriter()

    with pytest.raises(ValidationError):
        await writer.write(
            "sub_agent.timeout",
            simulation_id="sim-1",
            details={
                "correlation_id": "corr-x",
                "sub_agent": "Risk",
                "timeout_seconds": 5.0,
            },
            aiims_function="not-a-real-function",  # type: ignore[arg-type]
        )
