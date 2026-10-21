from app.middleware.resilience import TransientDependencyError, retry_transient_dependency_call
from app.services.dead_letter_service import DeadLetterService
from app.services.state_store import DEAD_LETTERS, reset_state

from apps.agents.common.handoffs import build_handoff, deliver_handoff_with_retry


class _RetryableCosmosError(Exception):
    def __init__(self, status_code: int):
        super().__init__(f"status {status_code}")
        self.status_code = status_code


class _NonRetryableCosmosError(Exception):
    def __init__(self, status_code: int):
        super().__init__(f"status {status_code}")
        self.status_code = status_code


def test_retry_succeeds_after_transient_failures() -> None:
    attempts = {"count": 0}

    @retry_transient_dependency_call
    def flaky_call() -> str:
        attempts["count"] += 1
        if attempts["count"] < 3:
            raise TransientDependencyError("temporary issue")
        return "ok"

    assert flaky_call() == "ok"
    assert attempts["count"] == 3


def test_retry_classifies_retryable_status_codes() -> None:
    attempts = {"count": 0}

    @retry_transient_dependency_call
    def flaky_call() -> str:
        attempts["count"] += 1
        if attempts["count"] < 3:
            raise _RetryableCosmosError(status_code=503)
        return "ok"

    assert flaky_call() == "ok"
    assert attempts["count"] == 3


def test_retry_does_not_retry_non_transient_status() -> None:
    attempts = {"count": 0}

    @retry_transient_dependency_call
    def non_retryable_call() -> None:
        attempts["count"] += 1
        raise _NonRetryableCosmosError(status_code=400)

    try:
        non_retryable_call()
    except _NonRetryableCosmosError:
        pass
    else:
        raise AssertionError("non-retryable exception should propagate")
    assert attempts["count"] == 1


def test_dead_letter_created_on_permanent_failure() -> None:
    reset_state()

    handoff = build_handoff(
        incident_id="incident-dlq-1",
        source_agent="monitoring",
        target_agent="risk_assessment",
        scope_key="live",
        payload={"signalId": "sig-1"},
        confidence=0.8,
    )

    async def _always_fail(_):
        raise RuntimeError("permanent failure")

    def _persist_dead_letter(h):
        entry = DeadLetterService().create_entry(
            entry_type="handoff_failure",
            correlation_id=f"handoff:{h.handoff_id}",
            original_payload=h.model_dump(mode="json"),
            failure_reason=h.failure_reason or "permanent failure",
            failure_code="MAX_RETRIES_EXCEEDED",
            source_service=h.source_agent,
            target_service=h.target_agent,
            tenant_scope_key=h.scope_key,
            incident_id=h.incident_id,
            retry_count=h.retry_count,
        )
        return entry.entry_id

    import asyncio

    result = asyncio.run(
        deliver_handoff_with_retry(
            handoff=handoff,
            deliver=_always_fail,
            on_dead_letter=_persist_dead_letter,
            max_retries=2,
            retry_window_seconds=5,
        )
    )

    assert result.status == "dead_lettered"
    assert result.dead_letter_entry_id is not None
    stored = DEAD_LETTERS.get(result.dead_letter_entry_id)
    assert stored is not None
    assert stored.entry_type == "handoff_failure"
    assert stored.incident_id == "incident-dlq-1"
