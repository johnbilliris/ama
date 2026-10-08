from apps.agents.risk_assessment.agent import RiskAssessmentAgent


def test_risk_prompt_contains_retrieved_evidence_and_valid_citation_subset() -> None:
    agent = RiskAssessmentAgent()
    captured: dict[str, object] = {}

    def _response(**kwargs: object) -> dict[str, object]:
        captured.update(kwargs)
        return {
            "text": "Public alert is recommended based on sig-101 and sig-102.",
            "deployment_id": "reasoning-1",
            "token_usage": {"input_tokens": 40, "output_tokens": 20},
        }

    agent._llm_client.generate_response = _response  # type: ignore[method-assign]
    recommendation = agent.recommend_public_alert(
        "incident-llm-1",
        ["sig-101", "sig-102"],
        signal_evidence={
            "sig-101": {"summary": "BoM severe warning", "source_uri": "https://bom.example"},
            "sig-102": {"summary": "SES field report", "source_uri": "https://ses.example"},
        },
    )

    prompt = str(captured.get("prompt", ""))
    assert "Retrieved source evidence" in prompt
    assert "sig-101" in prompt
    assert "sig-102" in prompt
    assert recommendation.generation_method == "llm"
    assert "sig-101" in recommendation.explanation
    assert recommendation.type == "public_alert"


def test_missing_or_invalid_citations_fall_back() -> None:
    agent = RiskAssessmentAgent()

    def _invalid_citations(**_: object) -> dict[str, object]:
        return {
            "text": "Public alert should cite synth-123 only.",
            "deployment_id": "reasoning-1",
            "token_usage": {"input_tokens": 40, "output_tokens": 20},
        }

    agent._llm_client.generate_response = _invalid_citations  # type: ignore[method-assign]
    recommendation = agent.recommend_public_alert("incident-llm-2", ["sig-201"])

    assert recommendation.generation_method == "template_fallback"
    assert "synth-" not in recommendation.explanation
