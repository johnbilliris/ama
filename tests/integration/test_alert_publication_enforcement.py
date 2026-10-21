from __future__ import annotations

import pytest
from app.core.tenant_context import TenantContext, reset_current_tenant, set_current_tenant
from app.services.operational_store import OperationalStore
from app.services.public_alert_service import (
    PublicAlertService,
)
from app.services.recommendation_service import RecommendationService
from app.services.state_store import ALERTS, RECOMMENDATIONS, TIMELINE_EVENTS, reset_state
from fastapi import HTTPException

from packages.domain.src.domain.models.public_alert import PublicAlert
from packages.domain.src.domain.models.recommendation import Recommendation


def _seed_recommendation(*, recommendation_id: str = "rec-1") -> Recommendation:
    recommendation = Recommendation(
        recommendation_id=recommendation_id,
        incident_id="incident-1",
        type="public_alert",
        summary="Issue emergency warning",
        explanation="Escalating conditions require immediate communication.",
        supporting_signal_ids=["sig-1"],
        required_approval_level="incident_commander",
    )
    RECOMMENDATIONS[recommendation.recommendation_id] = recommendation
    return recommendation


def _seed_alert(*, status: str = "draft", include_all_languages: bool = True, safety: str = "passed") -> PublicAlert:
    languages = ["en-AU", "zh-Hans", "ar", "vi", "el", "it"] if include_all_languages else ["en-AU"]
    content_blocks = {
        "headline": "Emergency warning",
        "body": "Leave immediately.",
        "recommendationId": "rec-1",
        "requiredApprovalLevel": "incident_commander",
        "en-AU": "Emergency warning: leave immediately.",
    }
    if include_all_languages:
        content_blocks.update(
            {
                "zh-Hans": "紧急警告：立即撤离。",
                "ar": "تحذير طارئ: غادر فورًا.",
                "vi": "Cảnh báo khẩn cấp: rời đi ngay.",
                "el": "Έκτακτη προειδοποίηση: φύγετε άμεσα.",
                "it": "Allerta di emergenza: evacuare subito.",
            }
        )

    alert = PublicAlert(
        alert_id="alert-1",
        incident_id="incident-1",
        audience_segments=["affected-community"],
        languages=languages,
        channel_set=["sms", "push"],
        status=status,
        content_blocks=content_blocks,
        content_safety_result=safety,  # type: ignore[arg-type]
    )
    ALERTS[alert.alert_id] = alert
    return alert


def test_recommendation_approval_creates_draft_alert_not_auto_approved() -> None:
    reset_state()
    _seed_recommendation(recommendation_id="rec-1")

    decision = RecommendationService().record_approval(
        recommendation_id="rec-1",
        approver_persona_id="persona-ic",
        approver_roles=("incident-commander",),
        outcome="approved",
        rationale="Approved recommendation",
    )

    derived_alert = ALERTS["alert-rec-1"]
    assert decision.recommendation_id == "rec-1"
    assert decision.public_alert_id is None
    assert derived_alert.status == "draft"
    assert derived_alert.content_safety_result == "not_checked"


def test_alert_version_approval_then_publish_succeeds() -> None:
    reset_state()
    _seed_recommendation(recommendation_id="rec-1")
    _seed_alert(status="draft", include_all_languages=True, safety="passed")
    service = PublicAlertService()

    approval = service.approve_draft(
        alert_id="alert-1",
        approver_persona_id="persona-ic",
        approver_roles=("incident-commander",),
        rationale="Six-language draft and safety metadata reviewed",
    )
    published = service.publish("alert-1", "persona-publisher")

    assert approval.public_alert_id == "alert-1"
    assert published.status == "published"
    assert published.content_blocks["approvalDecisionId"] == approval.approval_decision_id
    assert published.content_blocks["publishedBy"] == "persona-publisher"


def test_publish_rejects_draft_without_alert_specific_approval() -> None:
    reset_state()
    _seed_recommendation(recommendation_id="rec-1")
    _seed_alert(status="draft", include_all_languages=True, safety="passed")
    service = PublicAlertService()

    try:
        service.publish("alert-1", "persona-ic")
        assert False, "Expected draft status to reject publish"
    except HTTPException as exc:
        assert exc.status_code == 409
        assert "not publishable" in str(exc.detail)


def test_publish_rejects_english_only_incomplete_alert() -> None:
    reset_state()
    _seed_recommendation(recommendation_id="rec-1")
    _seed_alert(status="approved", include_all_languages=False, safety="passed")
    service = PublicAlertService()

    try:
        service.publish("alert-1", "persona-publisher")
        assert False, "Expected incomplete language set to reject publish"
    except HTTPException as exc:
        assert exc.status_code == 409
        assert "six supported languages" in str(exc.detail)


def test_apply_template_rejects_approved_alert() -> None:
    reset_state()
    _seed_recommendation(recommendation_id="rec-1")
    _seed_alert(status="approved", include_all_languages=True, safety="passed")
    service = PublicAlertService()

    try:
        service.apply_template("alert-1", "evacuation")
        assert False, "Expected approved alert template mutation to be rejected"
    except HTTPException as exc:
        assert exc.status_code == 409
        assert "Cannot modify template after approval workflow" in str(exc.detail)


def test_publish_rejects_alert_when_safety_failed() -> None:
    reset_state()
    _seed_recommendation(recommendation_id="rec-1")
    _seed_alert(status="approved", include_all_languages=True, safety="failed_with_fallback")

    service = PublicAlertService()
    try:
        service.publish("alert-1", "persona-publisher")
        assert False, "Expected publish rejection when safety metadata is not passed"
    except HTTPException as exc:
        assert exc.status_code == 409
        assert "safety metadata" in str(exc.detail)


def test_publish_rejects_alert_when_binding_changed_after_alert_approval() -> None:
    reset_state()
    _seed_recommendation(recommendation_id="rec-1")
    alert = _seed_alert(status="draft", include_all_languages=True, safety="passed")
    service = PublicAlertService()
    service.approve_draft(
        alert_id="alert-1",
        approver_persona_id="persona-ic",
        approver_roles=("incident-commander",),
        rationale="Approved exact version",
    )
    alert.content_blocks["headline"] = "CHANGED AFTER APPROVAL"

    try:
        service.publish("alert-1", "persona-publisher")
        assert False, "Expected publish rejection when approved content is modified"
    except HTTPException as exc:
        assert exc.status_code == 409
        assert "changed since approval" in str(exc.detail)


def test_alert_approval_rejects_wrong_authority() -> None:
    reset_state()
    _seed_recommendation(recommendation_id="rec-1")
    _seed_alert(status="draft", include_all_languages=True, safety="passed")
    service = PublicAlertService()

    with pytest.raises(HTTPException) as exc_info:
        service.approve_draft(
            alert_id="alert-1",
            approver_persona_id="persona-pio",
            approver_roles=("public-information-officer",),
            rationale="Attempt approval",
        )

    assert exc_info.value.status_code == 403


def test_supersede_requires_same_incident_and_non_self() -> None:
    reset_state()
    published = PublicAlert(
        alert_id="alert-old",
        incident_id="incident-1",
        status="published",
        channel_set=["sms"],
        content_blocks={"headline": "old"},
    )
    replacement = PublicAlert(
        alert_id="alert-new",
        incident_id="incident-2",
        status="approved",
        channel_set=["sms"],
        content_blocks={"headline": "new"},
    )
    ALERTS[published.alert_id] = published
    ALERTS[replacement.alert_id] = replacement

    service = PublicAlertService()
    try:
        service.supersede("alert-old", "alert-old")
        assert False, "Expected self-supersession to fail"
    except HTTPException as exc:
        assert exc.status_code == 409

    try:
        service.supersede("alert-old", "alert-new")
        assert False, "Expected cross-incident supersession to fail"
    except HTTPException as exc:
        assert exc.status_code == 409


def test_simulated_delivery_records_one_durable_receipt_per_alert_version() -> None:
    reset_state()
    tenant_id = "sim-12345678-1234-1234-1234-123456789012"
    token = set_current_tenant(
        TenantContext(
            agency_id="ses-nsw",
            jurisdiction_ids=("nsw",),
            tenant_id=tenant_id,
        )
    )
    try:
        alert = PublicAlert(
            alert_id="alert-simulation",
            incident_id="incident-simulation",
            tenant_id=tenant_id,
            mode="rehearsal",
            status="published",
            audience_segments=["participants"],
            languages=["en-AU", "zh-Hans", "ar", "vi", "el", "it"],
            channel_set=["sms"],
            content_blocks={
                "headline": "Exercise warning",
                "body": "Exercise only.",
                "contentVersion": "version-1",
                "publishedBy": "exercise-controller",
                "en-AU": "Exercise warning",
                "zh-Hans": "Exercise warning",
                "ar": "Exercise warning",
                "vi": "Exercise warning",
                "el": "Exercise warning",
                "it": "Exercise warning",
            },
            content_safety_result="passed",
        )
        OperationalStore.current().alerts.put(alert.alert_id, alert)

        first = PublicAlertService().deliver(alert.alert_id)
        second = PublicAlertService().deliver(alert.alert_id)

        receipt = "sim-publish-alert-simulation-version-1"
        assert first[0]["providerReceipt"] == receipt
        assert second[0]["providerReceipt"] == receipt
        events = TIMELINE_EVENTS.bucket_for(tenant_id)["incident-simulation"]
        assert len(events) == 1
        assert events[0].correlation_id == receipt
    finally:
        reset_current_tenant(token)
