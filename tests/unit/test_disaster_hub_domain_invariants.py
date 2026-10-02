from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from packages.domain.src.domain.models.approval_decision import ApprovalDecision
from packages.domain.src.domain.models.framework_assignment import FrameworkAssignment
from packages.domain.src.domain.models.hazard_assessment import HazardAssessment
from packages.domain.src.domain.models.incident import Incident
from packages.domain.src.domain.models.jurisdiction_policy import JurisdictionPolicy
from packages.domain.src.domain.models.signal import Signal


def test_incident_requires_non_empty_jurisdictions() -> None:
    with pytest.raises(Exception):
        Incident(
            incident_id="inc-1",
            title="Test",
            incident_type="flood",
            status="active",
            severity="warning",
            affected_jurisdiction_ids=[],
        )


def test_incident_rejects_ended_before_started() -> None:
    start = datetime.now(UTC)
    with pytest.raises(Exception):
        Incident(
            incident_id="inc-2",
            title="Test",
            incident_type="flood",
            status="closed",
            severity="warning",
            affected_jurisdiction_ids=["nsw"],
            started_at=start,
            ended_at=start - timedelta(minutes=1),
        )


def test_approval_decision_requires_single_target() -> None:
    with pytest.raises(Exception):
        ApprovalDecision(
            approval_decision_id="ad-1",
            approver_persona_id="persona-1",
            outcome="approved",
            rationale="valid reason",
        )


def test_approval_decision_rejects_dual_targets() -> None:
    with pytest.raises(Exception):
        ApprovalDecision(
            approval_decision_id="ad-2",
            recommendation_id="rec-1",
            public_alert_id="alert-1",
            approver_persona_id="persona-1",
            outcome="approved",
            rationale="valid reason",
        )


def test_framework_assignment_requires_scope_target() -> None:
    with pytest.raises(Exception):
        FrameworkAssignment(
            assignment_id="fa-1",
            framework_id="fw-1",
        )


def test_framework_assignment_requires_valid_window() -> None:
    start = datetime.now(UTC)
    with pytest.raises(Exception):
        FrameworkAssignment(
            assignment_id="fa-2",
            framework_id="fw-1",
            jurisdiction_id="nsw",
            effective_from=start,
            effective_to=start - timedelta(hours=1),
        )


def test_jurisdiction_policy_requires_australian_region() -> None:
    with pytest.raises(Exception):
        JurisdictionPolicy(
            policy_set_id="pol-1",
            data_residency_region="japaneast",
            retention_rules=["retain-operational-30d"],
        )


def test_jurisdiction_policy_requires_retention_rules() -> None:
    with pytest.raises(Exception):
        JurisdictionPolicy(
            policy_set_id="pol-1",
            data_residency_region="australiaeast",
            retention_rules=[],
        )


def test_hazard_assessment_requires_input_signals() -> None:
    with pytest.raises(Exception):
        HazardAssessment(
            hazard_assessment_id="ha-1",
            incident_id="inc-1",
            assessment_type="spread_prediction",
            input_signal_ids=[],
            summary="No source",
            confidence_level="low",
        )


def test_signal_rejects_reversed_timestamps() -> None:
    start = datetime.now(UTC)
    with pytest.raises(Exception):
        Signal(
            signal_id="sig-1",
            incident_id="inc-1",
            data_source_id="ds-1",
            category="weather",
            occurred_at=start,
            received_at=start - timedelta(minutes=1),
            location={"type": "Point", "coordinates": [151.2, -33.8]},
            confidence_score=0.9,
            freshness_score=0.8,
            validation_status="validated",
            provenance={"sourceUri": "https://example"},
        )
