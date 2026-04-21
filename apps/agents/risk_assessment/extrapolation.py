"""Time-series extrapolation for predictive hazard assessment.

Implements a linear extrapolation stage that projects current signal trends
forward to estimate when hazard thresholds will be breached. This provides
the "predictive lead time" that supports the 24-hour advance evacuation
success criterion (SC-005).

The approach is deliberately simple — linear regression over recent signal
observations — to stay deterministic, auditable, and independent of external
ML services. For production use, this would be supplemented by upstream
forecast feeds (e.g. FFWC 5-day flood forecasts, JMA 72-hour typhoon tracks).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

logger = logging.getLogger(__name__)

CATEGORY_THRESHOLDS: dict[str, dict[str, float]] = {
    "hydrology": {"advisory": 0.4, "watch": 0.6, "warning": 0.8, "emergency": 0.95},
    "weather": {"advisory": 0.4, "watch": 0.6, "warning": 0.8, "emergency": 0.95},
    "fire": {"advisory": 0.3, "watch": 0.5, "warning": 0.7, "emergency": 0.90},
    "geohazard": {"advisory": 0.3, "watch": 0.5, "warning": 0.7, "emergency": 0.85},
}

DEFAULT_THRESHOLDS: dict[str, float] = {
    "advisory": 0.4,
    "watch": 0.6,
    "warning": 0.8,
    "emergency": 0.95,
}

MAX_EXTRAPOLATION_HOURS = 72


@dataclass
class TrendPoint:
    """A single observation in the trend series."""

    timestamp: datetime
    value: float
    signal_id: str


@dataclass
class ExtrapolationResult:
    """Result of time-series extrapolation over recent signals."""

    trend_detected: bool = False
    trend_direction: str = "stable"  # "increasing", "decreasing", "stable"
    slope_per_hour: float = 0.0
    current_value: float = 0.0
    projected_value_24h: float = 0.0
    projected_value_48h: float = 0.0
    hours_to_warning_threshold: float | None = None
    hours_to_emergency_threshold: float | None = None
    predictive_lead_time_hours: float = 0.0
    data_points_used: int = 0
    extrapolation_confidence: float = 0.0
    category: str = ""
    details: dict = field(default_factory=dict)


def _extract_trend_points(signals: list[dict]) -> list[TrendPoint]:
    """Extract timestamped confidence values from signals for trend analysis."""
    points: list[TrendPoint] = []

    for sig in signals:
        signal_id = sig.get("signal_id", "unknown")
        confidence = float(sig.get("confidence_score", 0.0))
        freshness = float(sig.get("freshness_score", 1.0))
        effective_value = confidence * freshness

        provenance = sig.get("provenance", {})
        ts_str = provenance.get("sourceTimestamp") or provenance.get("receivedAt")

        if ts_str and isinstance(ts_str, str):
            try:
                ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
            except (ValueError, TypeError):
                ts = datetime.now(UTC)
        else:
            ts = datetime.now(UTC)

        points.append(TrendPoint(timestamp=ts, value=effective_value, signal_id=signal_id))

    points.sort(key=lambda p: p.timestamp)
    return points


def _linear_regression(points: list[TrendPoint]) -> tuple[float, float]:
    """Compute slope (per hour) and intercept from trend points.

    Uses simple least-squares regression with time in hours from the first point.
    Returns (slope_per_hour, intercept).
    """
    if len(points) < 2:
        return 0.0, points[0].value if points else 0.0

    t0 = points[0].timestamp
    n = len(points)
    xs = [(p.timestamp - t0).total_seconds() / 3600.0 for p in points]
    ys = [p.value for p in points]

    sum_x = sum(xs)
    sum_y = sum(ys)
    sum_xx = sum(x * x for x in xs)
    sum_xy = sum(x * y for x, y in zip(xs, ys))

    denom = n * sum_xx - sum_x * sum_x
    if abs(denom) < 1e-12:
        return 0.0, sum_y / n

    slope = (n * sum_xy - sum_x * sum_y) / denom
    intercept = (sum_y - slope * sum_x) / n
    return slope, intercept


def _hours_to_threshold(current: float, slope: float, threshold: float) -> float | None:
    """Calculate hours until a threshold is reached given current value and slope.

    Returns None if the threshold is already breached or the trend moves away from it.
    """
    if slope <= 0:
        return None
    if current >= threshold:
        return 0.0

    gap = threshold - current
    hours = gap / slope

    if hours > MAX_EXTRAPOLATION_HOURS:
        return None

    return round(hours, 1)


def _r_squared(points: list[TrendPoint], slope: float, intercept: float) -> float:
    """Compute R² goodness of fit for the linear model."""
    if len(points) < 2:
        return 0.0

    t0 = points[0].timestamp
    ys = [p.value for p in points]
    mean_y = sum(ys) / len(ys)

    ss_tot = sum((y - mean_y) ** 2 for y in ys)
    if ss_tot < 1e-12:
        return 1.0

    ss_res = 0.0
    for p in points:
        hours = (p.timestamp - t0).total_seconds() / 3600.0
        predicted = intercept + slope * hours
        ss_res += (p.value - predicted) ** 2

    return max(0.0, 1.0 - ss_res / ss_tot)


def extrapolate_hazard_trend(
    signals: list[dict],
    category: str = "",
    min_points: int = 2,
) -> ExtrapolationResult:
    """Extrapolate the hazard trend from a sequence of signals.

    Performs linear regression on signal confidence × freshness values over time
    to project when warning/emergency thresholds may be breached.

    Args:
        signals: List of signal dicts with confidence_score, freshness_score, provenance.
        category: Signal category for threshold lookup (hydrology, fire, etc.).
        min_points: Minimum data points required for extrapolation.

    Returns:
        ExtrapolationResult with trend direction, projected values, and lead times.
    """
    points = _extract_trend_points(signals)

    if len(points) < min_points:
        return ExtrapolationResult(
            data_points_used=len(points),
            current_value=points[-1].value if points else 0.0,
            category=category,
            details={"reason": f"Insufficient data points ({len(points)} < {min_points})"},
        )

    slope, intercept = _linear_regression(points)
    r_sq = _r_squared(points, slope, intercept)

    current_value = points[-1].value
    t0 = points[0].timestamp
    hours_since_t0 = (points[-1].timestamp - t0).total_seconds() / 3600.0

    projected_24h = max(0.0, min(1.0, intercept + slope * (hours_since_t0 + 24.0)))
    projected_48h = max(0.0, min(1.0, intercept + slope * (hours_since_t0 + 48.0)))

    # Determine trend direction
    slope_threshold = 0.001
    if slope > slope_threshold:
        direction = "increasing"
    elif slope < -slope_threshold:
        direction = "decreasing"
    else:
        direction = "stable"

    thresholds = CATEGORY_THRESHOLDS.get(category, DEFAULT_THRESHOLDS)

    hours_to_warning = _hours_to_threshold(current_value, slope, thresholds["warning"])
    hours_to_emergency = _hours_to_threshold(current_value, slope, thresholds["emergency"])

    # Predictive lead time: hours until warning threshold breach
    lead_time = hours_to_warning if hours_to_warning is not None else 0.0

    # Extrapolation confidence degrades with fewer points and poor fit
    point_factor = min(1.0, len(points) / 5.0)
    extrapolation_confidence = round(r_sq * point_factor, 3)

    return ExtrapolationResult(
        trend_detected=direction != "stable",
        trend_direction=direction,
        slope_per_hour=round(slope, 6),
        current_value=round(current_value, 3),
        projected_value_24h=round(projected_24h, 3),
        projected_value_48h=round(projected_48h, 3),
        hours_to_warning_threshold=hours_to_warning,
        hours_to_emergency_threshold=hours_to_emergency,
        predictive_lead_time_hours=round(lead_time, 1),
        data_points_used=len(points),
        extrapolation_confidence=extrapolation_confidence,
        category=category,
        details={
            "slope_per_hour": round(slope, 6),
            "intercept": round(intercept, 4),
            "r_squared": round(r_sq, 4),
            "time_span_hours": round(hours_since_t0, 2),
            "signal_ids": [p.signal_id for p in points],
            "warning_threshold": thresholds["warning"],
            "emergency_threshold": thresholds["emergency"],
        },
    )
