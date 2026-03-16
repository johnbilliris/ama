from uuid import uuid4

from app.services.state_store import ALERTS, APPROVALS, RECOMMENDATIONS

from packages.domain.src.domain.models.approval_decision import ApprovalDecision
from packages.domain.src.domain.models.public_alert import PublicAlert
from packages.domain.src.domain.models.recommendation import Recommendation


class RecommendationService:
    def record_approval(
        self,
        recommendation_id: str,
        approver_persona_id: str,
        outcome: str,
        rationale: str,
        conditions: list[str] | None = None,
    ) -> ApprovalDecision:
        recommendation = RECOMMENDATIONS[recommendation_id]
        recommendation.status = "approved" if outcome == "approved" else "rejected"

        decision = ApprovalDecision(
            approval_decision_id=f"appr-{uuid4().hex[:8]}",
            recommendation_id=recommendation_id,
            approver_persona_id=approver_persona_id,
            outcome=outcome,
            rationale=rationale,
            conditions=conditions or [],
        )
        APPROVALS[decision.approval_decision_id] = decision

        if outcome == "approved" and recommendation.type == "public_alert":
            alert = PublicAlert(
                alert_id=f"alert-{recommendation_id}",
                incident_id=recommendation.incident_id,
                status="approved",
                audience_segments=["affected-community"],
                languages=["en-AU"],
                accessibility_attributes=["plain-language"],
                channel_set=["sms", "push"],
                content_blocks={"headline": recommendation.summary},
            )
            ALERTS[alert.alert_id] = alert

        return decision

    def add(self, recommendation: Recommendation) -> Recommendation:
        RECOMMENDATIONS[recommendation.recommendation_id] = recommendation
        return recommendation
