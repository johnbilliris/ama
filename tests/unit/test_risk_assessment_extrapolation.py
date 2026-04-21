"""Tests for risk_assessment.extrapolation — time-series trend extrapolation."""

from datetime import UTC, datetime, timedelta

from risk_assessment.extrapolation import (
    _hours_to_threshold,
    _linear_regression,
    _r_squared,
    TrendPoint,
    extrapolate_hazard_trend,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_signal(
    signal_id: str,
    confidence: float,
    freshness: float = 1.0,
    hours_ago: float = 0.0,
    category: str = "hydrology",
    source_kind: str = "authoritative",
) -> dict:
    ts = datetime.now(UTC) - timedelta(hours=hours_ago)
    return {
        "signal_id": signal_id,
        "confidence_score": confidence,
        "freshness_score": freshness,
        "source_kind": source_kind,
        "category": category,
        "provenance": {"sourceTimestamp": ts.isoformat()},
    }


# ---------------------------------------------------------------------------
# Linear regression
# ---------------------------------------------------------------------------


class TestLinearRegression:
    def test_perfect_line(self):
        t0 = datetime(2026, 1, 1, tzinfo=UTC)
        points = [
            TrendPoint(timestamp=t0, value=0.2, signal_id="s1"),
            TrendPoint(timestamp=t0 + timedelta(hours=1), value=0.3, signal_id="s2"),
            TrendPoint(timestamp=t0 + timedelta(hours=2), value=0.4, signal_id="s3"),
        ]
        slope, intercept = _linear_regression(points)
        assert abs(slope - 0.1) < 1e-6
        assert abs(intercept - 0.2) < 1e-6

    def test_single_point_returns_zero_slope(self):
        t0 = datetime(2026, 1, 1, tzinfo=UTC)
        slope, intercept = _linear_regression([
            TrendPoint(timestamp=t0, value=0.5, signal_id="s1"),
        ])
        assert slope == 0.0
        assert intercept == 0.5

    def test_two_points(self):
        t0 = datetime(2026, 1, 1, tzinfo=UTC)
        points = [
            TrendPoint(timestamp=t0, value=0.3, signal_id="s1"),
            TrendPoint(timestamp=t0 + timedelta(hours=10), value=0.8, signal_id="s2"),
        ]
        slope, intercept = _linear_regression(points)
        assert abs(slope - 0.05) < 1e-6
        assert abs(intercept - 0.3) < 1e-6


# ---------------------------------------------------------------------------
# R-squared
# ---------------------------------------------------------------------------


class TestRSquared:
    def test_perfect_fit(self):
        t0 = datetime(2026, 1, 1, tzinfo=UTC)
        points = [
            TrendPoint(timestamp=t0, value=0.1, signal_id="s1"),
            TrendPoint(timestamp=t0 + timedelta(hours=1), value=0.2, signal_id="s2"),
            TrendPoint(timestamp=t0 + timedelta(hours=2), value=0.3, signal_id="s3"),
        ]
        r2 = _r_squared(points, slope=0.1, intercept=0.1)
        assert abs(r2 - 1.0) < 1e-6

    def test_poor_fit(self):
        t0 = datetime(2026, 1, 1, tzinfo=UTC)
        points = [
            TrendPoint(timestamp=t0, value=0.9, signal_id="s1"),
            TrendPoint(timestamp=t0 + timedelta(hours=1), value=0.1, signal_id="s2"),
            TrendPoint(timestamp=t0 + timedelta(hours=2), value=0.8, signal_id="s3"),
        ]
        slope, intercept = _linear_regression(points)
        r2 = _r_squared(points, slope, intercept)
        assert r2 < 0.5


# ---------------------------------------------------------------------------
# Hours to threshold
# ---------------------------------------------------------------------------


class TestHoursToThreshold:
    def test_positive_slope_reaches_threshold(self):
        hours = _hours_to_threshold(current=0.5, slope=0.05, threshold=0.8)
        assert hours is not None
        assert abs(hours - 6.0) < 0.2

    def test_already_above_threshold(self):
        hours = _hours_to_threshold(current=0.9, slope=0.05, threshold=0.8)
        assert hours == 0.0

    def test_negative_slope_returns_none(self):
        hours = _hours_to_threshold(current=0.5, slope=-0.01, threshold=0.8)
        assert hours is None

    def test_zero_slope_returns_none(self):
        hours = _hours_to_threshold(current=0.5, slope=0.0, threshold=0.8)
        assert hours is None

    def test_very_slow_slope_exceeds_max(self):
        hours = _hours_to_threshold(current=0.1, slope=0.001, threshold=0.95)
        assert hours is None  # Would take 850 hours, exceeds MAX_EXTRAPOLATION_HOURS


# ---------------------------------------------------------------------------
# Full extrapolation
# ---------------------------------------------------------------------------


class TestExtrapolateHazardTrend:
    def test_increasing_trend_detected(self):
        signals = [
            _make_signal("s1", 0.3, hours_ago=6.0),
            _make_signal("s2", 0.5, hours_ago=3.0),
            _make_signal("s3", 0.7, hours_ago=0.0),
        ]
        result = extrapolate_hazard_trend(signals, category="hydrology")
        assert result.trend_detected is True
        assert result.trend_direction == "increasing"
        assert result.slope_per_hour > 0
        assert result.data_points_used == 3
        assert result.projected_value_24h > result.current_value

    def test_decreasing_trend_detected(self):
        signals = [
            _make_signal("s1", 0.9, hours_ago=6.0),
            _make_signal("s2", 0.7, hours_ago=3.0),
            _make_signal("s3", 0.5, hours_ago=0.0),
        ]
        result = extrapolate_hazard_trend(signals, category="hydrology")
        assert result.trend_detected is True
        assert result.trend_direction == "decreasing"
        assert result.slope_per_hour < 0

    def test_stable_trend(self):
        signals = [
            _make_signal("s1", 0.5, hours_ago=6.0),
            _make_signal("s2", 0.5, hours_ago=3.0),
            _make_signal("s3", 0.5, hours_ago=0.0),
        ]
        result = extrapolate_hazard_trend(signals, category="hydrology")
        assert result.trend_detected is False
        assert result.trend_direction == "stable"

    def test_insufficient_points(self):
        signals = [_make_signal("s1", 0.5, hours_ago=0.0)]
        result = extrapolate_hazard_trend(signals, category="hydrology", min_points=2)
        assert result.trend_detected is False
        assert result.data_points_used == 1
        assert "Insufficient" in result.details.get("reason", "")

    def test_empty_signals(self):
        result = extrapolate_hazard_trend([], category="hydrology")
        assert result.trend_detected is False
        assert result.data_points_used == 0

    def test_warning_threshold_hours(self):
        signals = [
            _make_signal("s1", 0.3, hours_ago=12.0),
            _make_signal("s2", 0.4, hours_ago=6.0),
            _make_signal("s3", 0.5, hours_ago=0.0),
        ]
        result = extrapolate_hazard_trend(signals, category="hydrology")
        assert result.trend_detected is True
        # Warning threshold for hydrology is 0.8
        # Current is ~0.5, slope ~0.0167/hr → ~18h to 0.8
        assert result.hours_to_warning_threshold is not None
        assert result.hours_to_warning_threshold > 0
        assert result.predictive_lead_time_hours > 0

    def test_category_specific_thresholds(self):
        signals = [
            _make_signal("s1", 0.3, hours_ago=6.0, category="fire"),
            _make_signal("s2", 0.5, hours_ago=3.0, category="fire"),
            _make_signal("s3", 0.65, hours_ago=0.0, category="fire"),
        ]
        result = extrapolate_hazard_trend(signals, category="fire")
        assert result.trend_detected is True
        # Fire warning threshold is 0.7 (lower than hydrology's 0.8)
        assert result.hours_to_warning_threshold is not None

    def test_extrapolation_confidence_scales_with_points(self):
        two_signals = [
            _make_signal("s1", 0.3, hours_ago=6.0),
            _make_signal("s2", 0.6, hours_ago=0.0),
        ]
        five_signals = [
            _make_signal("s1", 0.2, hours_ago=12.0),
            _make_signal("s2", 0.3, hours_ago=9.0),
            _make_signal("s3", 0.4, hours_ago=6.0),
            _make_signal("s4", 0.5, hours_ago=3.0),
            _make_signal("s5", 0.6, hours_ago=0.0),
        ]
        result_2 = extrapolate_hazard_trend(two_signals, category="hydrology")
        result_5 = extrapolate_hazard_trend(five_signals, category="hydrology")
        # More data points → higher extrapolation confidence
        assert result_5.extrapolation_confidence >= result_2.extrapolation_confidence

    def test_projected_values_clamped_0_to_1(self):
        signals = [
            _make_signal("s1", 0.8, hours_ago=4.0),
            _make_signal("s2", 0.9, hours_ago=2.0),
            _make_signal("s3", 0.95, hours_ago=0.0),
        ]
        result = extrapolate_hazard_trend(signals, category="hydrology")
        assert 0.0 <= result.projected_value_24h <= 1.0
        assert 0.0 <= result.projected_value_48h <= 1.0

    def test_freshness_affects_effective_value(self):
        fresh_signals = [
            _make_signal("s1", 0.6, freshness=1.0, hours_ago=6.0),
            _make_signal("s2", 0.8, freshness=1.0, hours_ago=0.0),
        ]
        stale_signals = [
            _make_signal("s1", 0.6, freshness=0.3, hours_ago=6.0),
            _make_signal("s2", 0.8, freshness=0.3, hours_ago=0.0),
        ]
        result_fresh = extrapolate_hazard_trend(fresh_signals, category="hydrology")
        result_stale = extrapolate_hazard_trend(stale_signals, category="hydrology")
        # Stale signals have lower effective values
        assert result_stale.current_value < result_fresh.current_value

    def test_result_contains_signal_ids(self):
        signals = [
            _make_signal("sig-alpha", 0.3, hours_ago=6.0),
            _make_signal("sig-beta", 0.6, hours_ago=0.0),
        ]
        result = extrapolate_hazard_trend(signals, category="hydrology")
        assert "sig-alpha" in result.details.get("signal_ids", [])
        assert "sig-beta" in result.details.get("signal_ids", [])
