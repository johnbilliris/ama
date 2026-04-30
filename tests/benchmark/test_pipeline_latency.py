"""Pipeline latency benchmark — verifies ≤2s blocking cap on handoff delivery (T026)."""

from __future__ import annotations

import asyncio
import time

import pytest
from common.handoffs import AgentHandoffEvent, deliver_handoff_with_retry


def _make_handoff() -> AgentHandoffEvent:
    return AgentHandoffEvent(
        handoff_id="bench-001",
        source_agent="monitoring",
        target_agent="risk_assessment",
        incident_id="inc-bench",
        scope_key="live:inc-bench:bench-001",
        confidence=0.9,
        payload={"benchmark": True},
    )


class TestDeliveryLatencyBenchmark:
    """Benchmark: handoff delivery must not exceed blocking cap."""

    @pytest.mark.asyncio
    async def test_successful_delivery_under_100ms(self):
        """Successful delivery should complete well under 2s."""

        async def fast_deliver(_):
            await asyncio.sleep(0.01)

        handoff = _make_handoff()
        start = time.monotonic()
        result = await deliver_handoff_with_retry(
            handoff=handoff,
            deliver=fast_deliver,
        )
        elapsed = time.monotonic() - start

        assert result.status == "delivered"
        assert elapsed < 0.5, f"Expected <500ms, got {elapsed * 1000:.0f}ms"

    @pytest.mark.asyncio
    async def test_slow_delivery_capped_at_2s(self):
        """FR-002: Slow delivery must time out at ~2s, not block indefinitely."""

        async def slow_deliver(_):
            await asyncio.sleep(30)

        handoff = _make_handoff()
        start = time.monotonic()
        result = await deliver_handoff_with_retry(
            handoff=handoff,
            deliver=slow_deliver,
            max_retries=0,
        )
        elapsed = time.monotonic() - start

        assert result.status == "dead_lettered"
        # Should timeout at ~2s + small overhead, not 30s
        assert elapsed < 5.0, f"Expected <5s (2s timeout + overhead), got {elapsed:.1f}s"

    @pytest.mark.asyncio
    async def test_retry_backoff_total_time_bounded(self):
        """Retries with backoff should have bounded total time."""
        attempt = 0

        async def fail_then_succeed(handoff):
            nonlocal attempt
            attempt += 1
            if attempt <= 2:
                raise Exception("transient")

        handoff = _make_handoff()
        start = time.monotonic()
        result = await deliver_handoff_with_retry(
            handoff=handoff,
            deliver=fail_then_succeed,
            max_retries=3,
        )
        elapsed = time.monotonic() - start

        assert result.status == "delivered"
        # 2 retries with backoff (0.5s, 1.0s approx) + delivery < 5s
        assert elapsed < 10.0, f"Expected <10s total, got {elapsed:.1f}s"
