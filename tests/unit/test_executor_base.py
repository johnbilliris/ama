"""Output-schema mismatch + retry-budget tests (T042b, T042c)."""

from __future__ import annotations

import asyncio

import pytest
from pydantic import BaseModel

from apps.agents.maf_runtime.errors import (
    LlmContentFilterError,
    LlmServerError,
    OutputSchemaMismatchError,
)
from apps.agents.maf_runtime.workflow.executors._base import (
    validate_output,
    with_retry_budget,
)


class _Sample(BaseModel):
    name: str
    count: int


def test_validate_output_passes_on_valid_dict() -> None:
    out = validate_output(_Sample, {"name": "x", "count": 3}, correlation_id="c")
    assert isinstance(out, _Sample) and out.count == 3


def test_validate_output_passes_on_already_typed() -> None:
    out = validate_output(_Sample, _Sample(name="x", count=1), correlation_id="c")
    assert out.count == 1


def test_validate_output_raises_on_missing_field() -> None:
    with pytest.raises(OutputSchemaMismatchError) as exc:
        validate_output(_Sample, {"name": "x"}, correlation_id="c", run_id="r")
    assert "count" in exc.value.details["offending_fields"]
    assert exc.value.run_id == "r"


def test_retry_budget_succeeds_after_transient() -> None:
    attempts = {"n": 0}

    async def work() -> str:
        attempts["n"] += 1
        if attempts["n"] < 3:
            raise LlmServerError("flaky", correlation_id="c")
        return "ok"

    result = asyncio.run(with_retry_budget(work, correlation_id="c", sleep_seconds=0.0))
    assert result == "ok"
    assert attempts["n"] == 3


def test_retry_budget_exhausts_then_raises() -> None:
    attempts = {"n": 0}

    async def work() -> None:
        attempts["n"] += 1
        raise LlmServerError("permanent", correlation_id="c")

    with pytest.raises(LlmServerError):
        asyncio.run(with_retry_budget(
            work, correlation_id="c", max_attempts=3, total_seconds=2.0, sleep_seconds=0.01,
        ))
    assert attempts["n"] == 3


def test_non_retryable_fails_immediately() -> None:
    attempts = {"n": 0}

    async def work() -> None:
        attempts["n"] += 1
        raise LlmContentFilterError("blocked", correlation_id="c")

    with pytest.raises(LlmContentFilterError):
        asyncio.run(with_retry_budget(work, correlation_id="c", sleep_seconds=0.0))
    assert attempts["n"] == 1
