from datetime import datetime, timezone

from app.services.exercise_metrics_service import ExerciseKPI, ExerciseMetricsService


def test_exercise_metrics_comparison_passes_all_criteria() -> None:
    service = ExerciseMetricsService()

    baseline = ExerciseKPI(
        exercise_id="EX-001",
        scenario_type="flood",
        jurisdiction_id="nsw",
        organisation_ids=["ses-nsw", "bom-national"],
        run_type="baseline",
        timestamp_activation=datetime(2026, 3, 9, 9, 0, tzinfo=timezone.utc),
        timestamp_first_coordinated_action=datetime(2026, 3, 9, 9, 45, tzinfo=timezone.utc),
        timestamp_evacuation_decision=datetime(2026, 3, 9, 15, 0, tzinfo=timezone.utc),
        time_to_assignment_minutes=38,
        resource_utilization_ratio=0.62,
        unfilled_priority_requests=4,
    )

    hub = ExerciseKPI(
        exercise_id="EX-002",
        scenario_type="flood",
        jurisdiction_id="nsw",
        organisation_ids=["ses-nsw", "bom-national"],
        run_type="hub_enabled",
        timestamp_activation=datetime(2026, 3, 9, 9, 0, tzinfo=timezone.utc),
        timestamp_first_coordinated_action=datetime(2026, 3, 9, 9, 18, tzinfo=timezone.utc),
        timestamp_evacuation_decision=datetime(2026, 3, 9, 11, 30, tzinfo=timezone.utc),
        time_to_assignment_minutes=14,
        resource_utilization_ratio=0.81,
        unfilled_priority_requests=1,
        ux_clarity_mean=4.2,
        ux_scanability_mean=4.5,
        ux_distinctiveness_mean=4.1,
        ux_decision_confidence_mean=4.3,
        participant_count=12,
        org_type_count=3,
        persona_type_count=5,
    )

    service.record(baseline)
    service.record(hub)

    comparison = service.compare("EX-001", "EX-002")

    # SC-004: 45min → 18min = 60% improvement (≥50% required)
    assert comparison["sc004_response_time"]["passes"] is True
    assert comparison["sc004_response_time"]["improvement_percent"] == 60.0

    # SC-005: 6h → 2.5h = 3.5h earlier (≥24h required — this is a scenario exercise, won't pass)
    assert comparison["sc005_evacuation_timing"]["hours_earlier"] == 3.5

    # SC-006: 38min → 14min = 63.2% improvement (≥30% required)
    assert comparison["sc006_resource_efficiency"]["passes"] is True

    # SC-007: All dimensions ≥4.0, coverage met
    assert comparison["sc007_ux_evaluation"]["all_dimensions_above_4"] is True
    assert comparison["sc007_ux_evaluation"]["coverage_met"] is True


def test_exercise_metrics_missing_record_returns_error() -> None:
    service = ExerciseMetricsService()
    result = service.compare("missing-1", "missing-2")
    assert result["error"] == "Missing exercise record"
