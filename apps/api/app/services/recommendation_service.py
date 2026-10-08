from typing import Literal
from uuid import uuid4

from app.core.tenant_context import get_current_tenant
from app.services.audit_service import AuditService
from app.services.operational_store import OperationalStore
from app.services.public_alert_service import assert_approver_authority
from fastapi import HTTPException

from packages.domain.src.domain.models.approval_decision import ApprovalDecision
from packages.domain.src.domain.models.public_alert import PublicAlert
from packages.domain.src.domain.models.recommendation import Recommendation


class RecommendationService:
    @staticmethod
    def _user_conditions(conditions: list[str]) -> list[str]:
        return [
            condition
            for condition in conditions
            if not condition.startswith("contentVersion=") and not condition.startswith("bindingSha256=")
        ]

    @staticmethod
    def _find_existing_decision(store: OperationalStore, recommendation_id: str) -> ApprovalDecision | None:
        for _, decision in store.approvals.items():
            if decision.recommendation_id == recommendation_id:
                return decision
        return None

    def record_approval(
        self,
        recommendation_id: str,
        approver_persona_id: str,
        outcome: Literal["approved", "rejected", "escalated", "timed_out"],
        rationale: str,
        conditions: list[str] | None = None,
        approver_roles: list[str] | tuple[str, ...] | None = None,
    ) -> ApprovalDecision:
        store = OperationalStore.current()
        recommendation = store.recommendations.require(recommendation_id)

        prior_decision = self._find_existing_decision(store, recommendation_id)
        normalized_conditions = list(conditions or [])
        normalized_rationale = rationale.strip()
        if prior_decision is not None:
            if (
                prior_decision.approver_persona_id == approver_persona_id
                and prior_decision.outcome == outcome
                and prior_decision.rationale == normalized_rationale
                and self._user_conditions(prior_decision.conditions) == self._user_conditions(normalized_conditions)
            ):
                return prior_decision
            raise HTTPException(status_code=409, detail="Recommendation is already in a terminal decision state")

        if recommendation.status in {"approved", "rejected", "escalated", "executed", "expired"}:
            raise HTTPException(status_code=409, detail="Recommendation is already in a terminal decision state")

        recommendation_status_map: dict[str, str] = {
            "approved": "approved",
            "rejected": "rejected",
            "escalated": "escalated",
            "timed_out": "expired",
        }
        next_recommendation_status = recommendation_status_map[outcome]

        if outcome == "approved" and approver_roles is not None:
            assert_approver_authority(recommendation.required_approval_level, approver_roles)

        linked_alert_id: str | None = None
        recommendation_conditions = list(normalized_conditions)
        derived_alert: PublicAlert | None = None
        if outcome == "approved" and recommendation.type == "public_alert":
            try:
                tenant = get_current_tenant()
                tenant_id = tenant.tenant_id
            except LookupError:
                tenant_id = "live"

            alert_id = f"alert-{recommendation_id}"
            existing_alert = store.alerts.get(alert_id)
            if existing_alert is not None and existing_alert.status in {"published", "superseded"}:
                raise HTTPException(
                    status_code=409, detail="Derived alert is already published and cannot be re-approved"
                )

            derived_alert = existing_alert or PublicAlert(
                alert_id=alert_id,
                incident_id=recommendation.incident_id,
                tenant_id=tenant_id,
                mode="live" if tenant_id == "live" else "rehearsal",
                status="draft",
                audience_segments=["affected-community"],
                languages=["en-AU"],
                accessibility_attributes=["plain-language"],
                channel_set=["sms", "push"],
                content_blocks={
                    "headline": recommendation.summary,
                    "body": recommendation.explanation,
                    "recommendationId": recommendation.recommendation_id,
                    "requiredApprovalLevel": recommendation.required_approval_level,
                },
                content_safety_result="not_checked",
            )
            derived_alert.status = "draft"
            linked_alert_id = derived_alert.alert_id

        decision = ApprovalDecision(
            approval_decision_id=f"appr-{uuid4().hex[:8]}",
            recommendation_id=recommendation_id,
            public_alert_id=None,
            approver_persona_id=approver_persona_id,
            outcome=outcome,
            rationale=normalized_rationale,
            conditions=recommendation_conditions,
        )

        AuditService().record_event(
            incident_id=recommendation.incident_id,
            event_type="approval",
            summary=f"Recommendation {recommendation_id} decision: {outcome}",
            actor=approver_persona_id,
            tenant_id=store.tenant_id,
            mode="live" if store.tenant_id == "live" else "rehearsal",
            correlation_id=decision.approval_decision_id,
            outcome=outcome,
            route="/api/recommendations/{recommendation_id}/approvals",
            content_version=None,
            supporting_signal_ids=list(recommendation.supporting_signal_ids),
            rationale=decision.rationale,
            payload={
                "recommendationId": recommendation_id,
                "publicAlertId": linked_alert_id,
            },
        )

        recommendation.status = next_recommendation_status
        if derived_alert is not None:
            store.alerts.put(derived_alert.alert_id, derived_alert)
        store.approvals.put(decision.approval_decision_id, decision)

        return decision

    def add(self, recommendation: Recommendation) -> Recommendation:
        store = OperationalStore.current()
        store.recommendations.put(recommendation.recommendation_id, recommendation)
        return recommendation
