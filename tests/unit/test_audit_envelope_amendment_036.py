"""Tests for spec-036 T-O06 / T-O07 — audit envelope amendment-cycle additions.

* T-O06 introduces ``audit.idempotency.replay_cross_user`` — a new typed
  entry per ``contracts/audit-envelope.md §3.14c``.
* T-O07 finalises the T-A06 [AMEND] residual envelope fields on the
  base :class:`AuditEnvelope`: optional top-level
  ``prompt_hash_source``, ``idempotency_key``, ``request_correlation_id``,
  ``delivery_channel`` (additive only — every existing test continues
  to pass without supplying them).
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from apps.api.app.services.simulation.audit_writer import (
    AuditWriter,
    reset_audit_writer_for_tests,
)
from packages.domain.src.domain.models.telemetry_injection_audit_entry import (
    ALL_ENTRY_TYPES,
    AuditEnvelope,
    validate_details,
)


@pytest.fixture(autouse=True)
def _isolate_audit_state() -> None:
    reset_audit_writer_for_tests()
    yield
    reset_audit_writer_for_tests()


# ---- T-O06 audit.idempotency.replay_cross_user typed entry --------------


def test_replay_cross_user_is_in_canonical_entry_type_set() -> None:
    """Per §3.14c the new typed entry MUST be enumerated in ALL_ENTRY_TYPES."""

    assert "audit.idempotency.replay_cross_user" in ALL_ENTRY_TYPES


def test_replay_cross_user_payload_validation_round_trip() -> None:
    payload = {
        "cache_doc_id": "sim-1/POST/route/key-A",
        "cached_rbac_subject_id": "user-A-OID",
        "replay_rbac_subject_id": "user-B-OID",
        "verb": "POST",
        "route": "/api/simulations/sim-1/pause",
    }
    validated = validate_details("audit.idempotency.replay_cross_user", payload)
    dump = validated.model_dump(mode="json")
    assert dump["cache_doc_id"] == "sim-1/POST/route/key-A"
    assert dump["cached_rbac_subject_id"] == "user-A-OID"
    assert dump["replay_rbac_subject_id"] == "user-B-OID"


def test_replay_cross_user_required_fields_enforced() -> None:
    """Missing required fields must surface a ValidationError."""

    with pytest.raises(Exception):
        validate_details(
            "audit.idempotency.replay_cross_user",
            {"cache_doc_id": "x"},
        )


@pytest.mark.asyncio
async def test_audit_writer_persists_replay_cross_user_entry() -> None:
    writer = AuditWriter()
    env = await writer.write(
        "audit.idempotency.replay_cross_user",
        simulation_id="sim-CU",
        details={
            "cache_doc_id": "sim-CU/POST/route/K",
            "cached_rbac_subject_id": "user-A-OID",
            "replay_rbac_subject_id": "user-B-OID",
            "verb": "POST",
            "route": "/api/simulations/sim-CU/pause",
        },
    )
    assert env.entry_type == "audit.idempotency.replay_cross_user"
    assert env.sequence_number == 1


# ---- T-O07 residual T-A06 envelope fields -------------------------------


def _envelope_kwargs(**overrides: object) -> dict[str, object]:
    base = {
        "id": str(uuid4()),
        "_partitionKey": "sim-1",
        "simulation_id": "sim-1",
        "sequence_number": 1,
        "entry_type": "lifecycle.paused",
        "timestamp": datetime.now(UTC),
        "source": {"component": "controller_service"},
        "details": {"attempted_action": "chat_turn"},
    }
    base.update(overrides)
    return base


def test_envelope_accepts_optional_prompt_hash_source() -> None:
    env = AuditEnvelope.model_validate(_envelope_kwargs(prompt_hash_source="canonical_llm_prompt"))
    assert env.prompt_hash_source == "canonical_llm_prompt"


def test_envelope_rejects_invalid_prompt_hash_source() -> None:
    with pytest.raises(Exception):
        AuditEnvelope.model_validate(_envelope_kwargs(prompt_hash_source="not-a-canonical-source"))


def test_envelope_accepts_idempotency_key_and_correlation() -> None:
    env = AuditEnvelope.model_validate(
        _envelope_kwargs(
            idempotency_key="key-O07",
            request_correlation_id=str(uuid4()),
        )
    )
    assert env.idempotency_key == "key-O07"
    assert env.request_correlation_id is not None


def test_envelope_accepts_delivery_channel_enum() -> None:
    env_audio = AuditEnvelope.model_validate(_envelope_kwargs(delivery_channel="audio"))
    env_text = AuditEnvelope.model_validate(_envelope_kwargs(delivery_channel="text-live-log"))
    env_both = AuditEnvelope.model_validate(_envelope_kwargs(delivery_channel="both"))
    assert env_audio.delivery_channel == "audio"
    assert env_text.delivery_channel == "text-live-log"
    assert env_both.delivery_channel == "both"


def test_envelope_rejects_invalid_delivery_channel() -> None:
    with pytest.raises(Exception):
        AuditEnvelope.model_validate(_envelope_kwargs(delivery_channel="email"))


def test_envelope_residual_fields_default_to_none_for_back_compat() -> None:
    """All four residual fields are optional — existing call sites continue to work."""

    env = AuditEnvelope.model_validate(_envelope_kwargs())
    assert env.prompt_hash_source is None
    assert env.idempotency_key is None
    assert env.request_correlation_id is None
    assert env.delivery_channel is None


@pytest.mark.asyncio
async def test_audit_writer_propagates_residual_fields_into_envelope() -> None:
    writer = AuditWriter()
    env = await writer.write(
        "lifecycle.paused",
        simulation_id="sim-residual",
        details={"attempted_action": "chat_turn"},
        idempotency_key="K-residual",
        request_correlation_id=str(uuid4()),
        prompt_hash_source="raw_user_input",
        delivery_channel="text-live-log",
    )
    assert env.idempotency_key == "K-residual"
    assert env.prompt_hash_source == "raw_user_input"
    assert env.delivery_channel == "text-live-log"
    assert env.request_correlation_id is not None
