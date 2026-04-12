import os

import pytest

LIVE_ENV_VARS = [
    "AZURE_OPENAI_ENDPOINT",
    "AZURE_OPENAI_REASONING_DEPLOYMENT",
    "AZURE_OPENAI_DRAFTING_DEPLOYMENT",
]


@pytest.mark.skipif(
    any(not os.getenv(name) for name in LIVE_ENV_VARS),
    reason="Azure OpenAI credentials/deployments are not configured",
)
def test_live_llm_quickstart_rehearsal() -> None:
    from apps.agents.risk_assessment.agent import RiskAssessmentAgent

    risk_agent = RiskAssessmentAgent()

    recommendation = risk_agent.recommend_public_alert("incident-live-llm", ["sig-live-001"])
    assert recommendation.generation_method == "llm"
    assert recommendation.model_deployment_id
    assert recommendation.token_usage
