"""Unit tests for SignalDeduplicator (Phase 2: T011)."""

import time

import pytest


class TestSignalDeduplicator:
    """T011: Deduplication service tests."""

    def test_first_seen_signal_is_not_duplicate(self) -> None:
        from monitoring.dedup import SignalDeduplicator

        dedup = SignalDeduplicator(window_minutes=10)
        assert dedup.is_duplicate("sig-001") is False

    def test_duplicate_within_window_returns_true(self) -> None:
        from monitoring.dedup import SignalDeduplicator

        dedup = SignalDeduplicator(window_minutes=10)
        dedup.mark_seen("sig-001")
        assert dedup.is_duplicate("sig-001") is True

    def test_different_signal_ids_not_duplicates(self) -> None:
        from monitoring.dedup import SignalDeduplicator

        dedup = SignalDeduplicator(window_minutes=10)
        dedup.mark_seen("sig-001")
        assert dedup.is_duplicate("sig-002") is False

    def test_signal_after_ttl_expiry_returns_false(self) -> None:
        from monitoring.dedup import SignalDeduplicator

        # Use a very short window (0.01 minutes = 0.6 seconds)
        dedup = SignalDeduplicator(window_minutes=0)
        dedup._window_seconds = 0.1  # 100ms for test speed
        dedup.mark_seen("sig-001")
        time.sleep(0.2)  # wait past window
        assert dedup.is_duplicate("sig-001") is False

    def test_cache_eviction_on_max_size(self) -> None:
        from monitoring.dedup import SignalDeduplicator

        dedup = SignalDeduplicator(window_minutes=10, max_size=5)
        for i in range(10):
            dedup.mark_seen(f"sig-{i:03d}")
        # Only the last 5 should remain
        assert dedup.size == 5
        # Oldest should be evicted
        assert dedup.is_duplicate("sig-000") is False
        # Most recent should still be present
        assert dedup.is_duplicate("sig-009") is True

    def test_mark_seen_refreshes_existing_entry(self) -> None:
        from monitoring.dedup import SignalDeduplicator

        dedup = SignalDeduplicator(window_minutes=10)
        dedup.mark_seen("sig-001")
        dedup.mark_seen("sig-002")
        dedup.mark_seen("sig-001")  # refresh
        assert dedup.is_duplicate("sig-001") is True
        assert dedup.size == 2  # no duplicate entries

    def test_size_property(self) -> None:
        from monitoring.dedup import SignalDeduplicator

        dedup = SignalDeduplicator(window_minutes=10)
        assert dedup.size == 0
        dedup.mark_seen("sig-001")
        assert dedup.size == 1
        dedup.mark_seen("sig-002")
        assert dedup.size == 2
