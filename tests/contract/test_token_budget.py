import dataclasses

from apps.agents.common.token_budget import UnicodeHeuristicTokenizer
from apps.agents.risk_assessment.agent import RiskAssessmentAgent


def test_output_budget_enforced_and_usage_split_reported() -> None:
    agent = RiskAssessmentAgent()
    agent._tokenizer = UnicodeHeuristicTokenizer()

    def _large_response(**_: object) -> dict[str, object]:
        return {
            "text": "A" * 600,
            "deployment_id": "reasoning-1",
            "token_usage": {"input_tokens": 120, "output_tokens": 400},
        }

    agent._llm_client.generate_response = _large_response  # type: ignore[method-assign]

    result = agent._generate_with_fallback(
        purpose="reasoning",
        prompt="brief prompt",
        template_text="template",
        max_output_tokens=280,
    )

    assert result["generation_method"] == "llm"
    assert agent._tokenizer.count_tokens(str(result["text"])) <= 280
    assert result["token_usage"]["output_tokens"] <= 280
    assert result["actual_token_usage"]["output_tokens"] == 400


def test_input_budget_exceeded_blocks_transport_call() -> None:
    agent = RiskAssessmentAgent()
    agent._tokenizer = UnicodeHeuristicTokenizer()
    agent._llm_config = dataclasses.replace(agent._llm_config, max_input_tokens=5)

    called = {"value": False}

    def _should_not_call(**_: object) -> dict[str, object]:
        called["value"] = True
        return {
            "text": "unexpected",
            "deployment_id": "reasoning-1",
            "token_usage": {"input_tokens": 1, "output_tokens": 1},
        }

    agent._llm_client.generate_response = _should_not_call  # type: ignore[method-assign]

    result = agent._generate_with_fallback(
        purpose="reasoning",
        prompt="this prompt is intentionally over the small configured budget",
        template_text="template fallback",
        max_output_tokens=280,
    )

    assert called["value"] is False
    assert result["generation_method"] == "template_fallback"
    assert result["error_reason"] == "input_budget_exceeded"
    assert result["actual_token_usage"]["input_tokens"] > 5


def test_cjk_budget_boundary_respected() -> None:
    agent = RiskAssessmentAgent()
    agent._tokenizer = UnicodeHeuristicTokenizer()

    def _cjk_response(**_: object) -> dict[str, object]:
        return {
            "text": "火" * 400,
            "deployment_id": "reasoning-1",
            "token_usage": {"input_tokens": 40, "output_tokens": 400},
        }

    agent._llm_client.generate_response = _cjk_response  # type: ignore[method-assign]

    result = agent._generate_with_fallback(
        purpose="reasoning",
        prompt="danger",
        template_text="template",
        max_output_tokens=280,
    )

    assert agent._tokenizer.count_tokens(str(result["text"])) <= 280


def test_post_citation_append_is_rebudgeted() -> None:
    agent = RiskAssessmentAgent()
    agent._tokenizer = UnicodeHeuristicTokenizer()

    def _near_limit_response(**_: object) -> dict[str, object]:
        return {
            "text": "a " * 278,
            "deployment_id": "reasoning-1",
            "token_usage": {"input_tokens": 40, "output_tokens": 278},
        }

    agent._llm_client.generate_response = _near_limit_response  # type: ignore[method-assign]

    recommendation = agent.recommend_public_alert("incident-budget", ["sig-301", "sig-302"])
    assert recommendation.token_usage is not None
    assert recommendation.token_usage["output_tokens"] <= 280
    assert agent._tokenizer.count_tokens(recommendation.explanation) <= 280
