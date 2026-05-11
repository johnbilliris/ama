"""Unit tests for spec-036 T-T02 — augment :class:`SubAgentInvocationRecord`
with ``aiims_function`` + ``secondary_aiims_tags`` fields.

Per data-model.md §8.7 (Amendment A) and constitution v1.2.0 invariants:

* Every record carries exactly **one** primary AIIMS function and at most
  **two** secondary tags (the "1 + ≤2" cap is constitutional, amendment Q→A
  Q4).
* The values are derived from the canonical
  :data:`packages.domain.src.domain.models.aiims_mapping.AGENT_TO_AIIMS`
  table introduced in Wave 1 (T-T01).
* Existing `agent_role` Literal (kebab-case 6-member set) maps deterministically
  to the new PascalCase :data:`SubAgent` Literal via a private bridge.

The Wave 4 test T-T05 (``tests/unit/test_aiims_mapping.py``) covers the
purity invariants of the mapping itself; this Wave 2 test verifies the
**propagation** of those values onto the persisted invocation record.
"""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from pydantic import ValidationError

from packages.domain.src.domain.models.sub_agent_invocation_record import (
    LEGACY_ROLE_TO_SUB_AGENT,
    SubAgentInvocationRecord,
)


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


# ---- Auto-population from agent_role ------------------------------------


def test_aiims_function_auto_derived_for_risk_assessment() -> None:
    """``risk-assessment`` (legacy) → ``Risk`` (canonical) → ``planning``."""

    rec = SubAgentInvocationRecord(**_good())
    assert rec.aiims_function == "planning"


def test_secondary_aiims_tags_auto_derived_for_risk_assessment() -> None:
    """``Risk`` carries the ``intelligence`` secondary tag (T-T01 mapping)."""

    rec = SubAgentInvocationRecord(**_good())
    assert rec.secondary_aiims_tags == ["intelligence"]


@pytest.mark.parametrize(
    ("agent_role", "expected_primary"),
    [
        ("monitoring", "intelligence"),
        ("planning", "planning"),
        ("risk-assessment", "planning"),
        ("communication", "public_information"),
        ("evacuation", "operations"),
        ("resource-allocation", "logistics"),
    ],
)
def test_aiims_function_for_every_legacy_role(
    agent_role: str, expected_primary: str
) -> None:
    """Every legacy ``SubAgentRole`` maps to a canonical AIIMS function."""

    kwargs = _good()
    kwargs["agent_role"] = agent_role
    rec = SubAgentInvocationRecord(**kwargs)
    assert rec.aiims_function == expected_primary


# ---- Constitutional invariant: ≤2 secondary tags ------------------------


def test_secondary_aiims_tags_capped_at_two() -> None:
    """Constitution v1.2.0 / amendment Q→A Q4 — secondary tags ≤ 2."""

    kwargs = _good()
    kwargs["secondary_aiims_tags"] = [
        "operations",
        "logistics",
        "intelligence",  # 3rd tag — must be rejected
    ]
    with pytest.raises(ValidationError):
        SubAgentInvocationRecord(**kwargs)


def test_secondary_aiims_tags_can_be_empty() -> None:
    """Sub-agents with no doctrinal secondary tags can be persisted."""

    kwargs = _good()
    kwargs["secondary_aiims_tags"] = []
    rec = SubAgentInvocationRecord(**kwargs)
    assert rec.secondary_aiims_tags == []


def test_secondary_aiims_tags_must_not_duplicate_primary() -> None:
    """Constitution v1.2.0 — secondary set is disjoint from the primary."""

    kwargs = _good()
    kwargs["aiims_function"] = "planning"
    kwargs["secondary_aiims_tags"] = ["planning"]  # duplicate primary
    with pytest.raises(ValidationError):
        SubAgentInvocationRecord(**kwargs)


# ---- Explicit overrides win over the auto-derived value -----------------


def test_explicit_aiims_function_overrides_default() -> None:
    """An explicit ``aiims_function`` is preserved verbatim."""

    kwargs = _good()
    kwargs["aiims_function"] = "operations"  # not the default for risk-assessment
    rec = SubAgentInvocationRecord(**kwargs)
    assert rec.aiims_function == "operations"


def test_explicit_secondary_aiims_tags_override_default() -> None:
    """An explicit ``secondary_aiims_tags`` value is preserved verbatim."""

    kwargs = _good()
    kwargs["secondary_aiims_tags"] = ["operations"]  # custom subset
    rec = SubAgentInvocationRecord(**kwargs)
    assert rec.secondary_aiims_tags == ["operations"]


# ---- Bridge map between legacy and canonical SubAgent identifiers -------


def test_legacy_role_to_sub_agent_bridge_covers_every_role() -> None:
    """Every legacy ``SubAgentRole`` has a canonical ``SubAgent`` entry."""

    legacy_roles = {
        "monitoring",
        "planning",
        "risk-assessment",
        "communication",
        "evacuation",
        "resource-allocation",
    }
    assert set(LEGACY_ROLE_TO_SUB_AGENT.keys()) == legacy_roles


def test_legacy_role_bridge_targets_are_canonical_sub_agents() -> None:
    """Each bridge target is a member of the spec-036 ``SubAgent`` Literal."""

    from packages.domain.src.domain.models.aiims_mapping import ALL_SUB_AGENTS

    for legacy_role, canonical_sub_agent in LEGACY_ROLE_TO_SUB_AGENT.items():
        assert canonical_sub_agent in ALL_SUB_AGENTS, (
            f"Legacy role {legacy_role!r} maps to {canonical_sub_agent!r}, "
            f"which is not a canonical SubAgent ({ALL_SUB_AGENTS!r})."
        )


# ---- Round-trip serialisation includes the new fields -------------------


def test_model_dump_contains_aiims_fields() -> None:
    """``model_dump()`` round-trips the new fields for Cosmos persistence."""

    rec = SubAgentInvocationRecord(**_good())
    dumped = rec.model_dump(mode="json")
    assert dumped["aiims_function"] == "planning"
    assert dumped["secondary_aiims_tags"] == ["intelligence"]
