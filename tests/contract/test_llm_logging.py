import logging

from apps.agents.risk_assessment.agent import RiskAssessmentAgent


def test_llm_logging_contains_correlation_and_token_usage(caplog) -> None:
    agent = RiskAssessmentAgent()

    def _logged_response(**_: object) -> dict[str, object]:
        logging.getLogger("common.llm_client").info(
            "llm_call correlation_id=test-correlation"
            " deployment_id=reasoning-1 latency_ms=100"
            " input_tokens=15 output_tokens=25"
        )
        return {
            "text": "Risk remains high for sector alpha.",
            "deployment_id": "reasoning-1",
            "token_usage": {"input_tokens": 15, "output_tokens": 25},
        }

    agent._llm_client.generate_response = _logged_response  # type: ignore[method-assign]

    with caplog.at_level(logging.INFO):
        recommendation = agent.recommend_public_alert("incident-log", ["sig-401"])

    combined = "\n".join(caplog.messages)
    assert "correlation_id=test-correlation" in combined
    assert "input_tokens=15" in combined
    assert recommendation.model_deployment_id == "reasoning-1"
