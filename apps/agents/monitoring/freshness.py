"""Data freshness tracking service — per-source health monitoring.

Implements the four status transition rules from data-model.md:
- healthy → degraded: No signal for ``staleness_threshold_minutes``
- degraded → offline: No signal for ``2 × staleness_threshold_minutes``
- degraded → healthy: Signal received with ``freshnessScore >= 0.5``
- offline → healthy: Signal received with ``freshnessScore >= 0.5``
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from monitoring.config import MonitoringConfig
from monitoring.models import DataFreshnessIndicator, FreshnessStatus, SourceType

logger = logging.getLogger(__name__)


@dataclass
class StatusChange:
    """Describes a freshness status transition for a data source."""

    data_source_id: str
    source_type: str
    previous_status: FreshnessStatus
    new_status: FreshnessStatus
    changed_at: datetime


class DataFreshnessTracker:
    """Manages per-source ``DataFreshnessIndicator`` instances."""

    def __init__(self, config: MonitoringConfig | None = None) -> None:
        self._config = config or MonitoringConfig()
        self._indicators: dict[str, DataFreshnessIndicator] = {}

    def update(
        self,
        data_source_id: str,
        source_type: str,
        freshness_score: float,
    ) -> StatusChange | None:
        """Update freshness for a source and return a ``StatusChange`` if status transitions."""
        now = datetime.now(UTC)

        # Resolve staleness threshold
        threshold = self._config.staleness_threshold_for(source_type)

        # Resolve SourceType enum
        try:
            st = SourceType(source_type)
        except ValueError:
            st = SourceType.social  # default fallback

        if data_source_id not in self._indicators:
            self._indicators[data_source_id] = DataFreshnessIndicator(
                data_source_id=data_source_id,
                source_type=st,
                last_signal_received_at=now,
                current_freshness_score=freshness_score,
                staleness_threshold_minutes=threshold,
                status=FreshnessStatus.healthy,
                last_status_change_at=now,
            )
            return None  # first signal — no transition

        indicator = self._indicators[data_source_id]
        old_status = indicator.status

        # Update reception time and freshness score
        indicator.last_signal_received_at = now
        indicator.current_freshness_score = freshness_score

        # Determine new status
        new_status = old_status
        if freshness_score >= 0.5 and old_status in (FreshnessStatus.degraded, FreshnessStatus.offline):
            new_status = FreshnessStatus.healthy
        elif freshness_score < 0.5 and old_status == FreshnessStatus.healthy:
            new_status = FreshnessStatus.degraded

        if new_status != old_status:
            indicator.status = new_status
            indicator.last_status_change_at = now
            change = StatusChange(
                data_source_id=data_source_id,
                source_type=source_type,
                previous_status=old_status,
                new_status=new_status,
                changed_at=now,
            )
            logger.info(
                "Data source %s status changed: %s → %s",
                data_source_id,
                old_status.value,
                new_status.value,
            )
            return change

        return None

    def check_staleness(self) -> list[StatusChange]:
        """Check all sources for staleness-based degradation (time-driven)."""
        now = datetime.now(UTC)
        changes: list[StatusChange] = []

        for indicator in self._indicators.values():
            elapsed = now - indicator.last_signal_received_at
            threshold = timedelta(minutes=indicator.staleness_threshold_minutes)
            old_status = indicator.status

            if indicator.status == FreshnessStatus.healthy and elapsed >= threshold:
                indicator.status = FreshnessStatus.degraded
                indicator.last_status_change_at = now
            elif indicator.status == FreshnessStatus.degraded and elapsed >= (threshold * 2):
                indicator.status = FreshnessStatus.offline
                indicator.last_status_change_at = now

            if indicator.status != old_status:
                changes.append(
                    StatusChange(
                        data_source_id=indicator.data_source_id,
                        source_type=indicator.source_type.value,
                        previous_status=old_status,
                        new_status=indicator.status,
                        changed_at=now,
                    )
                )

        return changes

    def get_status(self, data_source_id: str) -> DataFreshnessIndicator | None:
        """Return the freshness indicator for a specific source, or None."""
        return self._indicators.get(data_source_id)

    def get_all_indicators(self) -> list[DataFreshnessIndicator]:
        """Return all tracked freshness indicators."""
        return list(self._indicators.values())

    def get_summary_status(self) -> str:
        """Return aggregate freshness: 'healthy' or 'degraded'."""
        if not self._indicators:
            return "healthy"
        for indicator in self._indicators.values():
            if indicator.status != FreshnessStatus.healthy:
                return "degraded"
        return "healthy"
