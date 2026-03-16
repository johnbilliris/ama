import os

import pytest

from apps.agents.communication.agent import CommunicationAgent
from apps.agents.risk_assessment.agent import RiskAssessmentAgent

LIVE_ENV_VARS = [
    "AZURE_OPENAI_ENDPOINT",
    "AZURE_OPENAI_API_KEY",
    "AZURE_OPENAI_REASONING_DEPLOYMENT",
    "AZURE_OPENAI_DRAFTING_DEPLOYMENT",
]


@pytest.mark.skipif(
    any(not os.getenv(name) for name in LIVE_ENV_VARS),
    reason="Azure OpenAI credentials/deployments are not configured",
)
def test_live_llm_quickstart_rehearsal() -> None:
    risk_agent = RiskAssessmentAgent()
    communication_agent = CommunicationAgent()

    recommendation = risk_agent.recommend_public_alert("incident-live-llm", ["sig-live-001"])
    assert recommendation.generation_method == "llm"
    assert recommendation.model_deployment_id
    assert recommendation.token_usage

    alert = communication_agent.draft_alert("incident-live-llm", recommendation.recommendation_id)
    assert alert.generation_method == "llm"
    assert set(alert.languages) == {"en-AU", "zh-Hans", "ar", "vi", "el", "it"}
    assert set(alert.content_blocks.keys()) == set(alert.languages)
    assert alert.model_deployment_id
