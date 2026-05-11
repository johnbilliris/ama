"""T-A06: typed audit-entry detail-payload unit tests."""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from domain.models.telemetry_injection_audit_entry import (
    ALL_ENTRY_TYPES,
    AuditEnvelope,
    AuditSource,
    CascadeDepth2RefusedDetails,
    InjectionRefusedDetails,
    InjectionSuccessDetails,
    SubAgentDegradedDetails,
    SyntheticDeliveryDetails,
    validate_details,
)
from pydantic import ValidationError


def test_all_entry_types_count_24() -> None:
    # Step 8 amendment cycle: 19 → 24 typed entries (lifecycle.refused_while_paused,
    # audit.watermark.applied, audit.sequence.uncertainty, audit.idempotency.replay_cross_user,
    # audit.rbac.unauthorized_attempt). See contracts/audit-envelope.md §6.1.
    assert len(ALL_ENTRY_TYPES) == 24


def test_envelope_round_trip() -> None:
    env = AuditEnvelope(
        id=str(uuid4()),
        _partitionKey="sim-1",
        simulation_id=str(uuid4()),
        sequence_number=1,
        entry_type="injection.success",
        timestamp=datetime.now(UTC),
        source=AuditSource(component="controller_service"),
        details={
            "chat_turn_id": str(uuid4()),
            "injection_correlation_id": str(uuid4()),
            "signal_ids": [str(uuid4())],
            "categories": ["weather"],
            "confidences": ["high"],
        },
    )
    assert env.entry_type == "injection.success"


def test_injection_success_strict_payload_validation() -> None:
    payload = {
        "chat_turn_id": str(uuid4()),
        "injection_correlation_id": str(uuid4()),
        "signal_ids": [str(uuid4())],
        "categories": ["weather"],
        "confidences": ["high"],
        "model_deployment": "gpt-4o-mini-australiaeast",
        "prompt_hash": hashlib.sha256(b"x").hexdigest(),
    }
    parsed = InjectionSuccessDetails.model_validate(payload)
    assert parsed.prompt_hash and parsed.prompt_hash[:6].isalnum()


def test_synthetic_delivery_payload_must_have_sim_msg_id() -> None:
    payload = {
        "channel": "sms",
        "audience": "operations-team",
        "message_id": "wrong-prefix-1234",
        "sim_timestamp": datetime.now(UTC),
        "block_reason": "simulation_tenant_egress_blocked",
        "payload_hash": hashlib.sha256(b"y").hexdigest(),
    }
    with pytest.raises(ValidationError):
        SyntheticDeliveryDetails.model_validate(payload)


def test_cascade_depth2_refused_required_fields() -> None:
    payload = {
        "audit_id": str(uuid4()),
        "simulation_id": str(uuid4()),
        "sequence_number": 7,
        "tenant_id": "sim-1",
        "timestamp_utc": datetime.now(UTC),
        "actor": "cascade_orchestrator",
        "entry_type": "cascade.depth2_refused",
        "attempted_signal_id": str(uuid4()),
        "originating_cascade_id": str(uuid4()),
        "refusal_reason": "depth2_cascade_disallowed",
        "chat_reply_text": "Depth-2 cascade is not allowed; new top-level correlation issued.",
        "new_top_level_correlation_id": str(uuid4()),
    }
    parsed = CascadeDepth2RefusedDetails.model_validate(payload)
    assert parsed.refusal_reason == "depth2_cascade_disallowed"


def test_sub_agent_degraded_reason_constrained() -> None:
    with pytest.raises(ValidationError):
        SubAgentDegradedDetails.model_validate(
            {
                "correlation_id": str(uuid4()),
                "sub_agent": "risk-assessment",
                "degradation_reason": "alien_invasion",
            }
        )


def test_validate_details_dispatch_table_covers_all_24() -> None:
    for et in ALL_ENTRY_TYPES:
        # Just ensure dispatch table entry exists (the per-payload validation
        # is covered by per-class tests above).
        from domain.models.telemetry_injection_audit_entry import DetailsByEntry

        assert et in DetailsByEntry, f"Missing dispatch entry for {et!r}"


def test_validate_details_unknown_entry_type_raises() -> None:
    with pytest.raises(ValueError):
        validate_details("bogus.type", {})


def test_injection_refused_reason_set() -> None:
    InjectionRefusedDetails.model_validate(
        {
            "chat_turn_id": str(uuid4()),
            "reason": "life_safety_low_confidence",
        }
    )
    with pytest.raises(ValidationError):
        InjectionRefusedDetails.model_validate(
            {
                "chat_turn_id": str(uuid4()),
                "reason": "ufo_detected",
            }
        )
