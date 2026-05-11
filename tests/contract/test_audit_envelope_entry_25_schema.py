"""Wave A / T-AA09 — entry-25 ``signal_pipeline.dispatch_failed`` envelope test.

Asserts that:

1. The 25th audit ``entry_type`` is registered in
   :data:`packages.domain.src.domain.models.telemetry_injection_audit_entry.ALL_ENTRY_TYPES`.
2. The Pydantic dispatch class
   ``SignalPipelineDispatchFailedDetails`` is registered in
   ``DetailsByEntry``.
3. ``write_dispatch_failed`` produces an envelope with the audit-envelope.md
   §3.25 payload (byte-equal to the response body's `triggered_sub_agents`
   array per CHK135).

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
"""

from __future__ import annotations

import asyncio
import json
from uuid import UUID

from apps.api.app.services.simulation.audit_writer import (
    AuditWriter,
    canonicalise_triggered_sub_agents,
    reset_audit_writer_for_tests,
    write_dispatch_failed,
)
from apps.api.app.services.simulation.dispatch_status import TriggeredSubAgent
from packages.domain.src.domain.models.telemetry_injection_audit_entry import (
    ALL_ENTRY_TYPES,
    DetailsByEntry,
    SignalPipelineDispatchFailedDetails,
)


def test_entry_25_registered_in_all_entry_types() -> None:
    assert "signal_pipeline.dispatch_failed" in ALL_ENTRY_TYPES, "Cycle 2 entry-25 MUST be in ALL_ENTRY_TYPES."
    # Cycle 3 / T-AA26 / FR-071 — the typed-entry counter advances to 26
    # with the addition of `staging_promotion.refused`. Cycle 2's
    # entry-25 (`signal_pipeline.dispatch_failed`) remains registered
    # — the assertion below pins the cumulative envelope count.
    assert len(ALL_ENTRY_TYPES) == 26, (
        f"ALL_ENTRY_TYPES MUST have exactly 26 entries (got {len(ALL_ENTRY_TYPES)}); "
        "entry-25 is `signal_pipeline.dispatch_failed` per Cycle 2 / FR-067; "
        "entry-26 is `staging_promotion.refused` per Cycle 3 / FR-071."
    )


def test_entry_25_registered_in_dispatch_table() -> None:
    cls = DetailsByEntry.get("signal_pipeline.dispatch_failed")
    assert cls is SignalPipelineDispatchFailedDetails, (
        "DetailsByEntry MUST map `signal_pipeline.dispatch_failed` -> `SignalPipelineDispatchFailedDetails`."
    )


def test_signal_pipeline_dispatch_failed_details_required_fields() -> None:
    """Pydantic schema mirrors audit-envelope.md §3.25 + pass 2 Q1/Q2 invariants."""

    fields = SignalPipelineDispatchFailedDetails.model_fields
    expected = {
        "injection_correlation_id",
        "exception_class",
        "exception_message",
        "triggered_sub_agents",
        "partial_successful_subset",
        "failed_subscriber_list",
        "prompt_hash",
        "prompt_hash_source",
        "degraded_dispatch_flag",
        "dispatch_ack_timeout_seconds",
        "idempotency_key",
        "request_correlation_id",
    }
    assert set(fields.keys()) == expected, (
        f"SignalPipelineDispatchFailedDetails.model_fields MUST match the "
        f"audit-envelope.md §3.25 contract (got {set(fields.keys())})."
    )

    instance = SignalPipelineDispatchFailedDetails(
        injection_correlation_id="00000000-0000-0000-0000-000000000001",
        exception_class="OrchestratorTimeout",
        exception_message="dispatch timed out after 5s",
        triggered_sub_agents=[
            {
                "correlation_id": "00000000-0000-0000-0000-000000000010",
                "dispatch_status": "timed_out",
                "sub_agent": "Resource",
                "trigger_source": "primary",
            }
        ],
        partial_successful_subset=[],
        failed_subscriber_list=["Resource"],
        prompt_hash="a" * 64,
        prompt_hash_source="raw_user_input",
        request_correlation_id="00000000-0000-0000-0000-000000000002",
    )
    assert instance.degraded_dispatch_flag is True
    assert instance.dispatch_ack_timeout_seconds == 5.0


def test_write_dispatch_failed_round_trip() -> None:
    reset_audit_writer_for_tests()
    writer = AuditWriter(cosmos_container=None)

    e1 = TriggeredSubAgent(
        sub_agent="Comms",
        trigger_source="primary",
        correlation_id=UUID("00000000-0000-0000-0000-000000000010"),
        dispatch_status="failed",
    )
    e2 = TriggeredSubAgent(
        sub_agent="Resource",
        trigger_source="primary",
        correlation_id=UUID("00000000-0000-0000-0000-000000000011"),
        dispatch_status="acknowledged",
    )

    envelope = asyncio.run(
        write_dispatch_failed(
            writer,
            simulation_id="sim-123",
            injection_correlation_id="00000000-0000-0000-0000-000000000001",
            exception_class="OrchestratorTimeout",
            exception_message="dispatch failed: synthetic",
            triggered_sub_agents=[e1, e2],
            prompt_hash="b" * 64,
            prompt_hash_source="raw_user_input",
            idempotency_key=None,
            request_correlation_id="00000000-0000-0000-0000-000000000002",
        )
    )

    assert envelope.entry_type == "signal_pipeline.dispatch_failed"
    details = envelope.details
    # Lex-sort by sub_agent — Comms < Resource.
    sub_agents = [item["sub_agent"] for item in details["triggered_sub_agents"]]
    assert sub_agents == ["Comms", "Resource"], (
        "Cycle 2 pass 1 Q4 — triggered_sub_agents MUST be lex-sorted by "
        "sub_agent PascalCase for byte-equality with response body."
    )
    assert details["partial_successful_subset"] == ["Resource"]
    assert details["failed_subscriber_list"] == ["Comms"]
    assert details["degraded_dispatch_flag"] is True
    assert details["dispatch_ack_timeout_seconds"] == 5.0


def test_write_dispatch_failed_byte_equality_canonical_with_body() -> None:
    """CHK135 — JCS-canonical body and audit array are byte-equal."""

    reset_audit_writer_for_tests()
    writer = AuditWriter(cosmos_container=None)

    body = [
        TriggeredSubAgent(
            sub_agent="Resource",
            trigger_source="primary",
            correlation_id=UUID("00000000-0000-0000-0000-000000000011"),
            dispatch_status="acknowledged",
        ),
        TriggeredSubAgent(
            sub_agent="Comms",
            trigger_source="primary",
            correlation_id=UUID("00000000-0000-0000-0000-000000000010"),
            dispatch_status="failed",
        ),
    ]
    body_canonical = canonicalise_triggered_sub_agents(body)

    envelope = asyncio.run(
        write_dispatch_failed(
            writer,
            simulation_id="sim-123",
            injection_correlation_id="00000000-0000-0000-0000-000000000001",
            exception_class="OrchestratorTimeout",
            exception_message="dispatch failed",
            triggered_sub_agents=body,
            prompt_hash="b" * 64,
            prompt_hash_source="raw_user_input",
            idempotency_key=None,
            request_correlation_id="00000000-0000-0000-0000-000000000002",
        )
    )

    audit_canonical = envelope.details["triggered_sub_agents"]
    assert json.dumps(body_canonical, sort_keys=True) == json.dumps(audit_canonical, sort_keys=True), (
        "CHK135 — HTTP 202 body's triggered_sub_agents MUST be byte-equal "
        "(after RFC 8785 JCS canonicalisation) to the audit envelope's array."
    )
