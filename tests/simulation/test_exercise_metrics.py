from datetime import UTC, datetime

from app.services.exercise_metrics_service import ExerciseKPI, ExerciseMetricsService


def _participant_rows(favourable_rate: float, count: int = 20) -> list[dict[str, float]]:
    favourable = int(count * favourable_rate)
    rows: list[dict[str, float]] = []
    for i in range(count):
        score = 4.0 if i < favourable else 3.0
        rows.append(
            {
                "clarity": score,
                "scanability": score,
                "distinctiveness": score,
                "decision_confidence": score,
            }
        )
    return rows


def test_exercise_metrics_comparison_all_criteria_keys_present_and_overall_false_on_sc005() -> None:
    service = ExerciseMetricsService()

    baseline = ExerciseKPI(
        exercise_id="EX-001",
        scenario_type="flood",
        jurisdiction_id="nsw",
        organisation_ids=["ses-nsw", "bom-national"],
        run_type="baseline",
        timestamp_activation=datetime(2026, 3, 9, 9, 0, tzinfo=UTC),
        timestamp_first_coordinated_action=datetime(2026, 3, 9, 9, 45, tzinfo=UTC),
        timestamp_evacuation_decision=datetime(2026, 3, 9, 15, 0, tzinfo=UTC),
        time_to_assignment_minutes=38,
        resource_utilization_ratio=0.62,
        unfilled_priority_requests=4,
        org_type_count=3,
        persona_type_count=5,
    )

    hub = ExerciseKPI(
        exercise_id="EX-002",
        scenario_type="flood",
        jurisdiction_id="nsw",
        organisation_ids=["ses-nsw", "bom-national"],
        run_type="hub_enabled",
        timestamp_activation=datetime(2026, 3, 9, 9, 0, tzinfo=UTC),
        timestamp_first_coordinated_action=datetime(2026, 3, 9, 9, 18, tzinfo=UTC),
        timestamp_evacuation_decision=datetime(2026, 3, 9, 11, 30, tzinfo=UTC),
        time_to_assignment_minutes=14,
        resource_utilization_ratio=0.81,
        unfilled_priority_requests=1,
        ux_clarity_mean=4.2,
        ux_scanability_mean=4.5,
        ux_distinctiveness_mean=4.1,
        ux_decision_confidence_mean=4.3,
        ux_participant_scores=_participant_rows(0.9),
        participant_count=12,
        org_type_count=3,
        persona_type_count=5,
    )

    service.record(baseline)
    service.record(hub)

    comparison = service.compare("EX-001", "EX-002")
    criteria = comparison["criteria"]
    prefix = "001-disaster-response-hub"

    assert len(criteria) == 7
    assert criteria[f"{prefix}:SC-004"]["passes"] is True
    assert criteria[f"{prefix}:SC-004"]["details"]["improvement_percent"] == 60.0

    assert criteria[f"{prefix}:SC-005"]["details"]["hours_earlier"] == 3.5
    assert criteria[f"{prefix}:SC-005"]["status"] == "fail"

    expected_sc006 = (0.4 * 63.1578947368) + (0.3 * 30.6451612903) + (0.3 * 75.0)
    assert criteria[f"{prefix}:SC-006"]["details"]["weighted_composite_percent"] == round(expected_sc006, 1)
    assert criteria[f"{prefix}:SC-006"]["passes"] is True

    assert criteria[f"{prefix}:SC-007"]["details"]["coverage_met"] is True
    assert criteria[f"{prefix}:SC-007"]["passes"] is True
    assert comparison["overall_pass"] is False


def test_exercise_metrics_missing_record_returns_error() -> None:
    service = ExerciseMetricsService()
    result = service.compare("missing-1", "missing-2")
    assert result["error"] == "Missing exercise record"


def test_exercise_metrics_rejects_mismatched_cohort() -> None:
    service = ExerciseMetricsService()
    service.record(
        ExerciseKPI(
            exercise_id="BASE-1",
            scenario_type="flood",
            jurisdiction_id="nsw",
            organisation_ids=["ses-nsw"],
            run_type="baseline",
            timestamp_activation=datetime(2026, 3, 9, 9, 0, tzinfo=UTC),
        )
    )
    service.record(
        ExerciseKPI(
            exercise_id="HUB-1",
            scenario_type="cyclone",
            jurisdiction_id="qld",
            organisation_ids=["ses-qld"],
            run_type="hub_enabled",
            timestamp_activation=datetime(2026, 3, 9, 9, 0, tzinfo=UTC),
        )
    )
    result = service.compare("BASE-1", "HUB-1")
    assert result["error"] == "Mismatched baseline/hub cohort"


def test_sc007_uses_participant_favourable_proportion_not_means() -> None:
    service = ExerciseMetricsService()
    baseline = ExerciseKPI(
        exercise_id="BASE-UX",
        scenario_type="flood",
        jurisdiction_id="nsw",
        organisation_ids=["ses-nsw"],
        run_type="baseline",
        timestamp_activation=datetime(2026, 3, 9, 9, 0, tzinfo=UTC),
        org_type_count=3,
        persona_type_count=5,
    )
    hub = ExerciseKPI(
        exercise_id="HUB-UX",
        scenario_type="flood",
        jurisdiction_id="nsw",
        organisation_ids=["ses-nsw"],
        run_type="hub_enabled",
        timestamp_activation=datetime(2026, 3, 9, 9, 0, tzinfo=UTC),
        ux_clarity_mean=4.8,
        ux_scanability_mean=4.8,
        ux_distinctiveness_mean=4.8,
        ux_decision_confidence_mean=4.8,
        ux_participant_scores=_participant_rows(0.8),
        participant_count=20,
        org_type_count=3,
        persona_type_count=5,
    )
    service.record(baseline)
    service.record(hub)
    result = service.compare("BASE-UX", "HUB-UX")
    sc007 = result["criteria"]["001-disaster-response-hub:SC-007"]
    assert sc007["status"] == "fail"


def test_overall_false_when_any_required_sc_missing() -> None:
    service = ExerciseMetricsService()
    service.record(
        ExerciseKPI(
            exercise_id="BASE-MISS",
            scenario_type="flood",
            jurisdiction_id="nsw",
            organisation_ids=["ses-nsw"],
            run_type="baseline",
            timestamp_activation=datetime(2026, 3, 9, 9, 0, tzinfo=UTC),
        )
    )
    service.record(
        ExerciseKPI(
            exercise_id="HUB-MISS",
            scenario_type="flood",
            jurisdiction_id="nsw",
            organisation_ids=["ses-nsw"],
            run_type="hub_enabled",
            timestamp_activation=datetime(2026, 3, 9, 9, 0, tzinfo=UTC),
        )
    )
    result = service.compare("BASE-MISS", "HUB-MISS")
    assert result["overall_pass"] is False
    incomplete = [v for v in result["criteria"].values() if v["status"] == "incomplete"]
    assert incomplete
