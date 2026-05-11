"""T-A02: SubAgentInvocationRecord model unit tests (FR-060)."""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from domain.models.sub_agent_invocation_record import (
    SubAgentInvocationRecord,
)
from pydantic import ValidationError


def _good() -> dict[str, object]:
    started = datetime.now(UTC)
    return {
        "invocation_id": str(uuid4()),
        "simulation_id": str(uuid4()),
        "tenant_id": "sim-tenant-a",
        "agent_role": "risk-assessment",
        "prompt_hash": hashlib.sha256(b"test").hexdigest(),
        "model_deployment": "gpt-4o-australiaeast",
        "latency_ms": 432,
        "outcome": "success",
        "started_at": started,
        "ended_at": started + timedelta(milliseconds=432),
    }


def test_sub_agent_invocation_record_happy() -> None:
    rec = SubAgentInvocationRecord(**_good())
    assert rec.partition_key == rec.simulation_id
    assert rec.document_type == "sub_agent_invocation_record"


def test_sub_agent_invocation_record_prompt_hash_must_be_sha256_hex() -> None:
    bad = _good()
    bad["prompt_hash"] = "not-a-hex"
    with pytest.raises(ValidationError):
        SubAgentInvocationRecord(**bad)


def test_sub_agent_invocation_record_canonical_role_set() -> None:
    for role in (
        "monitoring",
        "planning",
        "risk-assessment",
        "communication",
        "evacuation",
        "resource-allocation",
    ):
        kwargs = _good()
        kwargs["agent_role"] = role
        SubAgentInvocationRecord(**kwargs)
