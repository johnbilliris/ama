"""Unit tests for spec-036 T-L05 — subscriber registry mapping signal kinds
to consumer sub-agents.

Per tasks.md §5 (Phase L) and FR-051 (signal pipeline architecture):

* hazard       → {Risk, Evac, Resource, Planning}
* resource     → {Resource, Logistics}
* channel-state → {Comms}

The registry is a pure function (DI-overridable for tests).
"""

from __future__ import annotations

import pytest

from apps.api.app.services.simulation.subscriber_registry import (
    SignalKind,
    subscribers_for,
)


def test_hazard_signal_fans_out_to_four_sub_agents() -> None:
    """Per FR-051 / Phase L spec — hazard cascades into Risk/Evac/Resource/Planning."""

    assert subscribers_for("hazard") == {"Risk", "Evac", "Resource", "Planning"}


def test_resource_signal_fans_out_to_resource_and_logistics() -> None:
    assert subscribers_for("resource") == {"Resource", "Logistics"}


def test_channel_state_signal_only_engages_comms() -> None:
    assert subscribers_for("channel-state") == {"Comms"}


def test_subscribers_for_returns_a_frozen_set_copy() -> None:
    """Callers must not be able to mutate the registry from the result."""

    first = subscribers_for("hazard")
    first.add("Health")  # if this leaked back, the next call would too
    second = subscribers_for("hazard")
    assert "Health" not in second


def test_subscribers_for_unknown_kind_raises_value_error() -> None:
    with pytest.raises((ValueError, KeyError)):
        subscribers_for("unknown-kind")  # type: ignore[arg-type]


def test_signal_kind_literal_covers_three_documented_kinds() -> None:
    """Documents the closed set so future additions need an explicit task."""

    from typing import get_args

    assert set(get_args(SignalKind)) == {"hazard", "resource", "channel-state"}


def test_every_subscriber_is_a_canonical_sub_agent() -> None:
    """Subscribers must be members of the spec-036 9-member SubAgent Literal."""

    from packages.domain.src.domain.models.aiims_mapping import ALL_SUB_AGENTS

    canonical = set(ALL_SUB_AGENTS)
    for kind in ("hazard", "resource", "channel-state"):
        for subscriber in subscribers_for(kind):
            assert subscriber in canonical, f"{subscriber!r} (in {kind!r} fan-out) is not a canonical SubAgent"
