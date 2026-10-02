import asyncio

import pytest

from apps.agents.common.circuit_breaker import CircuitBreaker
from apps.agents.common.handoffs import build_handoff, deliver_handoff_with_retry


@pytest.mark.asyncio
async def test_handoff_retry_then_delivery() -> None:
    handoff = build_handoff(
        incident_id="incident-retry-1",
        source_agent="monitoring",
        target_agent="risk_assessment",
        scope_key="incident-retry-1",
        payload={"signal": "sig-1"},
        confidence=0.9,
    )

    attempts = {"count": 0}

    class _Clock:
        def __init__(self) -> None:
            self.now = 0.0

        def monotonic(self) -> float:
            return self.now

        async def sleep(self, seconds: float) -> None:
            self.now += seconds

    fake_clock = _Clock()

    async def flaky_deliver(_):
        attempts["count"] += 1
        if attempts["count"] < 2:
            raise RuntimeError("temporary unavailable")

    def dead_letter(_):
        return "dlq-not-used"

    result = await deliver_handoff_with_retry(
        handoff=handoff,
        deliver=flaky_deliver,
        on_dead_letter=dead_letter,
        max_retries=3,
        retry_window_seconds=3,
        clock=fake_clock.monotonic,
        sleep_func=fake_clock.sleep,
    )

    assert result.status == "delivered"
    assert result.attempt_count == 2
    assert result.retry_count == 1


@pytest.mark.asyncio
async def test_handoff_dead_letter_after_exhaustion() -> None:
    handoff = build_handoff(
        incident_id="incident-retry-2",
        source_agent="monitoring",
        target_agent="risk_assessment",
        scope_key="incident-retry-2",
        payload={"signal": "sig-2"},
        confidence=0.9,
    )

    async def fail_deliver(_):
        raise RuntimeError("permanent failure")

    def dead_letter(_):
        return "dlq-123"

    result = await deliver_handoff_with_retry(
        handoff=handoff,
        deliver=fail_deliver,
        on_dead_letter=dead_letter,
        max_retries=3,
        retry_window_seconds=2,
    )

    assert result.status == "dead_lettered"
    assert result.attempt_count == 3
    assert result.retry_count == 2
    assert result.dead_letter_entry_id == "dlq-123"


@pytest.mark.asyncio
async def test_handoff_open_circuit_skips_delivery_and_dead_letters() -> None:
    handoff = build_handoff(
        incident_id="incident-retry-3",
        source_agent="monitoring",
        target_agent="risk_assessment",
        scope_key="incident-retry-3",
        payload={"signal": "sig-3"},
        confidence=0.9,
    )

    class _Clock:
        def __init__(self) -> None:
            self.now = 0.0

        def monotonic(self) -> float:
            return self.now

        async def sleep(self, seconds: float) -> None:
            self.now += seconds

    fake_clock = _Clock()
    circuit = CircuitBreaker(failure_threshold=1, recovery_timeout=300, clock=fake_clock.monotonic)
    circuit.record_failure()
    deliver_calls = {"count": 0}

    async def deliver(_):
        deliver_calls["count"] += 1

    result = await deliver_handoff_with_retry(
        handoff=handoff,
        deliver=deliver,
        on_dead_letter=lambda _: "dlq-open-circuit",
        max_retries=3,
        retry_window_seconds=2,
        circuit_breaker=circuit,
        clock=fake_clock.monotonic,
        sleep_func=fake_clock.sleep,
    )

    assert result.status == "dead_lettered"
    assert result.dead_letter_entry_id == "dlq-open-circuit"
    assert result.attempt_count == 3
    assert result.retry_count == 2
    assert deliver_calls["count"] == 0


@pytest.mark.asyncio
async def test_handoff_retry_respects_monotonic_deadline() -> None:
    handoff = build_handoff(
        incident_id="incident-retry-4",
        source_agent="monitoring",
        target_agent="risk_assessment",
        scope_key="incident-retry-4",
        payload={"signal": "sig-4"},
        confidence=0.9,
    )

    class _Clock:
        def __init__(self) -> None:
            self.now = 0.0

        def monotonic(self) -> float:
            return self.now

        async def sleep(self, seconds: float) -> None:
            self.now += seconds

    fake_clock = _Clock()
    sleeps: list[float] = []

    async def record_sleep(seconds: float) -> None:
        sleeps.append(seconds)
        await fake_clock.sleep(seconds)

    async def fail_deliver(_):
        raise RuntimeError("still failing")

    result = await deliver_handoff_with_retry(
        handoff=handoff,
        deliver=fail_deliver,
        on_dead_letter=lambda _: "dlq-deadline",
        max_retries=3,
        retry_window_seconds=0.6,
        clock=fake_clock.monotonic,
        sleep_func=record_sleep,
    )

    assert result.status == "dead_lettered"
    assert result.dead_letter_entry_id == "dlq-deadline"
    assert result.attempt_count == 3
    assert result.retry_count == 2
    assert sleeps[0] == pytest.approx(0.5, abs=0.01)
    assert sleeps[1] == pytest.approx(0.1, abs=0.02)


@pytest.mark.asyncio
async def test_handoff_duplicate_concurrent_delivery_is_idempotent() -> None:
    one = build_handoff(
        incident_id="incident-retry-5",
        source_agent="monitoring",
        target_agent="risk_assessment",
        scope_key="incident-retry-5",
        payload={"signal": "sig-5"},
        confidence=0.9,
        tenant_id="live",
    )
    two = build_handoff(
        incident_id="incident-retry-5",
        source_agent="monitoring",
        target_agent="risk_assessment",
        scope_key="incident-retry-5",
        payload={"signal": "sig-5"},
        confidence=0.9,
        tenant_id="live",
    )
    two.handoff_id = one.handoff_id

    calls = {"count": 0}
    first_started = asyncio.Event()

    async def deliver(_):
        calls["count"] += 1
        first_started.set()
        await asyncio.sleep(0.02)

    first, second = await asyncio.gather(
        deliver_handoff_with_retry(handoff=one, deliver=deliver, max_retries=3),
        deliver_handoff_with_retry(handoff=two, deliver=deliver, max_retries=3),
    )

    assert first.status == "delivered"
    assert second.status == "delivered"
    assert calls["count"] == 1
