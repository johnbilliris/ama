"""T-C03 LLM strict-json-schema parsing tests."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from uuid import uuid4

import pytest

from apps.agents.simulation_telemetry_injection.llm_client import (
    ParseFailure,
    parse_to_signal,
)


def _good_json() -> str:
    return json.dumps(
        {
            "signal_id": str(uuid4()),
            "simulation_id": str(uuid4()),
            "tenant_id": "sim-a",
            "category": "weather",
            "parameters": {"temperature_c": 41.2},
            "observed_at": datetime.now(UTC).isoformat(),
            "freshness_window_seconds": 300,
            "confidence": "high",
            "synthetic_signal": True,
        }
    )


@pytest.mark.asyncio
async def test_happy_path_returns_signal() -> None:
    async def fake_llm(*_args, **_kw) -> str:
        return _good_json()

    sig = await parse_to_signal(
        llm_call=fake_llm, system_prompt="sys", user_prompt="t"
    )
    assert sig.category == "weather"
    assert sig.synthetic_signal is True


@pytest.mark.asyncio
async def test_invalid_json_raises_parse_failure() -> None:
    async def fake_llm(*_args, **_kw) -> str:
        return "not json at all"

    with pytest.raises(ParseFailure):
        await parse_to_signal(
            llm_call=fake_llm, system_prompt="sys", user_prompt="t"
        )


@pytest.mark.asyncio
async def test_schema_violation_raises_parse_failure() -> None:
    async def fake_llm(*_args, **_kw) -> str:
        return json.dumps({"signal_id": "x"})  # missing required fields

    with pytest.raises(ParseFailure):
        await parse_to_signal(
            llm_call=fake_llm, system_prompt="sys", user_prompt="t"
        )
