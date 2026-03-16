from packages.domain.src.domain.models.recommendation import Recommendation


class RiskAssessmentAgent:
    def recommend_public_alert(self, incident_id: str, signal_ids: list[str]) -> Recommendation:
        return Recommendation(
            recommendation_id=f"rec-{incident_id}",
            incident_id=incident_id,
            type="public_alert",
            summary="Prepare multilingual community alert",
            explanation="Authoritative and community signals indicate escalating community risk.",
            supporting_signal_ids=signal_ids,
            required_approval_level="incident_commander",
            confidence_level="high",
        )
