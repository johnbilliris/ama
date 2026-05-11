"""Unit tests for spec-036 T-T01 — AIIMS sub-agent mapping (FR-061).

The static table ``AGENT_TO_AIIMS`` and helper ``secondary_aiims_tags`` live
under ``packages/domain/src/domain/models/aiims_mapping.py``. The 9 sub-agents
(Risk, Evac, Resource, Logistics, Comms, Planning, Health, Operations, Intel)
each map to a primary AIIMS function (per Q4 of the amendment Q→A: single
primary + ≤2 secondary tags). Every secondary tag MUST be a valid
``AiimsFunction`` and ≤2 entries (constitutional invariant).

Acceptance criteria from tasks.md §13 T-T01 + T-T05:
- Every ``SubAgent`` has a primary mapping.
- Every ``AiimsFunction`` is reachable from at least one sub-agent
  (cohort-review safeguard so AAR ordering never silently drops a function).
- Secondary tags are a subset of the full ``AiimsFunction`` enum, with
  ≤2 entries per sub-agent (constitution v1.2.0).
"""

from __future__ import annotations

import pytest

from packages.domain.src.domain.models.aiims_mapping import (
    AGENT_TO_AIIMS,
    ALL_SUB_AGENTS,
    SubAgent,
    secondary_aiims_tags,
)
from packages.domain.src.domain.models.aiims_role_assignment import (
    ALL_AIIMS_FUNCTIONS,
)


def test_all_nine_sub_agents_present() -> None:
    """The closed-set of sub-agents matches the spec-036 amendment list of 9."""

    expected = {
        "Risk",
        "Evac",
        "Resource",
        "Logistics",
        "Comms",
        "Planning",
        "Health",
        "Operations",
        "Intel",
    }
    assert set(ALL_SUB_AGENTS) == expected
    assert set(AGENT_TO_AIIMS.keys()) == expected


def test_every_sub_agent_has_primary_mapping() -> None:
    """Every sub-agent is keyed in AGENT_TO_AIIMS (T-T01 acceptance #1)."""

    for sa in ALL_SUB_AGENTS:
        assert sa in AGENT_TO_AIIMS, f"sub-agent {sa!r} missing AIIMS primary"
        primary = AGENT_TO_AIIMS[sa]
        assert primary in ALL_AIIMS_FUNCTIONS, f"sub-agent {sa!r} maps to non-AIIMS function {primary!r}"


#: AIIMS doctrine: the Control function is held by the human Incident
#: Controller. No sub-agent ever assumes IC, so ``control`` is excluded
#: from the reachability invariant. T-T05 acceptance is therefore "every
#: *non-control* AiimsFunction is reachable from at least one sub-agent".
_HUMAN_ONLY_AIIMS_FUNCTIONS: frozenset[str] = frozenset({"control"})


def test_every_non_control_aiims_function_reachable() -> None:
    """Every non-IC AIIMS function is reachable (T-T05 invariant #2)."""

    reachable = set(AGENT_TO_AIIMS.values())
    for fn in ALL_AIIMS_FUNCTIONS:
        if fn in _HUMAN_ONLY_AIIMS_FUNCTIONS:
            # IC is human-only by AIIMS doctrine — see _HUMAN_ONLY_AIIMS_FUNCTIONS.
            continue
        # Either it's a primary, or it's referenced as a secondary tag.
        if fn in reachable:
            continue
        if any(fn in secondary_aiims_tags(sa) for sa in ALL_SUB_AGENTS):
            continue
        pytest.fail(f"AIIMS function {fn!r} is not reachable from any sub-agent")


def test_no_sub_agent_assumes_control_function() -> None:
    """AIIMS doctrine: no sub-agent may map to or tag the IC (control)."""

    for sa in ALL_SUB_AGENTS:
        primary = AGENT_TO_AIIMS[sa]
        assert primary != "control", (
            f"sub-agent {sa!r} cannot have AIIMS Control as primary — that role belongs to the human IC"
        )
        assert "control" not in secondary_aiims_tags(sa), (
            f"sub-agent {sa!r} cannot tag AIIMS Control as secondary — that role belongs to the human IC"
        )


def test_secondary_tags_subset_of_aiims_enum() -> None:
    """Every secondary tag is a valid AIIMS function (T-T05 invariant #3)."""

    for sa in ALL_SUB_AGENTS:
        tags = secondary_aiims_tags(sa)
        assert isinstance(tags, list), "secondary_aiims_tags must return a list"
        for tag in tags:
            assert tag in ALL_AIIMS_FUNCTIONS, f"sub-agent {sa!r} has invalid secondary tag {tag!r}"


def test_secondary_tags_capped_at_two_per_constitution() -> None:
    """Constitution v1.2.0 caps AIIMS tags to 1 primary + max 2 secondary."""

    for sa in ALL_SUB_AGENTS:
        tags = secondary_aiims_tags(sa)
        assert len(tags) <= 2, (
            f"sub-agent {sa!r} exceeds constitution v1.2.0 cap of 2 secondary tags (actual: {len(tags)} -> {tags})"
        )


def test_secondary_tags_exclude_primary() -> None:
    """A sub-agent's secondary tags must not duplicate its primary tag."""

    for sa in ALL_SUB_AGENTS:
        primary = AGENT_TO_AIIMS[sa]
        tags = secondary_aiims_tags(sa)
        assert primary not in tags, f"sub-agent {sa!r} duplicates primary {primary!r} in secondary tags"


def test_secondary_tags_unique_per_sub_agent() -> None:
    """Secondary tags within a single sub-agent must be unique."""

    for sa in ALL_SUB_AGENTS:
        tags = secondary_aiims_tags(sa)
        assert len(tags) == len(set(tags)), f"sub-agent {sa!r} has duplicate secondary tags: {tags}"


def test_secondary_aiims_tags_unknown_sub_agent_returns_empty() -> None:
    """Unknown sub-agents return ``[]`` rather than raising (graceful degradation)."""

    assert secondary_aiims_tags("NotARealAgent") == []  # type: ignore[arg-type]


def test_sub_agent_literal_alignment() -> None:
    """``SubAgent`` Literal type stays aligned with ``ALL_SUB_AGENTS`` tuple."""

    # Use ``typing.get_args`` so the test reflects the type definition rather
    # than a hand-maintained constant.
    from typing import get_args

    assert set(get_args(SubAgent)) == set(ALL_SUB_AGENTS)
