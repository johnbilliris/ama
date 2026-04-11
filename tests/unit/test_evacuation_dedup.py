"""Tests for evacuation.dedup — TTL-based in-memory deduplication (T016)."""

import time
from unittest.mock import patch

import pytest

from evacuation.dedup import HandoffDeduplicator


# ---------------------------------------------------------------------------
# Basic duplicate detection
# ---------------------------------------------------------------------------


class TestDuplicateDetection:
    def test_first_seen_returns_false(self):
        d = HandoffDeduplicator(window_minutes=10)
        assert d.is_duplicate("hf-1") is False

    def test_second_seen_returns_true(self):
        d = HandoffDeduplicator(window_minutes=10)
        d.is_duplicate("hf-1")
        assert d.is_duplicate("hf-1") is True

    def test_different_ids_not_duplicate(self):
        d = HandoffDeduplicator(window_minutes=10)
        d.is_duplicate("hf-1")
        assert d.is_duplicate("hf-2") is False

    def test_size_grows(self):
        d = HandoffDeduplicator(window_minutes=10)
        assert d.size == 0
        d.is_duplicate("hf-1")
        assert d.size == 1
        d.is_duplicate("hf-2")
        assert d.size == 2

    def test_duplicate_does_not_increase_size(self):
        d = HandoffDeduplicator(window_minutes=10)
        d.is_duplicate("hf-1")
        d.is_duplicate("hf-1")
        assert d.size == 1


# ---------------------------------------------------------------------------
# TTL expiry
# ---------------------------------------------------------------------------


class TestTTLExpiry:
    def test_entry_expires_after_window(self):
        d = HandoffDeduplicator(window_minutes=1)
        d.is_duplicate("hf-1")

        # Fast-forward time beyond the 1-minute window
        original_time = d._cache["hf-1"]
        d._cache["hf-1"] = original_time - 120  # 2 minutes ago

        # Should no longer be a duplicate (expired)
        assert d.is_duplicate("hf-1") is False

    def test_entry_not_expired_within_window(self):
        d = HandoffDeduplicator(window_minutes=10)
        d.is_duplicate("hf-1")

        # Still within window
        assert d.is_duplicate("hf-1") is True

    def test_expired_entries_evicted(self):
        d = HandoffDeduplicator(window_minutes=1)
        d.is_duplicate("hf-1")
        d.is_duplicate("hf-2")
        assert d.size == 2

        # Age both entries past the window
        now = time.monotonic()
        d._cache["hf-1"] = now - 120
        d._cache["hf-2"] = now - 120

        # Adding a new entry should trigger eviction of expired
        d.is_duplicate("hf-3")
        # hf-1 and hf-2 should have been evicted
        assert d.size == 1


# ---------------------------------------------------------------------------
# Max size / LRU eviction
# ---------------------------------------------------------------------------


class TestMaxSizeEviction:
    def test_max_size_enforced(self):
        d = HandoffDeduplicator(window_minutes=10, max_size=5)
        for i in range(10):
            d.is_duplicate(f"hf-{i}")
        assert d.size == 5

    def test_oldest_evicted_first(self):
        d = HandoffDeduplicator(window_minutes=10, max_size=3)
        d.is_duplicate("hf-1")
        d.is_duplicate("hf-2")
        d.is_duplicate("hf-3")
        d.is_duplicate("hf-4")  # hf-1 should be evicted

        assert d.is_duplicate("hf-1") is False  # Re-added as new
        assert d.is_duplicate("hf-4") is True  # Still present


# ---------------------------------------------------------------------------
# Empty cache
# ---------------------------------------------------------------------------


class TestEmptyCache:
    def test_empty_cache_size(self):
        d = HandoffDeduplicator()
        assert d.size == 0

    def test_empty_cache_not_duplicate(self):
        d = HandoffDeduplicator()
        assert d.is_duplicate("anything") is False


# ---------------------------------------------------------------------------
# Concurrent access pattern (sequential simulation)
# ---------------------------------------------------------------------------


class TestConcurrentAccess:
    def test_rapid_sequential_access(self):
        """Simulate rapid access pattern — not truly concurrent but validates
        thread-safety-relevant ordering behaviour."""
        d = HandoffDeduplicator(window_minutes=10)
        results = []
        for _ in range(100):
            results.append(d.is_duplicate("hf-same"))
        # First should be False, rest True
        assert results[0] is False
        assert all(r is True for r in results[1:])

    def test_interleaved_ids(self):
        d = HandoffDeduplicator(window_minutes=10)
        for i in range(50):
            d.is_duplicate(f"hf-{i % 10}")
        # All 10 unique IDs should be present
        assert d.size == 10
