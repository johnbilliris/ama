"""Tests for risk_assessment.dedup – HandoffDeduplicator TTL cache."""

from unittest.mock import patch

from risk_assessment.dedup import HandoffDeduplicator


class TestHandoffDeduplicator:
    def test_first_seen_returns_false(self):
        dedup = HandoffDeduplicator(window_minutes=10)
        assert dedup.is_duplicate("hf-001") is False

    def test_same_id_within_window_returns_true(self):
        dedup = HandoffDeduplicator(window_minutes=10)
        dedup.is_duplicate("hf-001")
        assert dedup.is_duplicate("hf-001") is True

    def test_after_expiry_returns_false(self):
        dedup = HandoffDeduplicator(window_minutes=1)
        with patch("risk_assessment.dedup.time.monotonic", return_value=1000.0):
            dedup.is_duplicate("hf-002")
        # Advance past the 1-minute window
        with patch("risk_assessment.dedup.time.monotonic", return_value=1061.0):
            assert dedup.is_duplicate("hf-002") is False

    def test_multiple_different_ids_independent(self):
        dedup = HandoffDeduplicator(window_minutes=10)
        assert dedup.is_duplicate("hf-A") is False
        assert dedup.is_duplicate("hf-B") is False
        assert dedup.is_duplicate("hf-A") is True
        assert dedup.is_duplicate("hf-B") is True

    def test_lru_eviction_on_max_size(self):
        dedup = HandoffDeduplicator(window_minutes=10, max_size=3)
        dedup.is_duplicate("hf-1")
        dedup.is_duplicate("hf-2")
        dedup.is_duplicate("hf-3")
        assert dedup.size == 3
        # Adding a 4th should evict the oldest (hf-1)
        dedup.is_duplicate("hf-4")
        assert dedup.size <= 3
        # hf-1 was evicted, so it should be seen as new again
        assert dedup.is_duplicate("hf-1") is False

    def test_size_property(self):
        dedup = HandoffDeduplicator(window_minutes=10)
        assert dedup.size == 0
        dedup.is_duplicate("hf-x")
        assert dedup.size == 1
