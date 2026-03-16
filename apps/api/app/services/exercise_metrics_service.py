"""Exercise metrics service for scenario replay instrumentation.

Captures KPIs from rehearsal runs and compares baseline vs hub-enabled results
for success criteria SC-004 through SC-007.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ExerciseKPI(BaseModel):
    exercise_id: str
    scenario_type: str
    jurisdiction_id: str
    organisation_ids: list[str] = Field(default_factory=list)
    run_type: str  # "baseline" or "hub_enabled"
    timestamp_activation: datetime
    timestamp_first_coordinated_action: datetime | None = None
    timestamp_evacuation_decision: datetime | None = None
    time_to_assignment_minutes: float | None = None
    resource_utilization_ratio: float | None = None
    unfilled_priority_requests: int | None = None
    ux_clarity_mean: float | None = None
    ux_scanability_mean: float | None = None
    ux_distinctiveness_mean: float | None = None
    ux_decision_confidence_mean: float | None = None
    participant_count: int | None = None
    org_type_count: int | None = None
    persona_type_count: int | None = None


class ExerciseMetricsService:
    def __init__(self) -> None:
        self._records: list[ExerciseKPI] = []

    def record(self, kpi: ExerciseKPI) -> ExerciseKPI:
        self._records.append(kpi)
        return kpi

    def compare(self, baseline_id: str, hub_id: str) -> dict[str, Any]:
        baseline = next((r for r in self._records if r.exercise_id == baseline_id), None)
        hub = next((r for r in self._records if r.exercise_id == hub_id), None)

        if baseline is None or hub is None:
            return {"error": "Missing exercise record"}

        results: dict[str, Any] = {
            "baseline_id": baseline_id,
            "hub_id": hub_id,
            "scenario_type": baseline.scenario_type,
        }

        # SC-004: Coordinated response time improvement
        if baseline.timestamp_first_coordinated_action and hub.timestamp_first_coordinated_action:
            baseline_minutes = (baseline.timestamp_first_coordinated_action - baseline.timestamp_activation).total_seconds() / 60
            hub_minutes = (hub.timestamp_first_coordinated_action - hub.timestamp_activation).total_seconds() / 60
            improvement = ((baseline_minutes - hub_minutes) / baseline_minutes) * 100 if baseline_minutes > 0 else 0
            results["sc004_response_time"] = {
                "baseline_minutes": round(baseline_minutes, 1),
                "hub_minutes": round(hub_minutes, 1),
                "improvement_percent": round(improvement, 1),
                "passes": improvement >= 50,
            }

        # SC-005: Evacuation decision timing improvement
        if baseline.timestamp_evacuation_decision and hub.timestamp_evacuation_decision:
            baseline_hours = (baseline.timestamp_evacuation_decision - baseline.timestamp_activation).total_seconds() / 3600
            hub_hours = (hub.timestamp_evacuation_decision - hub.timestamp_activation).total_seconds() / 3600
            hours_earlier = baseline_hours - hub_hours
            results["sc005_evacuation_timing"] = {
                "baseline_hours": round(baseline_hours, 1),
                "hub_hours": round(hub_hours, 1),
                "hours_earlier": round(hours_earlier, 1),
                "passes": hours_earlier >= 24,
            }

        # SC-006: Resource deployment efficiency
        if baseline.time_to_assignment_minutes is not None and hub.time_to_assignment_minutes is not None:
            time_improvement = ((baseline.time_to_assignment_minutes - hub.time_to_assignment_minutes) / baseline.time_to_assignment_minutes) * 100 if baseline.time_to_assignment_minutes > 0 else 0
            results["sc006_resource_efficiency"] = {
                "baseline_assignment_minutes": baseline.time_to_assignment_minutes,
                "hub_assignment_minutes": hub.time_to_assignment_minutes,
                "improvement_percent": round(time_improvement, 1),
                "passes": time_improvement >= 30,
            }

        # SC-007: UX evaluation
        if hub.ux_clarity_mean is not None:
            ux_means = [
                hub.ux_clarity_mean,
                hub.ux_scanability_mean or 0,
                hub.ux_distinctiveness_mean or 0,
                hub.ux_decision_confidence_mean or 0,
            ]
            overall_mean = sum(ux_means) / len(ux_means)
            passes_threshold = all(m >= 4.0 for m in ux_means)
            meets_coverage = (hub.org_type_count or 0) >= 3 and (hub.persona_type_count or 0) >= 5
            results["sc007_ux_evaluation"] = {
                "clarity_mean": hub.ux_clarity_mean,
                "scanability_mean": hub.ux_scanability_mean,
                "distinctiveness_mean": hub.ux_distinctiveness_mean,
                "decision_confidence_mean": hub.ux_decision_confidence_mean,
                "overall_mean": round(overall_mean, 2),
                "all_dimensions_above_4": passes_threshold,
                "coverage_met": meets_coverage,
                "passes": passes_threshold and meets_coverage,
            }

        # Overall verdict
        sc_results = [v for k, v in results.items() if k.startswith("sc") and isinstance(v, dict)]
        results["overall_pass"] = all(r.get("passes", False) for r in sc_results) if sc_results else False

        return results
