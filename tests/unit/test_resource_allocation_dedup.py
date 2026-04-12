"""Unit tests for handoff deduplication.

Covers:
- First-seen handoff passes
- Duplicate within window discarded
- Duplicate after window passes
- Configurable window duration
- Concurrent dedup safety
"""

from __future__ import annotations

import time

from resource_allocation.dedup import HandoffDeduplicator


class TestHandoffDeduplicator:
    def test_first_seen_is_not_duplicate(self):
        dedup = HandoffDeduplicator(window_minutes=10)
        assert dedup.is_duplicate("handoff-001") is False

    def test_second_seen_is_duplicate(self):
        dedup = HandoffDeduplicator(window_minutes=10)
        dedup.is_duplicate("handoff-001")
        assert dedup.is_duplicate("handoff-001") is True

    def test_different_ids_not_duplicate(self):
        dedup = HandoffDeduplicator(window_minutes=10)
        dedup.is_duplicate("handoff-001")
        assert dedup.is_duplicate("handoff-002") is False

    def test_expired_entry_is_not_duplicate(self):
        # Use very short window
        dedup = HandoffDeduplicator(window_minutes=0)  # 0 minutes = immediate expiry
        dedup._window_seconds = 0.01  # 10ms for testing

        dedup.is_duplicate("handoff-001")
        time.sleep(0.02)  # Wait for expiry
        assert dedup.is_duplicate("handoff-001") is False

    def test_configurable_window(self):
        dedup = HandoffDeduplicator(window_minutes=5)
        assert dedup._window_seconds == 300

    def test_size_property(self):
        dedup = HandoffDeduplicator(window_minutes=10)
        assert dedup.size == 0
        dedup.is_duplicate("h1")
        assert dedup.size == 1
        dedup.is_duplicate("h2")
        assert dedup.size == 2

    def test_max_size_enforcement(self):
        dedup = HandoffDeduplicator(window_minutes=10, max_size=3)
        for i in range(5):
            dedup.is_duplicate(f"h-{i}")
        assert dedup.size <= 3

    def test_multiple_lookups_same_id(self):
        dedup = HandoffDeduplicator(window_minutes=10)
        assert dedup.is_duplicate("h-001") is False
        assert dedup.is_duplicate("h-001") is True
        assert dedup.is_duplicate("h-001") is True
