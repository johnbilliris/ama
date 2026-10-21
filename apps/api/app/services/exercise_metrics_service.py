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
    ux_participant_scores: list[dict[str, float]] = Field(default_factory=list)
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
        if baseline.run_type != "baseline" or hub.run_type != "hub_enabled":
            return {"error": "Invalid run_type pairing"}

        baseline_orgs = sorted(baseline.organisation_ids)
        hub_orgs = sorted(hub.organisation_ids)
        if (
            baseline.scenario_type != hub.scenario_type
            or baseline.jurisdiction_id != hub.jurisdiction_id
            or baseline_orgs != hub_orgs
        ):
            return {"error": "Mismatched baseline/hub cohort"}

        criteria: dict[str, dict[str, Any]] = {}
        prefix = "001-disaster-response-hub"

        criteria[f"{prefix}:SC-001"] = self._criterion(
            baseline.org_type_count is not None and hub.org_type_count is not None,
            (hub.org_type_count or 0) >= 3,
            {"org_type_count": hub.org_type_count},
        )
        criteria[f"{prefix}:SC-002"] = self._criterion(
            baseline.persona_type_count is not None and hub.persona_type_count is not None,
            (hub.persona_type_count or 0) >= 5,
            {"persona_type_count": hub.persona_type_count},
        )
        criteria[f"{prefix}:SC-003"] = self._criterion(
            hub.participant_count is not None,
            (hub.participant_count or 0) >= 5,
            {"participant_count": hub.participant_count},
        )

        criteria[f"{prefix}:SC-004"] = self._sc004(baseline, hub)
        criteria[f"{prefix}:SC-005"] = self._sc005(baseline, hub)
        criteria[f"{prefix}:SC-006"] = self._sc006(baseline, hub)
        criteria[f"{prefix}:SC-007"] = self._sc007(hub)

        statuses = [entry["status"] for entry in criteria.values()]
        overall_pass = all(status == "pass" for status in statuses)

        return {
            "spec_id": prefix,
            "baseline_id": baseline_id,
            "hub_id": hub_id,
            "scenario_type": baseline.scenario_type,
            "jurisdiction_id": baseline.jurisdiction_id,
            "criteria": criteria,
            "overall_pass": overall_pass,
        }

    @staticmethod
    def _criterion(complete: bool, passed: bool, details: dict[str, Any]) -> dict[str, Any]:
        if not complete:
            return {"status": "incomplete", "passes": False, "details": details}
        return {"status": "pass" if passed else "fail", "passes": passed, "details": details}

    def _sc004(self, baseline: ExerciseKPI, hub: ExerciseKPI) -> dict[str, Any]:
        if not baseline.timestamp_first_coordinated_action or not hub.timestamp_first_coordinated_action:
            return self._criterion(False, False, {})
        baseline_minutes = (
            baseline.timestamp_first_coordinated_action - baseline.timestamp_activation
        ).total_seconds() / 60
        hub_minutes = (hub.timestamp_first_coordinated_action - hub.timestamp_activation).total_seconds() / 60
        improvement = ((baseline_minutes - hub_minutes) / baseline_minutes) * 100 if baseline_minutes > 0 else 0.0
        return self._criterion(
            True,
            improvement >= 50.0,
            {
                "baseline_minutes": round(baseline_minutes, 1),
                "hub_minutes": round(hub_minutes, 1),
                "improvement_percent": round(improvement, 1),
            },
        )

    def _sc005(self, baseline: ExerciseKPI, hub: ExerciseKPI) -> dict[str, Any]:
        if not baseline.timestamp_evacuation_decision or not hub.timestamp_evacuation_decision:
            return self._criterion(False, False, {})
        baseline_hours = (baseline.timestamp_evacuation_decision - baseline.timestamp_activation).total_seconds() / 3600
        hub_hours = (hub.timestamp_evacuation_decision - hub.timestamp_activation).total_seconds() / 3600
        hours_earlier = baseline_hours - hub_hours
        return self._criterion(
            True,
            hours_earlier >= 24.0,
            {
                "baseline_hours": round(baseline_hours, 1),
                "hub_hours": round(hub_hours, 1),
                "hours_earlier": round(hours_earlier, 1),
            },
        )

    def _sc006(self, baseline: ExerciseKPI, hub: ExerciseKPI) -> dict[str, Any]:
        baseline_assignment = baseline.time_to_assignment_minutes
        hub_assignment = hub.time_to_assignment_minutes
        baseline_utilization = baseline.resource_utilization_ratio
        hub_utilization = hub.resource_utilization_ratio
        baseline_unfilled = baseline.unfilled_priority_requests
        hub_unfilled = hub.unfilled_priority_requests
        if any(
            value is None
            for value in (
                baseline_assignment,
                hub_assignment,
                baseline_utilization,
                hub_utilization,
                baseline_unfilled,
                hub_unfilled,
            )
        ):
            return self._criterion(False, False, {})
        if (
            baseline_assignment is None
            or hub_assignment is None
            or baseline_utilization is None
            or hub_utilization is None
            or baseline_unfilled is None
            or hub_unfilled is None
        ):
            return self._criterion(False, False, {})

        assignment_improvement = (
            ((baseline_assignment - hub_assignment) / baseline_assignment) * 100 if baseline_assignment > 0 else 0.0
        )
        utilization_improvement = (
            ((hub_utilization - baseline_utilization) / baseline_utilization) * 100 if baseline_utilization > 0 else 0.0
        )
        unfilled_reduction = (
            ((baseline_unfilled - hub_unfilled) / baseline_unfilled) * 100
            if baseline_unfilled > 0
            else (100.0 if hub_unfilled == 0 else 0.0)
        )

        weighted_composite = (
            (0.4 * assignment_improvement) + (0.3 * utilization_improvement) + (0.3 * unfilled_reduction)
        )
        return self._criterion(
            True,
            weighted_composite >= 30.0,
            {
                "assignment_improvement_percent": round(assignment_improvement, 1),
                "utilization_improvement_percent": round(utilization_improvement, 1),
                "unfilled_reduction_percent": round(unfilled_reduction, 1),
                "weighted_composite_percent": round(weighted_composite, 1),
            },
        )

    def _sc007(self, hub: ExerciseKPI) -> dict[str, Any]:
        participant_scores = hub.ux_participant_scores
        participant_count = hub.participant_count or len(participant_scores)
        if participant_count <= 0 or len(participant_scores) <= 0:
            return self._criterion(False, False, {})

        dimensions = (
            "clarity",
            "scanability",
            "distinctiveness",
            "decision_confidence",
        )
        proportions: dict[str, float] = {}
        per_dimension_pass: dict[str, bool] = {}
        for dimension in dimensions:
            values: list[float] = []
            for row in participant_scores:
                value = row.get(dimension)
                if value is not None:
                    values.append(value)
            if not values:
                return self._criterion(False, False, {})
            favourable = sum(1 for value in values if value >= 4.0)
            proportion = favourable / len(values)
            proportions[dimension] = round(proportion * 100.0, 1)
            per_dimension_pass[dimension] = proportion >= 0.85

        passes = (
            all(per_dimension_pass.values()) and (hub.org_type_count or 0) >= 3 and (hub.persona_type_count or 0) >= 5
        )
        details = {
            "participant_count": participant_count,
            "favourable_percent": proportions,
            "per_dimension_pass": per_dimension_pass,
            "coverage_met": (hub.org_type_count or 0) >= 3 and (hub.persona_type_count or 0) >= 5,
        }
        return self._criterion(True, passes, details)
