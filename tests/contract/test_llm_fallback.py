from apps.agents.risk_assessment.agent import RiskAssessmentAgent


def test_template_fallback_when_llm_unavailable() -> None:
    agent = RiskAssessmentAgent()

    def _raise_error(**_: object) -> dict[str, object]:
        raise RuntimeError("model unavailable")

    agent._llm_client.generate_response = _raise_error  # type: ignore[method-assign]

    recommendation = agent.recommend_public_alert("incident-fallback", ["sig-201"])
    assert recommendation.generation_method == "template_fallback"


def test_safety_fallback_when_content_flagged() -> None:
    agent = RiskAssessmentAgent()

    def _unsafe_response(**_: object) -> dict[str, object]:
        return {
            "text": "attack now",
            "deployment_id": "drafting-1",
            "token_usage": {"input_tokens": 10, "output_tokens": 5},
        }

    agent._llm_client.generate_response = _unsafe_response  # type: ignore[method-assign]

    recommendation = agent.recommend_public_alert("incident-safety", ["sig-202"])
    assert recommendation.generation_method == "safety_fallback"
