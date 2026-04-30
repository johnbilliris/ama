"""Tests for communication.dedup — HandoffDeduplicator with dual dedup keys."""

from communication.dedup import HandoffDeduplicator

# ---------------------------------------------------------------------------
# By-ID dedup
# ---------------------------------------------------------------------------


class TestDedupById:
    def test_first_seen_returns_false(self):
        dedup = HandoffDeduplicator()
        assert dedup.is_duplicate_by_id("handoff-1") is False

    def test_duplicate_returns_true(self):
        dedup = HandoffDeduplicator()
        dedup.is_duplicate_by_id("handoff-1")
        assert dedup.is_duplicate_by_id("handoff-1") is True

    def test_different_ids_not_duplicate(self):
        dedup = HandoffDeduplicator()
        dedup.is_duplicate_by_id("handoff-1")
        assert dedup.is_duplicate_by_id("handoff-2") is False


# ---------------------------------------------------------------------------
# By-incident dedup
# ---------------------------------------------------------------------------


class TestDedupByIncident:
    def test_first_seen_returns_false(self):
        dedup = HandoffDeduplicator()
        assert dedup.is_duplicate_by_incident("inc-1", "fire") is False

    def test_duplicate_returns_true(self):
        dedup = HandoffDeduplicator()
        dedup.is_duplicate_by_incident("inc-1", "fire")
        assert dedup.is_duplicate_by_incident("inc-1", "fire") is True

    def test_different_hazard_not_duplicate(self):
        dedup = HandoffDeduplicator()
        dedup.is_duplicate_by_incident("inc-1", "fire")
        assert dedup.is_duplicate_by_incident("inc-1", "flood") is False

    def test_different_incident_not_duplicate(self):
        dedup = HandoffDeduplicator()
        dedup.is_duplicate_by_incident("inc-1", "fire")
        assert dedup.is_duplicate_by_incident("inc-2", "fire") is False


# ---------------------------------------------------------------------------
# TTL expiry
# ---------------------------------------------------------------------------


class TestDedupTTLExpiry:
    def test_id_dedup_expires_after_window(self, monkeypatch):
        dedup = HandoffDeduplicator(window_minutes=1)
        # Insert at time T
        import time

        fake_time = [1000.0]
        monkeypatch.setattr(time, "monotonic", lambda: fake_time[0])
        dedup.is_duplicate_by_id("handoff-1")

        # Advance past the 60-second window
        fake_time[0] = 1061.0
        assert dedup.is_duplicate_by_id("handoff-1") is False

    def test_incident_dedup_expires_after_window(self, monkeypatch):
        dedup = HandoffDeduplicator(window_minutes=1)
        import time

        fake_time = [1000.0]
        monkeypatch.setattr(time, "monotonic", lambda: fake_time[0])
        dedup.is_duplicate_by_incident("inc-1", "fire")

        # Advance past the 60-second window
        fake_time[0] = 1061.0
        assert dedup.is_duplicate_by_incident("inc-1", "fire") is False

    def test_id_dedup_within_window_still_duplicate(self, monkeypatch):
        dedup = HandoffDeduplicator(window_minutes=1)
        import time

        fake_time = [1000.0]
        monkeypatch.setattr(time, "monotonic", lambda: fake_time[0])
        dedup.is_duplicate_by_id("handoff-1")

        # Still within 60s window
        fake_time[0] = 1050.0
        assert dedup.is_duplicate_by_id("handoff-1") is True


# ---------------------------------------------------------------------------
# Cache size
# ---------------------------------------------------------------------------


class TestDedupCacheSize:
    def test_size_after_inserts(self):
        dedup = HandoffDeduplicator()
        dedup.is_duplicate_by_id("h1")
        dedup.is_duplicate_by_id("h2")
        dedup.is_duplicate_by_incident("inc-1", "fire")
        assert dedup.id_cache_size == 2
        assert dedup.incident_cache_size == 1
        assert dedup.size == 3

    def test_empty_cache_size(self):
        dedup = HandoffDeduplicator()
        assert dedup.size == 0

    def test_max_size_enforcement(self):
        dedup = HandoffDeduplicator(max_size=3)
        for i in range(5):
            dedup.is_duplicate_by_id(f"h-{i}")
        assert dedup.id_cache_size <= 3
