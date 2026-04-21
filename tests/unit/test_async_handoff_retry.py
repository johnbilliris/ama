"""Tests for async handoff retry with 2-second blocking cap (T012).

Covers:
- Successful delivery on first attempt
- Retry with exponential backoff
- Dead-letter after max retries
- 2-second timeout per delivery attempt (FR-002)
- Structured telemetry logging
"""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from common.handoffs import (
    AgentHandoffEvent,
    deliver_handoff_with_retry,
)


def _make_handoff(**overrides) -> AgentHandoffEvent:
    defaults = {
        "handoff_id": "hoff-001",
        "source_agent": "monitoring",
        "target_agent": "risk_assessment",
        "incident_id": "inc-001",
        "scope_key": "test",
        "confidence": 0.9,
        "payload": {"test": True},
    }
    defaults.update(overrides)
    return AgentHandoffEvent(**defaults)
    return AgentHandoffEvent(**defaults)


class TestDeliverHandoffWithRetry:
    """Tests for deliver_handoff_with_retry()."""

    @pytest.mark.asyncio
    async def test_successful_first_attempt(self):
        """Delivery succeeds on first try — no retries."""
        deliver = AsyncMock()
        handoff = _make_handoff()

        result = await deliver_handoff_with_retry(handoff=handoff, deliver=deliver)

        assert result.status == "delivered"
        assert result.retry_count == 0
        deliver.assert_awaited_once_with(handoff)

    @pytest.mark.asyncio
    async def test_retry_then_succeed(self):
        """Delivery fails once then succeeds on retry."""
        deliver = AsyncMock(side_effect=[Exception("transient"), None])
        handoff = _make_handoff()

        result = await deliver_handoff_with_retry(
            handoff=handoff, deliver=deliver, max_retries=3,
        )

        assert result.status == "delivered"
        assert result.retry_count == 1

    @pytest.mark.asyncio
    async def test_dead_letter_after_max_retries(self):
        """All retries exhausted → dead_lettered status."""
        deliver = AsyncMock(side_effect=Exception("permanent failure"))
        on_dead_letter = MagicMock(return_value="dl-001")
        handoff = _make_handoff()

        result = await deliver_handoff_with_retry(
            handoff=handoff,
            deliver=deliver,
            max_retries=2,
            on_dead_letter=on_dead_letter,
        )

        assert result.status == "dead_lettered"
        assert result.retry_count == 2
        on_dead_letter.assert_called_once()

    @pytest.mark.asyncio
    async def test_two_second_timeout(self):
        """FR-002: Each delivery attempt has a 2-second blocking cap."""
        async def slow_deliver(_):
            await asyncio.sleep(10)  # Would block for 10s without timeout

        handoff = _make_handoff()

        result = await deliver_handoff_with_retry(
            handoff=handoff,
            deliver=slow_deliver,
            max_retries=1,
        )

        # Should fail due to timeout, not wait 10s
        assert result.status == "dead_lettered"

    @pytest.mark.asyncio
    async def test_structured_telemetry_on_success(self, caplog):
        """Verify structured telemetry log on successful delivery."""
        deliver = AsyncMock()
        handoff = _make_handoff()

        with caplog.at_level("INFO"):
            await deliver_handoff_with_retry(handoff=handoff, deliver=deliver)

        assert any("handoff_delivered" in r.message for r in caplog.records)

    @pytest.mark.asyncio
    async def test_structured_telemetry_on_retry(self, caplog):
        """Verify structured telemetry log on retry."""
        deliver = AsyncMock(side_effect=[Exception("fail"), None])
        handoff = _make_handoff()

        with caplog.at_level("WARNING"):
            await deliver_handoff_with_retry(
                handoff=handoff, deliver=deliver, max_retries=3,
            )

        assert any("handoff_retry" in r.message for r in caplog.records)

    @pytest.mark.asyncio
    async def test_no_dead_letter_callback_if_none(self):
        """Dead-letter works even without a callback."""
        deliver = AsyncMock(side_effect=Exception("fail"))
        handoff = _make_handoff()

        result = await deliver_handoff_with_retry(
            handoff=handoff, deliver=deliver, max_retries=1,
        )

        assert result.status == "dead_lettered"
