from datetime import UTC, datetime, timedelta

from apps.api.app.services.ingestion.pipeline_base import CircuitBreakerState


class TestCircuitBreakerStateTransitions:
    def test_starts_closed(self):
        cb = CircuitBreakerState(threshold=3)
        assert cb.state == "closed"
        assert cb.should_allow_request() is True

    def test_stays_closed_below_threshold(self):
        cb = CircuitBreakerState(threshold=3)
        cb.record_failure()
        cb.record_failure()
        assert cb.state == "closed"
        assert cb.should_allow_request() is True

    def test_trips_to_open_at_threshold(self):
        cb = CircuitBreakerState(threshold=3, backoff_initial=1)
        cb.record_failure()
        cb.record_failure()
        cb.record_failure()
        assert cb.state == "open"
        assert cb.total_trips == 1
        assert cb.should_allow_request() is False

    def test_success_resets_failure_count(self):
        cb = CircuitBreakerState(threshold=3)
        cb.record_failure()
        cb.record_failure()
        cb.record_success()
        assert cb.consecutive_failures == 0
        assert cb.state == "closed"

    def test_half_open_after_backoff(self):
        cb = CircuitBreakerState(threshold=3, backoff_initial=1)
        cb.record_failure()
        cb.record_failure()
        cb.record_failure()
        assert cb.state == "open"
        cb.backoff_until = datetime.now(UTC) - timedelta(seconds=1)
        assert cb.should_allow_request() is True
        assert cb.state == "half_open"

    def test_half_open_success_closes(self):
        cb = CircuitBreakerState(threshold=3, backoff_initial=1)
        cb.record_failure()
        cb.record_failure()
        cb.record_failure()
        cb.backoff_until = datetime.now(UTC) - timedelta(seconds=1)
        cb.should_allow_request()
        assert cb.state == "half_open"
        cb.record_success()
        assert cb.state == "closed"
        assert cb.consecutive_failures == 0

    def test_half_open_failure_reopens(self):
        cb = CircuitBreakerState(threshold=3, backoff_initial=1)
        cb.record_failure()
        cb.record_failure()
        cb.record_failure()
        cb.backoff_until = datetime.now(UTC) - timedelta(seconds=1)
        cb.should_allow_request()
        assert cb.state == "half_open"
        cb.record_failure()
        assert cb.state == "open"
        assert cb.total_trips == 2

    def test_exponential_backoff(self):
        cb = CircuitBreakerState(threshold=1, backoff_initial=30, backoff_max=300)
        cb.record_failure()
        assert cb.state == "open"
        assert cb.total_trips == 1
        cb.backoff_until = datetime.now(UTC) - timedelta(seconds=1)
        cb.should_allow_request()
        cb.record_failure()
        assert cb.total_trips == 2
