"""Phase J — contract test for ALL audit entry types (T-J01).

Asserts that every entry-type literal listed in
``packages.domain.src.domain.models.telemetry_injection_audit_entry.
ALL_ENTRY_TYPES`` has:

1. A Pydantic dispatch class registered in :func:`validate_details`.
2. A round-trip serialisable example payload that exercises the
   schema's required fields.

The matrix below MUST stay in lock-step with
``contracts/audit-envelope.md §3``. Wave 4 grew the catalogue from 19
entries to **24** by adding ``lifecycle.refused_while_paused``,
``audit.watermark.applied``, ``audit.sequence.uncertainty``,
``audit.idempotency.replay_cross_user``, and
``audit.rbac.unauthorized_attempt`` (FS10).
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import pytest

from packages.domain.src.domain.models.telemetry_injection_audit_entry import (
    ALL_ENTRY_TYPES,
    validate_details,
)

# Exemplar payload per audit entry type — every required field present.
EXAMPLES: dict[str, dict[str, Any]] = {
    "injection.attempted": {
        "chat_turn_id": "turn-1",
        "user_id": "alice",
        "original_text_hash": "a" * 64,
        "parse_started_at": datetime.now(UTC),
        "pii_redactions": 0,
    },
    "injection.success": {
        "chat_turn_id": "turn-1",
        "injection_correlation_id": "corr-1",
        "signal_ids": ["sig-1"],
        "categories": ["weather"],
        "confidences": ["medium"],
        "model_deployment": "gpt-4o-australiaeast",
        "prompt_hash": "b" * 64,
    },
    "injection.refused": {
        "chat_turn_id": "turn-1",
        "reason": "life_safety_low_confidence",
    },
    "injection.circuit_open": {
        "user_id": "alice",
        "attempts_in_window": 75,
    },
    "routing.viewport_hint_mismatch": {
        "chat_turn_id": "turn-1",
        "client_hint": "AU-NSW",
        "server_computed": "AU-VIC",
        "viewport_centroid_lat": -37.0,
        "viewport_centroid_lng": 145.0,
        "jurisdiction_dataset_version": "platform-registry-v3",
    },
    "routing.jurisdiction_ambiguous": {
        "chat_turn_id": "turn-1",
        "inference_step_attempted": 4,
        "candidates": ["AU-NSW", "AU-ACT"],
    },
    "routing.ambiguous": {
        "chat_turn_id": "turn-1",
        "candidate_agents": ["planning", "monitoring"],
        "confidences": [0.82, 0.79],
    },
    "cascade.degraded_to_annotation": {
        "origin_cascade_id": "cas-1",
        "triggering_thread_id": "thr-A",
        "target_thread_id": "thr-B",
        "affinity_step": 2,
        "suppressed_proposal": {"thread_id": "thr-new"},
    },
    "cascade.depth2_refused": {
        "audit_id": "aud-1",
        "simulation_id": "sim-1",
        "sequence_number": 5,
        "tenant_id": "tenant-1",
        "timestamp_utc": datetime.now(UTC),
        "actor": "cascade_orchestrator",
        "attempted_signal_id": "sig-2",
        "originating_cascade_id": "cas-1",
        "chat_reply_text": "Depth-2 cascade refused.",
        "new_top_level_correlation_id": "corr-2",
    },
    "thread.cap_exceeded": {
        "proposed_thread": {"id": "thr-new"},
        "rejection_source": "coordinator_injection",
    },
    "lifecycle.paused": {
        "attempted_action": "telemetry_injection",
        "coordinator_user_id": "alice",
    },
    "lifecycle.aborted": {
        "coordinator_user_id": "alice",
        "cancelled_invocations": 3,
        "abort_timestamp": datetime.now(UTC),
        "reason": "drill_end",
    },
    "lifecycle.resumed": {
        "coordinator_user_id": "alice",
        "previous_paused_duration_seconds": 60,
    },
    "audit.watermark.locale_missing": {
        "artefact_id": "art-1",
        "locale": "xx-YY",
        "pathway": "text",
        "fallback_applied": "english_only_text",
    },
    "synthetic-delivery": {
        "channel": "sms",
        "audience": "public",
        "message_id": "sim-msg-abcd",
        "sim_timestamp": datetime.now(UTC),
        "block_reason": "simulation_tenant_egress_blocked",
        "payload_hash": "f" * 64,
    },
    "sub_agent.timeout": {
        "correlation_id": "corr-1",
        "sub_agent": "planning",
        "timeout_seconds": 120.0,
    },
    "sub_agent.cancel": {
        "correlation_id": "corr-1",
        "sub_agent": "planning",
        "cancellation_reason": "aborted",
        "elapsed_ms": 0,
    },
    "sub_agent.degraded": {
        "correlation_id": "corr-1",
        "sub_agent": "monitoring",
        "degradation_reason": "rate_limit_exhausted",
    },
    "tenant_isolation.violation": {
        "violation_kind": "citation_to_live_tenant",
        "offending_resource_id": "res-1",
    },
    # ---- Wave 4 additions (24-entry locked catalogue) ----
    "lifecycle.refused_while_paused": {
        "attempted_action": "chat_turn",
        "coordinator_user_id": "alice",
        "request_correlation_id": "corr-9",
    },
    "audit.watermark.applied": {
        "artefact_id": "art-1",
        "delivery_channel": "both",
        "resolved_locale": "en-AU",
        "watermark_text_hash": "a" * 64,
    },
    "audit.sequence.uncertainty": {
        "original_correlation_id": "corr-1",
        "uncertainty_reason": "etag_exhausted",
        "fallback_audit_envelope": {"id": "audit-x"},
        "queued_at": datetime.now(UTC),
    },
    "audit.idempotency.replay_cross_user": {
        "cache_doc_id": "sim-1/pause/POST/key-1",
        "cached_rbac_subject_id": "alice",
        "replay_rbac_subject_id": "bob",
        "verb": "pause",
        "route": "POST /v1/simulations/{sim_id}/pause",
    },
    "audit.rbac.unauthorized_attempt": {
        "subject": {"user_id": "bob", "tenant_id": "tenant-1"},
        "route": "POST /v1/simulations/{sim_id}/inject-telemetry",
        "requested_role": "coordinator",
        "actual_roles": ["observer"],
        "reason": "missing_role",
        "request_correlation_id": "corr-1",
    },
}


def test_all_entry_types_have_examples() -> None:
    """Regression guard — every entry in ALL_ENTRY_TYPES has a fixture row."""
    missing = [t for t in ALL_ENTRY_TYPES if t not in EXAMPLES]
    assert not missing, f"missing exemplar payloads for: {missing}"


@pytest.mark.parametrize("entry_type", ALL_ENTRY_TYPES)
def test_entry_type_validates_against_dispatch(entry_type: str) -> None:
    """Each entry type's exemplar payload must validate via dispatch."""
    payload = EXAMPLES[entry_type]
    model = validate_details(entry_type, payload)
    # Round-trip — no extra fields drift through.
    dumped = model.model_dump()
    for key in payload.keys():
        assert key in dumped, f"{entry_type}: dumped payload missing required key {key}"


def test_24_audit_entry_types_locked() -> None:
    """The catalogue is locked at exactly 24 types (Wave 4 closing)."""
    # 19 original entries + 5 Wave 4 additions =
    #   lifecycle.refused_while_paused, audit.watermark.applied,
    #   audit.sequence.uncertainty, audit.idempotency.replay_cross_user,
    #   audit.rbac.unauthorized_attempt.
    assert len(ALL_ENTRY_TYPES) == 24
    assert len(set(ALL_ENTRY_TYPES)) == 24
