"""Unit tests for DataFreshnessTracker (Phase 2: T012)."""

from datetime import UTC, datetime, timedelta


class TestDataFreshnessTracker:
    """T012: Freshness tracker tests — all 4 status transitions."""

    def test_first_signal_creates_healthy_indicator(self) -> None:
        from monitoring.freshness import DataFreshnessTracker

        tracker = DataFreshnessTracker()
        change = tracker.update("bom-nsw", "authoritative", 0.95)
        assert change is None  # first signal, no transition
        indicator = tracker.get_status("bom-nsw")
        assert indicator is not None
        assert indicator.status.value == "healthy"
        assert indicator.current_freshness_score == 0.95

    def test_healthy_to_degraded_on_low_freshness(self) -> None:
        from monitoring.freshness import DataFreshnessTracker

        tracker = DataFreshnessTracker()
        tracker.update("sensor-001", "iot", 0.8)  # initial healthy
        change = tracker.update("sensor-001", "iot", 0.3)  # low freshness
        assert change is not None
        assert change.previous_status.value == "healthy"
        assert change.new_status.value == "degraded"

    def test_degraded_to_healthy_on_good_signal(self) -> None:
        from monitoring.freshness import DataFreshnessTracker

        tracker = DataFreshnessTracker()
        tracker.update("social-001", "social", 0.8)  # initial
        tracker.update("social-001", "social", 0.3)  # degrade
        change = tracker.update("social-001", "social", 0.7)  # recover
        assert change is not None
        assert change.previous_status.value == "degraded"
        assert change.new_status.value == "healthy"

    def test_offline_to_healthy_on_good_signal(self) -> None:
        from monitoring.freshness import DataFreshnessTracker
        from monitoring.models import FreshnessStatus

        tracker = DataFreshnessTracker()
        tracker.update("sensor-002", "iot", 0.9)  # initial

        # Manually set to offline for test
        indicator = tracker.get_status("sensor-002")
        indicator.status = FreshnessStatus.offline

        change = tracker.update("sensor-002", "iot", 0.8)  # recover
        assert change is not None
        assert change.previous_status.value == "offline"
        assert change.new_status.value == "healthy"

    def test_degraded_stays_degraded_on_low_signal(self) -> None:
        from monitoring.freshness import DataFreshnessTracker

        tracker = DataFreshnessTracker()
        tracker.update("social-002", "social", 0.8)  # initial
        tracker.update("social-002", "social", 0.3)  # degrade
        change = tracker.update("social-002", "social", 0.4)  # still low
        assert change is None  # no transition
        indicator = tracker.get_status("social-002")
        assert indicator.status.value == "degraded"

    def test_per_source_type_threshold(self) -> None:
        from monitoring.config import MonitoringConfig
        from monitoring.freshness import DataFreshnessTracker

        config = MonitoringConfig()
        tracker = DataFreshnessTracker(config)

        tracker.update("auth-001", "authoritative", 0.9)
        tracker.update("iot-001", "iot", 0.9)
        tracker.update("soc-001", "social", 0.9)

        auth_ind = tracker.get_status("auth-001")
        iot_ind = tracker.get_status("iot-001")
        soc_ind = tracker.get_status("soc-001")

        assert auth_ind.staleness_threshold_minutes == 15
        assert iot_ind.staleness_threshold_minutes == 5
        assert soc_ind.staleness_threshold_minutes == 30

    def test_check_staleness_degrades_stale_sources(self) -> None:
        from monitoring.freshness import DataFreshnessTracker
        from monitoring.models import FreshnessStatus

        tracker = DataFreshnessTracker()
        tracker.update("sensor-stale", "iot", 0.9)  # initial

        # Manually backdate the last signal time
        indicator = tracker.get_status("sensor-stale")
        indicator.last_signal_received_at = datetime.now(UTC) - timedelta(minutes=10)

        changes = tracker.check_staleness()
        assert len(changes) == 1
        assert changes[0].new_status == FreshnessStatus.degraded

    def test_get_summary_status_healthy_when_all_healthy(self) -> None:
        from monitoring.freshness import DataFreshnessTracker

        tracker = DataFreshnessTracker()
        tracker.update("src-1", "authoritative", 0.9)
        tracker.update("src-2", "iot", 0.8)
        assert tracker.get_summary_status() == "healthy"

    def test_get_summary_status_degraded_when_any_degraded(self) -> None:
        from monitoring.freshness import DataFreshnessTracker

        tracker = DataFreshnessTracker()
        tracker.update("src-1", "authoritative", 0.9)
        tracker.update("src-2", "iot", 0.8)
        tracker.update("src-2", "iot", 0.3)  # degrade
        assert tracker.get_summary_status() == "degraded"

    def test_get_all_indicators(self) -> None:
        from monitoring.freshness import DataFreshnessTracker

        tracker = DataFreshnessTracker()
        tracker.update("src-1", "authoritative", 0.9)
        tracker.update("src-2", "iot", 0.8)
        indicators = tracker.get_all_indicators()
        assert len(indicators) == 2
