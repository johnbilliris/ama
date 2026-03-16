from common.llm_mixin import LLMCallMixin
from common.handoffs import AgentHandoffEvent, build_handoff
from packages.domain.src.domain.models.recommendation import Recommendation


class RiskAssessmentAgent(LLMCallMixin):
    def __init__(self) -> None:
        super().__init__()

    def recommend_public_alert(self, incident_id: str, signal_ids: list[str]) -> Recommendation:
        cited_signals = ", ".join(signal_ids) if signal_ids else "no-signals"
        template_explanation = (
            "Authoritative and community signals indicate escalating community risk. "
            f"Signal references: {cited_signals}."
        )
        response = self._generate_with_fallback(
            purpose="reasoning",
            prompt=(
                "Create a concise public alert recommendation explanation that includes signal IDs. "
                f"Incident: {incident_id}; Signals: {cited_signals}."
            ),
            template_text=template_explanation,
            max_output_tokens=280,
        )

        explanation = str(response["text"])
        if signal_ids and not any(signal_id in explanation for signal_id in signal_ids):
            explanation = f"{explanation} Signal references: {cited_signals}."

        return Recommendation(
            recommendation_id=f"rec-{incident_id}",
            incident_id=incident_id,
            type="public_alert",
            summary="Prepare multilingual community alert",
            explanation=explanation,
            supporting_signal_ids=signal_ids,
            required_approval_level="incident_commander",
            confidence_level="high",
            generation_method=str(response["generation_method"]),
            model_deployment_id=response["model_deployment_id"],
            token_usage=response["token_usage"],
        )

    def build_communication_handoff(self, recommendation: Recommendation) -> AgentHandoffEvent | None:
        if recommendation.type != "public_alert" or recommendation.confidence_level != "high":
            return None

        return build_handoff(
            incident_id=recommendation.incident_id,
            source_agent="risk_assessment",
            target_agent="communication",
            scope_key=recommendation.incident_id,
            payload={
                "recommendationId": recommendation.recommendation_id,
                "summary": recommendation.summary,
                "explanation": recommendation.explanation,
            },
            confidence=0.9,
        )
