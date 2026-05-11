"""T-A04: RoutingDecision unit tests (FR-021)."""

from __future__ import annotations

from uuid import uuid4

import pytest
from domain.models.routing_decision import RoutingDecision
from pydantic import ValidationError


def _kwargs(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "decision_id": str(uuid4()),
        "simulation_id": str(uuid4()),
        "tenant_id": "sim-tenant-a",
        "steps_attempted": ["explicit_payload"],
        "final_jurisdiction_code": "AU-NSW",
        "confidence": "high",
    }
    base.update(overrides)
    return base


def test_routing_decision_happy() -> None:
    d = RoutingDecision(**_kwargs())
    assert d.partition_key == d.simulation_id
    assert d.viewport_hint_used is False


def test_routing_decision_steps_constrained() -> None:
    with pytest.raises(ValidationError):
        RoutingDecision(**_kwargs(steps_attempted=["unknown_step"]))


def test_routing_decision_confidence_constrained() -> None:
    with pytest.raises(ValidationError):
        RoutingDecision(**_kwargs(confidence="psychic"))
