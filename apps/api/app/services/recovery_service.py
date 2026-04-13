"""Community recovery tracking service.

Manages recovery environment trackers with 21 AIDR-defined indicators
across four environments (social, built, economic, natural).
Enforces k-anonymity for sensitive social indicators.

FRs: FR-032–037 | SCs: SC-005 | Research: R-003, R-008, R-012
"""

from datetime import UTC, datetime
from uuid import uuid4

from packages.domain.src.domain.models.recovery_environment_tracker import (
    AIDR_INDICATORS,
    ALL_INDICATOR_NAMES,
    SENSITIVE_SOCIAL_INDICATORS,
    RecoveryEnvironmentTracker,
    RecoveryIndicator,
)

from app.services.state_store import INCIDENTS, RECOVERY_TRACKERS


class RecoveryService:
    """Manages recovery environment trackers and indicator updates."""

    def initialise_tracker(self, incident_id: str) -> RecoveryEnvironmentTracker:
        if incident_id not in INCIDENTS:
            msg = f"Incident '{incident_id}' not found"
            raise KeyError(msg)

        if incident_id in RECOVERY_TRACKERS:
            msg = f"Tracker already exists for incident '{incident_id}'"
            raise ValueError(msg)

        indicators: list[RecoveryIndicator] = []
        for environment, names in AIDR_INDICATORS.items():
            for name in names:
                classification = (
                    "sensitive"
                    if name in SENSITIVE_SOCIAL_INDICATORS
                    else "public"
                )
                indicators.append(
                    RecoveryIndicator(
                        indicator_name=name,
                        environment=environment,  # type: ignore[arg-type]
                        value=None,
                        baseline_value=None,
                        data_classification=classification,  # type: ignore[arg-type]
                    ),
                )

        tracker = RecoveryEnvironmentTracker(
            tracker_id=str(uuid4()),
            incident_id=incident_id,
            indicators=indicators,
        )
        RECOVERY_TRACKERS[incident_id] = tracker
        return tracker

    def get_dashboard(self, incident_id: str) -> dict:
        if incident_id not in RECOVERY_TRACKERS:
            msg = f"No recovery tracker for incident '{incident_id}'"
            raise KeyError(msg)

        tracker = RECOVERY_TRACKERS[incident_id]
        grouped: dict[str, list[dict]] = {}
        for ind in tracker.indicators:
            grouped.setdefault(ind.environment, []).append(
                ind.model_dump(mode="json"),
            )

        regression_count = sum(1 for i in tracker.indicators if i.is_regressed)
        populated_count = sum(1 for i in tracker.indicators if i.value is not None)

        return {
            "tracker_id": tracker.tracker_id,
            "incident_id": incident_id,
            "status": tracker.status,
            "total_indicators": len(tracker.indicators),
            "populated_indicators": populated_count,
            "regression_count": regression_count,
            "environments": grouped,
        }

    def update_indicator(
        self,
        incident_id: str,
        indicator_name: str,
        value: float,
        update_source: str = "manual",
        population_coverage: int | None = None,
        linked_alert_id: str | None = None,
    ) -> dict:
        if incident_id not in RECOVERY_TRACKERS:
            msg = f"No recovery tracker for incident '{incident_id}'"
            raise KeyError(msg)
        if indicator_name not in ALL_INDICATOR_NAMES:
            msg = f"Unknown indicator: '{indicator_name}'"
            raise ValueError(msg)

        tracker = RECOVERY_TRACKERS[incident_id]
        target = next(
            (i for i in tracker.indicators if i.indicator_name == indicator_name),
            None,
        )
        if target is None:
            msg = f"Indicator '{indicator_name}' not found in tracker"
            raise KeyError(msg)

        # Enforce k-anonymity for sensitive social indicators
        if (
            target.data_classification == "sensitive"
            and population_coverage is not None
            and population_coverage < 10
        ):
            msg = (
                f"population_coverage must be ≥ 10 for sensitive indicator "
                f"'{indicator_name}' (k-anonymity requirement)"
            )
            raise ValueError(msg)

        is_regressed = self.check_regression_values(target.baseline_value, value)

        updates: dict = {
            "value": value,
            "last_updated_at": datetime.now(UTC),
            "update_source": update_source,
            "is_regressed": is_regressed,
        }
        if is_regressed:
            updates["regression_cause"] = "Value below baseline"
        if population_coverage is not None:
            updates["population_coverage"] = population_coverage
        if linked_alert_id is not None:
            updates["linked_alert_id"] = linked_alert_id

        updated_indicator = target.model_copy(update=updates)
        idx = tracker.indicators.index(target)
        tracker.indicators[idx] = updated_indicator
        tracker.updated_at = datetime.now(UTC)

        return {
            "indicator_name": indicator_name,
            "value": value,
            "is_regressed": is_regressed,
            "previous_value": target.value,
        }

    def batch_update_indicators(
        self,
        incident_id: str,
        updates: list[dict],
    ) -> dict:
        results = []
        errors = []
        for item in updates:
            try:
                result = self.update_indicator(
                    incident_id=incident_id,
                    indicator_name=item["indicator_name"],
                    value=item["value"],
                    update_source=item.get("update_source", "manual"),
                    population_coverage=item.get("population_coverage"),
                    linked_alert_id=item.get("linked_alert_id"),
                )
                results.append(result)
            except (KeyError, ValueError) as exc:
                errors.append({
                    "indicator_name": item.get("indicator_name"),
                    "error": str(exc),
                })
        return {
            "updated": len(results),
            "failed": len(errors),
            "results": results,
            "errors": errors,
        }

    def get_community_view(self, incident_id: str) -> dict:
        """Public-safe view filtering out sensitive indicators."""
        if incident_id not in RECOVERY_TRACKERS:
            msg = f"No recovery tracker for incident '{incident_id}'"
            raise KeyError(msg)

        tracker = RECOVERY_TRACKERS[incident_id]
        grouped: dict[str, list[dict]] = {}
        for ind in tracker.indicators:
            if ind.data_classification == "sensitive":
                continue
            grouped.setdefault(ind.environment, []).append(
                ind.model_dump(mode="json"),
            )

        return {
            "tracker_id": tracker.tracker_id,
            "incident_id": incident_id,
            "status": tracker.status,
            "environments": grouped,
        }

    def check_regression(self, indicator: RecoveryIndicator) -> bool:
        return self.check_regression_values(indicator.baseline_value, indicator.value)

    @staticmethod
    def check_regression_values(
        baseline: float | None, value: float | None,
    ) -> bool:
        if baseline is None or value is None:
            return False
        return value < baseline
