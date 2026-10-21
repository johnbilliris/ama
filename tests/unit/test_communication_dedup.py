"""Tests for communication.dedup — HandoffDeduplicator with dual dedup keys."""

from communication.dedup import HandoffDeduplicator

# ---------------------------------------------------------------------------
# By-ID dedup
# ---------------------------------------------------------------------------


class TestDedupById:
    def test_first_seen_returns_false(self):
        dedup = HandoffDeduplicator()
        assert dedup.is_duplicate_by_id("handoff-1", tenant_id="live") is False

    def test_duplicate_returns_true(self):
        dedup = HandoffDeduplicator()
        dedup.is_duplicate_by_id("handoff-1", tenant_id="live")
        assert dedup.is_duplicate_by_id("handoff-1", tenant_id="live") is True

    def test_different_ids_not_duplicate(self):
        dedup = HandoffDeduplicator()
        dedup.is_duplicate_by_id("handoff-1", tenant_id="live")
        assert dedup.is_duplicate_by_id("handoff-2", tenant_id="live") is False

    def test_same_handoff_is_independent_between_tenants(self):
        dedup = HandoffDeduplicator()
        assert dedup.is_duplicate_by_id("handoff-1", tenant_id="tenant-one") is False
        assert dedup.is_duplicate_by_id("handoff-1", tenant_id="tenant-two") is False


# ---------------------------------------------------------------------------
# By-incident dedup
# ---------------------------------------------------------------------------


class TestDedupByIncident:
    def test_first_seen_returns_false(self):
        dedup = HandoffDeduplicator()
        assert dedup.is_duplicate_by_incident("inc-1", "fire", tenant_id="live") is False

    def test_duplicate_returns_true(self):
        dedup = HandoffDeduplicator()
        dedup.is_duplicate_by_incident("inc-1", "fire", tenant_id="live")
        assert dedup.is_duplicate_by_incident("inc-1", "fire", tenant_id="live") is True

    def test_different_hazard_not_duplicate(self):
        dedup = HandoffDeduplicator()
        dedup.is_duplicate_by_incident("inc-1", "fire", tenant_id="live")
        assert dedup.is_duplicate_by_incident("inc-1", "flood", tenant_id="live") is False

    def test_different_incident_not_duplicate(self):
        dedup = HandoffDeduplicator()
        dedup.is_duplicate_by_incident("inc-1", "fire", tenant_id="live")
        assert dedup.is_duplicate_by_incident("inc-2", "fire", tenant_id="live") is False

    def test_same_incident_and_hazard_are_independent_between_tenants(self):
        dedup = HandoffDeduplicator()
        assert dedup.is_duplicate_by_incident("inc-1", "fire", tenant_id="tenant-one") is False
        assert dedup.is_duplicate_by_incident("inc-1", "fire", tenant_id="tenant-two") is False


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
        dedup.is_duplicate_by_id("handoff-1", tenant_id="live")

        # Advance past the 60-second window
        fake_time[0] = 1061.0
        assert dedup.is_duplicate_by_id("handoff-1", tenant_id="live") is False

    def test_incident_dedup_expires_after_window(self, monkeypatch):
        dedup = HandoffDeduplicator(window_minutes=1)
        import time

        fake_time = [1000.0]
        monkeypatch.setattr(time, "monotonic", lambda: fake_time[0])
        dedup.is_duplicate_by_incident("inc-1", "fire", tenant_id="live")

        # Advance past the 60-second window
        fake_time[0] = 1061.0
        assert dedup.is_duplicate_by_incident("inc-1", "fire", tenant_id="live") is False

    def test_id_dedup_within_window_still_duplicate(self, monkeypatch):
        dedup = HandoffDeduplicator(window_minutes=1)
        import time

        fake_time = [1000.0]
        monkeypatch.setattr(time, "monotonic", lambda: fake_time[0])
        dedup.is_duplicate_by_id("handoff-1", tenant_id="live")

        # Still within 60s window
        fake_time[0] = 1050.0
        assert dedup.is_duplicate_by_id("handoff-1", tenant_id="live") is True


# ---------------------------------------------------------------------------
# Cache size
# ---------------------------------------------------------------------------


class TestDedupCacheSize:
    def test_size_after_inserts(self):
        dedup = HandoffDeduplicator()
        dedup.is_duplicate_by_id("h1", tenant_id="live")
        dedup.is_duplicate_by_id("h2", tenant_id="live")
        dedup.is_duplicate_by_incident("inc-1", "fire", tenant_id="live")
        assert dedup.id_cache_size == 2
        assert dedup.incident_cache_size == 1
        assert dedup.size == 3

    def test_empty_cache_size(self):
        dedup = HandoffDeduplicator()
        assert dedup.size == 0

    def test_max_size_enforcement(self):
        dedup = HandoffDeduplicator(max_size=3)
        for i in range(5):
            dedup.is_duplicate_by_id(f"h-{i}", tenant_id="live")
        assert dedup.id_cache_size <= 3


class TestProcessingReservations:
    def test_released_handoff_can_be_reserved_again(self):
        dedup = HandoffDeduplicator()
        assert dedup.reserve_handoff("h1", tenant_id="live") is True
        dedup.release(tenant_id="live", handoff_id="h1", incident_id="inc-1", hazard_type="key-1")
        assert dedup.reserve_handoff("h1", tenant_id="live") is True

    def test_completed_handoff_and_change_remain_duplicates(self):
        dedup = HandoffDeduplicator()
        assert dedup.reserve_handoff("h1", tenant_id="live") is True
        assert dedup.reserve_incident_change("inc-1", "assessment-1:initial", tenant_id="live") is True
        dedup.complete(
            tenant_id="live",
            handoff_id="h1",
            incident_id="inc-1",
            change_key="assessment-1:initial",
        )

        assert dedup.reserve_handoff("h1", tenant_id="live") is False
        assert dedup.reserve_incident_change("inc-1", "assessment-1:initial", tenant_id="live") is False
        assert dedup.reserve_incident_change("inc-1", "assessment-2:initial", tenant_id="live") is True
