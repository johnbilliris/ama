import pytest
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
    )

    assert result.status == "delivered"
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
        max_retries=2,
        retry_window_seconds=2,
    )

    assert result.status == "dead_lettered"
    assert result.dead_letter_entry_id == "dlq-123"
