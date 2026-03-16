from app.middleware.resilience import TransientDependencyError, retry_transient_dependency_call
from app.services.dead_letter_service import DeadLetterService


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


def test_dead_letter_created_on_permanent_failure() -> None:
    service = DeadLetterService()
    entry = service.create_entry(
        entry_type="event_delivery_failure",
        correlation_id="corr-900",
        original_payload={"operation": "sync"},
        failure_reason="permanent error",
        failure_code="MAX_RETRIES_EXCEEDED",
        source_service="integration-test",
        target_service="cache",
        tenant_scope_key="tenant-a",
    )

    assert entry.correlation_id == "corr-900"
    assert entry.resolution == "pending"
