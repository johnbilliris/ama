from apps.agents.risk_assessment.agent import RiskAssessmentAgent


def test_token_budget_enforcement_truncates_overage() -> None:
    agent = RiskAssessmentAgent()

    def _large_response(**_: object) -> dict[str, object]:
        return {
            "text": "A" * 600,
            "deployment_id": "reasoning-1",
            "token_usage": {"input_tokens": 120, "output_tokens": 400},
        }

    agent._llm_client.generate_response = _large_response  # type: ignore[method-assign]

    recommendation = agent.recommend_public_alert("incident-budget", ["sig-301"])

    assert len(recommendation.explanation) < 600
    assert recommendation.token_usage is not None
    assert recommendation.token_usage["output_tokens"] == 400
