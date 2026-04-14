"""Unit tests for PlanningProcessRecord domain model.

Tests: 9-step AIDR process tracking, step validation, team members,
stakeholder engagement, endorsement approvals.
"""
from datetime import UTC, datetime

import pytest

from packages.domain.src.domain.models.planning_process_record import (
    PLANNING_STEPS,
    EndorsementApproval,
    EngagementEntry,
    PlanningProcessRecord,
    StepCompletion,
    TeamMember,
)


class TestPlanningStepsConstant:
    def test_planning_steps_count(self):
        assert len(PLANNING_STEPS) == 9

    def test_planning_steps_keys_are_1_to_9(self):
        assert set(PLANNING_STEPS.keys()) == set(range(1, 10))

    def test_step_1_is_establish_project_plan(self):
        assert PLANNING_STEPS[1] == "Establish project plan"

    def test_step_9_is_monitor_and_review(self):
        assert PLANNING_STEPS[9] == "Monitor and review"


class TestStepCompletion:
    def test_valid_step_creation(self):
        step = StepCompletion(step_number=1, step_name="Establish project plan")
        assert step.step_number == 1
        assert step.is_complete is False
        assert step.completed_at is None

    def test_complete_step_with_completed_at(self):
        now = datetime.now(UTC)
        step = StepCompletion(
            step_number=3, step_name="Communicate and consult",
            is_complete=True, completed_at=now, completed_by="user-1",
        )
        assert step.is_complete is True
        assert step.completed_at == now

    def test_step_number_too_low(self):
        with pytest.raises(ValueError, match="step_number must be 1–9"):
            StepCompletion(step_number=0, step_name="Invalid")

    def test_step_number_too_high(self):
        with pytest.raises(ValueError, match="step_number must be 1–9"):
            StepCompletion(step_number=10, step_name="Invalid")

    def test_negative_step_number(self):
        with pytest.raises(ValueError, match="step_number must be 1–9"):
            StepCompletion(step_number=-1, step_name="Invalid")

    def test_complete_without_completed_at_raises(self):
        with pytest.raises(ValueError, match="completed_at required"):
            StepCompletion(step_number=1, step_name="Test", is_complete=True)

    def test_incomplete_without_completed_at_ok(self):
        step = StepCompletion(step_number=5, step_name="Develop strategies")
        assert step.is_complete is False
        assert step.completed_at is None

    @pytest.mark.parametrize("num", range(1, 10))
    def test_all_valid_step_numbers(self, num):
        step = StepCompletion(step_number=num, step_name=PLANNING_STEPS[num])
        assert step.step_number == num


class TestTeamMember:
    def test_valid_team_member(self):
        now = datetime.now(UTC)
        member = TeamMember(name="Jane Doe", role="Project Lead", organisation="SES", joined_at=now)
        assert member.name == "Jane Doe"
        assert member.role == "Project Lead"
        assert member.organisation == "SES"

    def test_team_member_fields(self):
        now = datetime.now(UTC)
        member = TeamMember(name="A", role="B", organisation="C", joined_at=now)
        assert member.joined_at == now


class TestEngagementEntry:
    def test_valid_engagement_workshop(self):
        entry = EngagementEntry(
            stakeholder="Local Council", method="workshop",
            date=datetime.now(UTC), summary="Risk assessment workshop",
        )
        assert entry.method == "workshop"
        assert entry.attendee_count is None

    def test_engagement_with_attendee_count(self):
        entry = EngagementEntry(
            stakeholder="Community Group", method="public_meeting",
            date=datetime.now(UTC), summary="Community consultation",
            attendee_count=45,
        )
        assert entry.attendee_count == 45

    @pytest.mark.parametrize("method", [
        "workshop", "survey", "interview", "public_meeting",
        "written_submission", "other",
    ])
    def test_all_engagement_methods_valid(self, method):
        entry = EngagementEntry(
            stakeholder="Test", method=method,
            date=datetime.now(UTC), summary="Test",
        )
        assert entry.method == method


class TestEndorsementApproval:
    def test_valid_approval(self):
        approval = EndorsementApproval(
            authority_name="Commissioner",
            authority_role="State Coordinator",
            approved=True,
            approved_at=datetime.now(UTC),
            comments="Approved with minor edits",
        )
        assert approval.approved is True

    def test_rejection(self):
        approval = EndorsementApproval(
            authority_name="Regional Director",
            authority_role="Director",
            approved=False,
            comments="Needs further stakeholder input",
        )
        assert approval.approved is False
        assert approval.approved_at is None


class TestPlanningProcessRecord:
    def test_valid_record_creation(self):
        record = PlanningProcessRecord(record_id="ppr-1", plan_id="ep-1")
        assert record.current_step == 1
        assert record.step_status == {}
        assert record.project_team == []

    def test_current_step_default_is_1(self):
        record = PlanningProcessRecord(record_id="ppr-1", plan_id="ep-1")
        assert record.current_step == 1

    def test_current_step_0_raises(self):
        with pytest.raises(ValueError, match="current_step must be 1–9"):
            PlanningProcessRecord(record_id="ppr-1", plan_id="ep-1", current_step=0)

    def test_current_step_10_raises(self):
        with pytest.raises(ValueError, match="current_step must be 1–9"):
            PlanningProcessRecord(record_id="ppr-1", plan_id="ep-1", current_step=10)

    def test_step_status_invalid_key_raises(self):
        step = StepCompletion(step_number=1, step_name="Test")
        with pytest.raises(ValueError, match="step_status key must be 1–9"):
            PlanningProcessRecord(
                record_id="ppr-1", plan_id="ep-1",
                step_status={0: step},
            )

    def test_step_status_valid_keys(self):
        step1 = StepCompletion(step_number=1, step_name="Establish project plan")
        step2 = StepCompletion(step_number=2, step_name="Establish project team")
        record = PlanningProcessRecord(
            record_id="ppr-1", plan_id="ep-1",
            step_status={1: step1, 2: step2},
        )
        assert len(record.step_status) == 2

    def test_record_with_team_members(self):
        member = TeamMember(name="A", role="Lead", organisation="SES", joined_at=datetime.now(UTC))
        record = PlanningProcessRecord(
            record_id="ppr-1", plan_id="ep-1",
            project_team=[member],
        )
        assert len(record.project_team) == 1

    def test_record_with_engagement_log(self):
        entry = EngagementEntry(
            stakeholder="Council", method="workshop",
            date=datetime.now(UTC), summary="Planning workshop",
        )
        record = PlanningProcessRecord(
            record_id="ppr-1", plan_id="ep-1",
            stakeholder_engagement_log=[entry],
        )
        assert len(record.stakeholder_engagement_log) == 1

    def test_record_with_endorsement_approvals(self):
        approval = EndorsementApproval(
            authority_name="Commissioner", authority_role="State Coordinator", approved=True,
        )
        record = PlanningProcessRecord(
            record_id="ppr-1", plan_id="ep-1",
            endorsement_approvals=[approval],
        )
        assert len(record.endorsement_approvals) == 1

    def test_record_with_risk_assessment_id(self):
        record = PlanningProcessRecord(
            record_id="ppr-1", plan_id="ep-1",
            risk_assessment_id="ra-42",
        )
        assert record.risk_assessment_id == "ra-42"
