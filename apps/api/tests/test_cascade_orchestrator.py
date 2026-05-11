"""Phase D — cascade orchestrator tests (T-D02 / T-D12 / FR-043..047, FR-057)."""

from __future__ import annotations

import pytest

from apps.api.app.services.simulation.cascade_orchestrator import (
    fan_out,
    list_fan_out_targets,
    load_rules,
    reset_cache_for_tests,
)
from packages.domain.src.domain.models.synthetic_signal import SyntheticSignal

pytestmark = pytest.mark.asyncio


def _signal(category: str = "weather") -> SyntheticSignal:
    from datetime import UTC, datetime
    from uuid import uuid4

    return SyntheticSignal(
        signal_id=str(uuid4()),
        simulation_id="sim-test",
        tenant_id="tenant-test",
        category=category,
        observed_at=datetime.now(UTC),
        confidence="high",
        freshness_window_seconds=300,
        synthetic_signal=True,
        parameters={"temperature": 41.5},
    )


async def test_load_rules_returns_ladder_and_fan_out_rules() -> None:
    reset_cache_for_tests()
    cfg = load_rules()
    assert cfg.ladder == [
        "jurisdiction_match",
        "hazard_class_match",
        "cascade_origin_thread",
        "most_recent_mutation",
        "thread_creation_ascending",
    ]
    assert cfg.cap == 5
    assert any(r.trigger_category == "weather" for r in cfg.fan_out_rules)


async def test_list_fan_out_targets_for_known_categories() -> None:
    targets = list_fan_out_targets("weather")
    assert "risk-assessment" in targets
    targets = list_fan_out_targets("evacuation")
    assert "communication" in targets


async def test_fan_out_dispatches_per_target() -> None:
    calls: list[tuple[str, str, str]] = []

    async def dispatcher(role: str, prompt: str, correlation_id: str) -> None:
        calls.append((role, prompt, correlation_id))

    result = await fan_out(trigger_signal=_signal("fire-behaviour"), dispatcher=dispatcher)
    assert result.skipped_reason is None
    assert "risk-assessment" in result.triggered
    assert "evacuation" in result.triggered
    # All children share one origin_cascade_id
    assert {c[2] for c in calls} == {result.origin_cascade_id}


async def test_fan_out_skips_when_no_rule_matches() -> None:
    """An orchestrator-injected signal whose category is not in the rules table is skipped."""

    async def dispatcher(*_args: object) -> None:
        raise AssertionError("dispatcher must not be called")

    # Use an empty cascade rules config to force the no-rule branch.
    from apps.api.app.services.simulation.cascade_orchestrator import (
        CascadeRulesConfig,
    )

    empty_cfg = CascadeRulesConfig(ladder=[], cap=5, fan_out_rules=[])
    result = await fan_out(
        trigger_signal=_signal("weather"),
        dispatcher=dispatcher,
        rules=empty_cfg,
    )
    assert result.skipped_reason == "no_matching_rule"
    assert result.triggered == []


async def test_depth2_refused_emits_audit_and_fresh_correlation() -> None:
    """FR-057 / T-D12 — depth-2 cascade is refused and origin_cascade_id is NOT propagated."""
    audit_calls: list[dict[str, object]] = []

    class FakeAuditWriter:
        async def write(self, entry_type: str, **kwargs: object) -> None:
            audit_calls.append({"entry_type": entry_type, **kwargs})

    async def dispatcher(*_args: object) -> None:
        raise AssertionError("dispatcher must not be called for depth-2")

    parent_origin = "parent-origin-cascade-id-XYZ"
    result = await fan_out(
        trigger_signal=_signal("weather"),
        dispatcher=dispatcher,
        parent_origin_cascade_id=parent_origin,
        audit_writer=FakeAuditWriter(),
    )
    assert result.skipped_reason == "depth2_refused"
    assert result.origin_cascade_id != parent_origin
    assert audit_calls and audit_calls[0]["entry_type"] == "cascade.depth2_refused"
    details = audit_calls[0].get("details", {})
    assert details.get("originating_cascade_id") == parent_origin
    assert details.get("new_top_level_correlation_id") == result.origin_cascade_id
    assert details.get("refusal_reason") == "depth2_cascade_disallowed"
