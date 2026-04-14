"""Unit tests for MEFramework domain model.

Tests: framework creation, 5 evaluation domains, selected outcomes,
success standards, collection schedules, status transitions.
"""
from datetime import UTC, datetime, timedelta

import pytest

from packages.domain.src.domain.models.me_framework import (
    ALL_EVALUATION_DOMAINS,
    CollectionSchedule,
    MEFramework,
    SelectedOutcome,
    SuccessStandard,
)


class TestEvaluationDomainConstants:
    def test_all_evaluation_domains_count(self):
        assert len(ALL_EVALUATION_DOMAINS) == 5

    def test_all_evaluation_domains_values(self):
        expected = {"governance", "community_engagement", "effectiveness", "efficiency", "implementation"}
        assert set(ALL_EVALUATION_DOMAINS) == expected


class TestSelectedOutcome:
    def test_valid_selected_outcome(self):
        outcome = SelectedOutcome(
            catalogue_outcome_id="aidr:social:community-health",
            domain="social",
            objective_type="resilience",
        )
        assert outcome.is_active is True
        assert outcome.community_restatement is None

    def test_selected_outcome_with_community_restatement(self):
        outcome = SelectedOutcome(
            catalogue_outcome_id="aidr:economic:local-business",
            domain="economic",
            objective_type="sustainability",
            community_restatement="Local businesses reopen within 6 months",
        )
        assert outcome.community_restatement == "Local businesses reopen within 6 months"

    def test_selected_outcome_inactive(self):
        outcome = SelectedOutcome(
            catalogue_outcome_id="aidr:built:housing",
            domain="built",
            objective_type="resilience",
            is_active=False,
        )
        assert outcome.is_active is False

    @pytest.mark.parametrize("domain", ["overarching", "social", "economic", "built", "natural"])
    def test_all_recovery_domains_valid(self, domain):
        outcome = SelectedOutcome(
            catalogue_outcome_id=f"aidr:{domain}:test",
            domain=domain,
            objective_type="resilience",
        )
        assert outcome.domain == domain

    @pytest.mark.parametrize("obj_type", ["sustainability", "resilience"])
    def test_both_objective_types_valid(self, obj_type):
        outcome = SelectedOutcome(
            catalogue_outcome_id="aidr:social:test",
            domain="social",
            objective_type=obj_type,
        )
        assert outcome.objective_type == obj_type


class TestSuccessStandard:
    def test_valid_success_standard_gte(self):
        ss = SuccessStandard(
            catalogue_outcome_id="aidr:social:test",
            indicator_id="ind-1",
            threshold_value=80.0,
            threshold_operator="gte",
        )
        assert ss.threshold_operator == "gte"
        assert ss.threshold_upper is None

    def test_between_requires_threshold_upper(self):
        with pytest.raises(ValueError, match="threshold_upper required"):
            SuccessStandard(
                catalogue_outcome_id="aidr:social:test",
                indicator_id="ind-1",
                threshold_value=50.0,
                threshold_operator="between",
            )

    def test_between_with_threshold_upper_valid(self):
        ss = SuccessStandard(
            catalogue_outcome_id="aidr:social:test",
            indicator_id="ind-1",
            threshold_value=50.0,
            threshold_operator="between",
            threshold_upper=90.0,
        )
        assert ss.threshold_upper == 90.0

    @pytest.mark.parametrize("op", ["gte", "lte", "eq", "between"])
    def test_all_operators_valid(self, op):
        kwargs = dict(
            catalogue_outcome_id="aidr:social:test",
            indicator_id="ind-1",
            threshold_value=50.0,
            threshold_operator=op,
        )
        if op == "between":
            kwargs["threshold_upper"] = 100.0
        ss = SuccessStandard(**kwargs)
        assert ss.threshold_operator == op

    def test_success_standard_stakeholder_label(self):
        ss = SuccessStandard(
            catalogue_outcome_id="aidr:social:test",
            indicator_id="ind-1",
            threshold_value=80.0,
            stakeholder_label="secondary",
        )
        assert ss.stakeholder_label == "secondary"

    def test_success_standard_default_label(self):
        ss = SuccessStandard(
            catalogue_outcome_id="aidr:social:test",
            indicator_id="ind-1",
            threshold_value=80.0,
        )
        assert ss.stakeholder_label == "primary"


class TestCollectionSchedule:
    def test_valid_collection_schedule(self):
        due = datetime.now(UTC) + timedelta(days=30)
        cs = CollectionSchedule(
            indicator_id="ind-1",
            frequency="monthly",
            next_due_date=due,
        )
        assert cs.frequency == "monthly"
        assert cs.is_overdue is False
        assert cs.last_collected_at is None

    @pytest.mark.parametrize("freq", ["weekly", "fortnightly", "monthly", "quarterly", "annually"])
    def test_all_frequencies_valid(self, freq):
        cs = CollectionSchedule(
            indicator_id="ind-1",
            frequency=freq,
            next_due_date=datetime.now(UTC),
        )
        assert cs.frequency == freq

    def test_collection_schedule_with_last_collected(self):
        now = datetime.now(UTC)
        cs = CollectionSchedule(
            indicator_id="ind-1",
            frequency="quarterly",
            next_due_date=now + timedelta(days=90),
            last_collected_at=now,
        )
        assert cs.last_collected_at == now

    def test_collection_schedule_overdue(self):
        cs = CollectionSchedule(
            indicator_id="ind-1",
            frequency="weekly",
            next_due_date=datetime.now(UTC),
            is_overdue=True,
        )
        assert cs.is_overdue is True


class TestMEFramework:
    def test_valid_framework_creation(self):
        fw = MEFramework(
            framework_id="me-1",
            incident_id="inc-1",
            program_name="Flood Recovery Program",
        )
        assert fw.status == "configuring"
        assert fw.framework_id == "me-1"

    def test_default_evaluation_domains_all_5(self):
        fw = MEFramework(
            framework_id="me-1",
            incident_id="inc-1",
            program_name="Test",
        )
        assert len(fw.active_evaluation_domains) == 5
        assert set(fw.active_evaluation_domains) == set(ALL_EVALUATION_DOMAINS)

    def test_custom_evaluation_domains_subset(self):
        fw = MEFramework(
            framework_id="me-1",
            incident_id="inc-1",
            program_name="Test",
            active_evaluation_domains=["governance", "effectiveness"],
        )
        assert len(fw.active_evaluation_domains) == 2

    def test_framework_with_selected_outcomes(self):
        outcome = SelectedOutcome(
            catalogue_outcome_id="aidr:social:health",
            domain="social",
            objective_type="resilience",
            community_restatement="Community health improves",
        )
        fw = MEFramework(
            framework_id="me-1",
            incident_id="inc-1",
            program_name="Test",
            selected_outcomes=[outcome],
        )
        assert len(fw.selected_outcomes) == 1
        assert fw.selected_outcomes[0].community_restatement == "Community health improves"

    def test_framework_with_success_standards(self):
        ss = SuccessStandard(
            catalogue_outcome_id="aidr:social:health",
            indicator_id="ind-1",
            threshold_value=80.0,
        )
        fw = MEFramework(
            framework_id="me-1",
            incident_id="inc-1",
            program_name="Test",
            standards_of_success=[ss],
        )
        assert len(fw.standards_of_success) == 1

    def test_framework_with_collection_schedule(self):
        cs = CollectionSchedule(
            indicator_id="ind-1",
            frequency="monthly",
            next_due_date=datetime.now(UTC),
        )
        fw = MEFramework(
            framework_id="me-1",
            incident_id="inc-1",
            program_name="Test",
            indicator_collection_schedule=[cs],
        )
        assert len(fw.indicator_collection_schedule) == 1

    @pytest.mark.parametrize("status", ["configuring", "active", "evaluation_complete", "closed"])
    def test_all_framework_statuses_valid(self, status):
        fw = MEFramework(
            framework_id="me-1",
            incident_id="inc-1",
            program_name="Test",
            status=status,
        )
        assert fw.status == status

    def test_default_status_is_configuring(self):
        fw = MEFramework(framework_id="me-1", incident_id="inc-1", program_name="Test")
        assert fw.status == "configuring"

    def test_framework_program_logic_link(self):
        fw = MEFramework(
            framework_id="me-1",
            incident_id="inc-1",
            program_name="Test",
            program_logic_id="pl-42",
        )
        assert fw.program_logic_id == "pl-42"

    def test_framework_evaluation_reports_list(self):
        fw = MEFramework(
            framework_id="me-1",
            incident_id="inc-1",
            program_name="Test",
            evaluation_reports=["er-1", "er-2"],
        )
        assert len(fw.evaluation_reports) == 2
