from apps.agents.risk_assessment.agent import RiskAssessmentAgent


def test_risk_assessment_llm_recommendation_contains_signal_citation() -> None:
    agent = RiskAssessmentAgent()
    recommendation = agent.recommend_public_alert("incident-llm-1", ["sig-101"])

    assert recommendation.generation_method in {"llm", "template_fallback", "safety_fallback"}
    assert "sig-101" in recommendation.explanation
    assert recommendation.type == "public_alert"
