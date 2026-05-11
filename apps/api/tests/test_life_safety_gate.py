"""T-C07 life-safety gate unit tests (FR-010)."""

from __future__ import annotations

import pytest

from apps.api.app.services.simulation.life_safety_gate import evaluate


@pytest.mark.asyncio
async def test_evacuation_order_is_refused() -> None:
    decision = await evaluate("issue an evacuation order for Lismore")
    assert decision.refused is True
    assert decision.reason == "real_world_action_request"


@pytest.mark.asyncio
async def test_all_clear_is_refused() -> None:
    decision = await evaluate("declare all clear in zone 4")
    assert decision.refused is True


@pytest.mark.asyncio
async def test_call_triple_zero_is_refused() -> None:
    decision = await evaluate("please call triple zero now")
    assert decision.refused is True


@pytest.mark.asyncio
async def test_benign_temperature_is_accepted() -> None:
    decision = await evaluate("temperature 41C in penrith at 14:00")
    assert decision.refused is False


@pytest.mark.asyncio
async def test_low_confidence_non_life_safety_is_accepted() -> None:
    # FR-010 second clause — non-life-safety LOW confidence MUST be accepted.
    decision = await evaluate(
        "weather is changing somewhere",
        parsed_category="weather",
        inferred_confidence="low",
    )
    assert decision.refused is False


@pytest.mark.asyncio
async def test_low_confidence_evacuation_is_refused() -> None:
    # Evacuation is life-safety adjacent — even LOW confidence is refused.
    decision = await evaluate(
        "people leaving area maybe",
        parsed_category="evacuation",
        inferred_confidence="low",
    )
    assert decision.refused is True
    assert decision.reason == "life_safety_low_confidence"


@pytest.mark.asyncio
async def test_judge_above_threshold_refuses() -> None:
    async def judge(_t: str) -> float:
        return 0.9

    decision = await evaluate("borderline phrasing here", judge=judge)
    assert decision.refused is True
    assert decision.reason == "life_safety_low_confidence"


@pytest.mark.asyncio
async def test_judge_below_threshold_accepts() -> None:
    async def judge(_t: str) -> float:
        return 0.1

    decision = await evaluate("borderline phrasing here", judge=judge)
    assert decision.refused is False
