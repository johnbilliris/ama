"""Contract tests for the cultural-safety subsystem (spec-035 T049 / FR-016).

Implements the contract from
``specs/035-webapp-capstone-closure/contracts/cultural-safety.contract.md``.

Tests cover the AWS-level-conditional outcome policy, IC-override eligibility,
and the elder-decline path.
"""

from __future__ import annotations

import pytest
from app.services.cultural_safety_service import (
    AwsLevel,
    CulturalSafetyDraft,
    CulturalSafetyError,
    CulturalSafetyOutcome,
    CulturalSafetyService,
    CulturalSafetyState,
)


def _draft(level: AwsLevel) -> CulturalSafetyDraft:
    return CulturalSafetyDraft(
        draft_id="d-1",
        aws_level=level,
        jurisdiction="NT",
        language_pack="yolngu_matha",
        operator_identity="op-oid",
    )


def test_emergency_warning_timeout_with_ic_override_emits_override_outcome() -> None:
    service = CulturalSafetyService()
    decision = service.on_timeout(
        _draft(AwsLevel.emergency_warning),
        ic_confirmer_oid="ic-oid",
    )
    assert decision.outcome is CulturalSafetyOutcome.cultural_safety_timeout_override
    assert decision.state is CulturalSafetyState.timeout_lifesafety_override
    assert decision.audit_row["cultural_safety_confirmer"] == "ic-oid"
    assert decision.audit_row["aws_level"] == "emergency_warning"
    assert decision.audit_row["timeout_seconds"] == 90


def test_emergency_warning_timeout_without_ic_holds_pending() -> None:
    service = CulturalSafetyService()
    decision = service.on_timeout(_draft(AwsLevel.emergency_warning))
    assert decision.outcome is CulturalSafetyOutcome.cultural_safety_held
    assert decision.state is CulturalSafetyState.timeout_lifesafety_override


def test_watch_and_act_timeout_holds_publication() -> None:
    service = CulturalSafetyService()
    decision = service.on_timeout(_draft(AwsLevel.watch_and_act))
    assert decision.outcome is CulturalSafetyOutcome.cultural_safety_held
    assert decision.state is CulturalSafetyState.timeout_blocked


def test_advice_timeout_holds_publication() -> None:
    service = CulturalSafetyService()
    decision = service.on_timeout(_draft(AwsLevel.advice))
    assert decision.outcome is CulturalSafetyOutcome.cultural_safety_held
    assert decision.state is CulturalSafetyState.timeout_blocked


def test_ic_override_rejected_on_non_emergency_aws_level() -> None:
    service = CulturalSafetyService()
    with pytest.raises(CulturalSafetyError):
        service.on_timeout(_draft(AwsLevel.watch_and_act), ic_confirmer_oid="ic-oid")


def test_elder_decline_yields_held_outcome_regardless_of_level() -> None:
    service = CulturalSafetyService()
    for level in AwsLevel:
        decision = service.on_elder_decline(_draft(level))
        assert decision.outcome is CulturalSafetyOutcome.cultural_safety_held
        assert decision.state is CulturalSafetyState.declined
