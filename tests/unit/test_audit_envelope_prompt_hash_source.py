"""Spec-036 Wave 4 — T-AA02 ``prompt_hash_source`` enum enforcement.

Per FR-065 / Q18 the ``prompt_hash_source`` envelope field MUST be one
of the canonical values:

* ``raw_user_input`` — SHA-256 of raw chat text bytes.
* ``canonical_llm_prompt`` — SHA-256 of the canonical assembled prompt.
* ``system_only`` — SHA-256 of the system-prompt bytes.

The Pydantic v2 ``AuditEnvelope`` model rejects any other value with a
``ValidationError`` (closed-set Literal). This module pins that
behaviour so the schema cannot regress to a free-string field.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from packages.domain.src.domain.models.telemetry_injection_audit_entry import (
    AuditEnvelope,
    AuditSource,
    PromptHashSource,
)

SIM_ID = "11111111-2222-3333-4444-aaaaaaaaaaaa"


def _envelope(prompt_hash_source: str | None) -> AuditEnvelope:
    return AuditEnvelope(
        id=f"audit-{uuid4()}",
        _partitionKey=SIM_ID,
        simulation_id=SIM_ID,
        sequence_number=1,
        entry_type="lifecycle.paused",
        timestamp=datetime.now(UTC),
        source=AuditSource(component="lifecycle_endpoint"),
        details={"attempted_action": "chat_turn", "coordinator_user_id": "coord-1"},
        prompt_hash_source=prompt_hash_source,
    )


@pytest.mark.parametrize("value", ["raw_user_input", "canonical_llm_prompt", "system_only", None])
def test_accepts_canonical_values(value: str | None) -> None:
    envelope = _envelope(value)
    assert envelope.prompt_hash_source == value


@pytest.mark.parametrize(
    "bad",
    [
        "RAW_USER_INPUT",  # uppercase rejected
        "user_input",  # legacy alias rejected
        "system",  # truncated rejected
        "system_prompt",  # synonym rejected
        "",  # empty rejected
    ],
)
def test_rejects_legacy_and_unknown_values(bad: str) -> None:
    with pytest.raises(ValidationError):
        _envelope(bad)


def test_prompt_hash_source_literal_is_a_closed_set() -> None:
    """Sanity check — the closed set has exactly 3 members."""

    from typing import get_args

    members = get_args(PromptHashSource)
    assert set(members) == {"raw_user_input", "canonical_llm_prompt", "system_only"}
    assert len(members) == 3
